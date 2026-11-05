import argparse
import json
from dataclasses import asdict
from hashlib import sha1, sha256
from pathlib import Path

from arc.adapters.datasets.common import Dataset
from arc.adapters.datasets.scifact import load_scifact
from arc.adapters.datasets.wands import load_wands
from arc.evaluation.qrels import audit_qrels, wands_split

SCIFACT_SOURCE = "https://github.com/beir-cellar/beir/wiki/Datasets-available"
WANDS_SOURCE = "https://github.com/wayfair/WANDS"
WANDS_REVISION = "3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5"

WANDS_BLOBS = {
    "product.csv": "a415f7295dc0d90b3163ef606da611a4e9ddeca8",
    "query.csv": "acb3c1f4cf1b775f494225afec79ec2163fc3e03",
    "label.csv": "2c09a0d7b1f77f6040deb5873b5a90b8ef1e3ae9",
}
SCIFACT_FILES = {
    "corpus.jsonl": "dec31c8182f3d744c7d2c09423756fd1d17cbef75808db13ba01cc0aab4d1ac6",
    "queries.jsonl": "8ff84a7c903f722981cd8d595c022660140c51867b27608a6d4910db86080313",
    "qrels/test.tsv": "0864bb985e0ca2367ba217977e72004d549054b2b06666ed9d4825ac7c21284c",
    "qrels/train.tsv": "a53f2114831916c096b6c37d9e54da68cef4efdcdbd5ed46533601af972acf1d",
}


def verify_wands_blob(path: Path) -> None:
    digest = sha1(f"blob {path.stat().st_size}\0".encode(), usedforsecurity=False)
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    if digest.hexdigest() != WANDS_BLOBS[path.name]:
        raise ValueError(f"WANDS blob mismatch: {path.name}")


def write_json(path: Path, data: object) -> str:
    payload = (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    return sha256(payload).hexdigest()


def inspect(
    dataset: Dataset, *, wands: bool
) -> tuple[dict[str, object], tuple[str, ...], tuple[str, ...], list[str]]:
    entities = {entity.key.entity_id for entity in dataset.corpus.entities}
    units = dataset.corpus.units
    failures = []
    if len(units) != len(entities) or any(
        unit.unit_id != unit.entity_key.entity_id for unit in units
    ):
        failures.append("Entity/Unit 1:1 mapping violated")
    splits = dataset.judgments
    if wands:
        try:
            dev, test = wands_split(dataset.queries)
        except ValueError as error:
            failures.append(str(error))
            dev, test = (), ()
        if len(entities) != 42994 or len(splits["all"]) != 233448:
            failures.append("Unexpected official WANDS product or raw judgment count")
    else:
        dev = tuple(sorted({qid for qid, _, _ in splits["dev"]}))
        test = tuple(sorted({qid for qid, _, _ in splits["test"]}))
        if len(entities) != 5183 or len(test) != 300:
            failures.append("Unexpected official SciFact corpus or test query count")
        if not dev or set(dev) | set(test) != set(dataset.queries):
            failures.append("SciFact queries do not match the official judgment splits")
    if set(dev).intersection(test):
        failures.append("Dev and test query IDs overlap")
    label_audits = {}
    for split, rows in splits.items():
        qids = set(dataset.queries) if wands else set(dev if split == "dev" else test)
        _, audit = audit_qrels(rows, qids & dataset.queries.keys(), entities)
        conflicts = [
            {"query_id": qid, "entity_id": eid, "grades": grades}
            for (qid, eid), grades in sorted(audit.conflicts.items())
        ]
        label_audits[split] = {**asdict(audit), "conflicts": conflicts}
        if conflicts or audit.unknown_queries or audit.unknown_entities:
            failures.append(f"{split}: conflicting labels or invalid query/entity references")
    report = {
        "entities": len(entities),
        "units": len(units),
        "queries": len(dataset.queries),
        "dev_queries": len(dev),
        "test_queries": len(test),
        "empty_fields": dataset.empty_fields,
        "labels": label_audits,
        "failures": failures,
    }
    return report, dev, test, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit official ARC benchmark inputs")
    parser.add_argument("--scifact", type=Path, required=True)
    parser.add_argument("--wands", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    reports = {}
    for name, load, root in (
        ("scifact", load_scifact, args.scifact),
        ("wands", load_wands, args.wands),
    ):
        is_wands = name == "wands"
        try:
            if is_wands:
                for filename in WANDS_BLOBS:
                    verify_wands_blob(root / filename)
            dataset = load(root)
            if not is_wands and dataset.files != SCIFACT_FILES:
                raise ValueError("SciFact file fingerprints differ from the verified BEIR archive")
            report, dev, test, failures = inspect(dataset, wands=is_wands)
        except (OSError, ValueError, KeyError) as error:
            reports[name] = {"failures": [f"{type(error).__name__}: {error}"]}
            print(f"{name}: audit input rejected: {error}")
            continue
        directory = args.output / name
        directory.mkdir(exist_ok=True)
        split_files = {}
        if dev and test:
            for split, ids in (("dev", dev), ("test", test)):
                filename = f"{split}_query_ids.json"
                split_files[filename] = write_json(directory / filename, ids)
        manifest[name] = {
            "source": WANDS_SOURCE if is_wands else SCIFACT_SOURCE,
            "revision": WANDS_REVISION if is_wands else "BEIR official SciFact ZIP",
            "input_sha256": dataset.files,
            "split_sha256": split_files,
        }
        reports[name] = report
        print(
            f"{name}: {report['entities']} entities, {report['queries']} queries; "
            f"{len(dev)} dev/{len(test)} test, {len(failures)} audit failures"
        )
    write_json(args.output / "dataset_manifest.json", manifest)
    write_json(args.output / "audit_report.json", reports)
    return int(any(report["failures"] for report in reports.values()))


if __name__ == "__main__":
    raise SystemExit(main())
