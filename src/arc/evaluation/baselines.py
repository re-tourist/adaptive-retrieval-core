import argparse
import json
import platform
from dataclasses import asdict
from hashlib import file_digest, sha256
from importlib.metadata import version
from pathlib import Path
from statistics import median
from time import perf_counter

from arc.adapters.datasets.scifact import load_scifact
from arc.adapters.datasets.wands import load_wands
from arc.application.search import SearchQuery, SearchService
from arc.evaluation.audit import WANDS_DISPUTED, write_json
from arc.evaluation.metrics import evaluate
from arc.evaluation.runfile import RunRow, read_run, render_run
from arc.evaluation.sensitivity import disputed_sensitivity


def _checked_json(path: Path, fingerprint: str) -> dict | list:
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != fingerprint:
        raise ValueError(f"Admission fingerprint mismatch: {path.name}")
    return json.loads(payload)


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def run(args: argparse.Namespace) -> None:
    root = args.output / args.dataset / args.method
    root.mkdir(parents=True, exist_ok=False)
    wands = args.dataset == "wands"
    loader = load_wands if wands else load_scifact
    dataset = loader(args.data)
    admission = json.loads((args.admission / "dataset_manifest.json").read_bytes())[args.dataset]
    audited = json.loads((args.admission / "audit_report.json").read_bytes())[args.dataset]
    if audited["failures"] or admission["input_sha256"] != dataset.files:
        raise ValueError("Input does not match the admitted dataset")
    corpus, queries = dataset.corpus, dataset.queries
    del dataset
    entities = {entity.key.entity_id for entity in corpus.entities}
    fingerprint = corpus.entities[0].key.revision
    started = perf_counter()
    if args.method == "e1":
        from arc.adapters.retrievers.bm25 import CONFIG, BM25Retriever

        retriever = BM25Retriever(corpus, fingerprint)
        config = CONFIG
        document_truncations = 0
        runtime = {"device": "cpu", "numpy": version("numpy")}
        retriever.index.save(str(root / "index"))
    else:
        import faiss
        import torch

        from arc.adapters.retrievers.dense import MODEL_REVISION, BGEEncoder, DenseRetriever

        if args.model is None or args.model.name != MODEL_REVISION:
            raise ValueError("E2 requires the pinned BGE snapshot directory")
        encoder = BGEEncoder(args.model, args.device, args.batch_size)
        retriever = DenseRetriever(corpus, fingerprint, encoder, snapshot=args.index_from)
        config = retriever.config
        document_truncations = retriever.document_truncations
        runtime = {
            "device": args.device,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(args.device)
            if args.device.startswith("cuda")
            else None,
            "sentence_transformers": version("sentence-transformers"),
            "transformers": version("transformers"),
            "numpy": version("numpy"),
        }
        faiss.write_index(retriever.index, str(root / "index.faiss"))
    build_s = perf_counter() - started
    index_files = tuple(path for path in sorted(root.rglob("*")) if path.is_file())
    print(f"{args.dataset}/{args.method}: indexed {len(entities)} entities", flush=True)
    service = SearchService(retriever, retriever.manifest.compatibility)
    write_json(
        root / "index_manifest.json",
        {
            "index": asdict(retriever.manifest),
            "config": config,
            "documents": len(entities),
            "document_truncations": document_truncations,
            "document_truncation_fraction": document_truncations / len(entities),
            "build_and_save_seconds": build_s,
            "reused_dense_snapshot": args.index_from is not None,
            "index_bytes": sum(path.stat().st_size for path in index_files),
            "index_files_sha256": {
                path.relative_to(root).as_posix(): _digest(path) for path in index_files
            },
            "runtime": {
                **runtime,
                "platform": platform.platform(),
                "python": platform.python_version(),
            },
        },
    )
    write_json(root / "entity_ids.json", sorted(entities))
    domain = corpus.entities[0].key.domain
    for split in ("dev", "test") if args.split == "both" else ("dev",):
        ids_file = f"{split}_query_ids.json"
        query_ids = _checked_json(
            args.admission / args.dataset / ids_file, admission["split_sha256"][ids_file]
        )
        if not isinstance(query_ids, list) or len(set(query_ids)) != len(query_ids):
            raise ValueError("Invalid admitted query IDs")
        if args.smoke:
            query_ids = query_ids[: args.smoke]
        directory = root / split
        directory.mkdir()
        latencies = []
        rows = []
        service.search(SearchQuery(queries[query_ids[0]], domain, 100))
        query_truncations_before = getattr(retriever, "query_truncations", 0)
        for query_id in query_ids:
            query = SearchQuery(queries[query_id], domain, 100)
            before = perf_counter()
            result = service.search(query)
            latencies.append((perf_counter() - before) * 1000)
            if len(result.hits) != 100:
                raise ValueError(f"Expected 100 candidates for query {query_id}")
            rows.extend(
                RunRow(query_id, hit.unit.entity_key.entity_id, rank, hit.score, args.method)
                for rank, hit in enumerate(result.hits, 1)
            )
        text = render_run(rows, set(query_ids), entities)
        run_path = directory / "run.trec"
        run_path.write_text(text, encoding="utf-8", newline="\n")
        # Open the judgments only after the Runfile is frozen.
        filename = f"{split}_qrels.json"
        qrels = _checked_json(
            args.admission / args.dataset / filename, admission["qrels_sha256"][filename]
        )
        qrels = {qid: qrels[qid] for qid in query_ids}
        checked = read_run(text.splitlines(), set(query_ids), entities)
        macro, per_query = evaluate(checked, qrels, entities, wands=wands)
        write_json(directory / "per_query.json", per_query)
        truncations = getattr(retriever, "query_truncations", 0) - query_truncations_before
        write_json(
            directory / "metrics.json",
            {
                "quality": macro,
                "queries": len(query_ids),
                "run_sha256": _digest(run_path),
                "retrieval_latency_ms": {"p50": median(latencies), "p95": _p95(latencies)},
                "query_truncations": truncations,
            },
        )
        if wands and split == "test":
            ledger = _checked_json(WANDS_DISPUTED, admission["disputed_ledger_sha256"])
            write_json(
                directory / "disputed_sensitivity.json",
                disputed_sensitivity({args.method: checked}, qrels, entities, ledger),
            )
        print(f"{args.dataset}/{args.method}/{split}: {len(query_ids)} queries {macro}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ARC M1 full-corpus baselines")
    parser.add_argument("--dataset", required=True, choices=("scifact", "wands"))
    parser.add_argument("--method", required=True, choices=("e1", "e2"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--index-from", type=Path, help="Replay a verified E2 index")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--split", choices=("dev", "both"), default="dev")
    parser.add_argument("--smoke", type=int, default=0)
    args = parser.parse_args()
    if args.index_from and args.method != "e2":
        parser.error("--index-from is only supported for E2")
    if args.smoke < 0 or args.smoke and args.split != "dev":
        parser.error("Smoke is a nonnegative query limit for dev only")
    run(args)


if __name__ == "__main__":
    main()
