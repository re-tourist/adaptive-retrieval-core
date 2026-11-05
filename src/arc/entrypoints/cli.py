import argparse
import json
import sys
from contextlib import redirect_stdout

from arc.application.harness import STRATEGIES
from arc.application.search import SearchQuery
from arc.bootstrap import configured_harness
from arc.entrypoints.presentation import present


def main() -> None:
    parser = argparse.ArgumentParser(prog="arc")
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--domain", choices=("technical", "product"))
    search.add_argument("--strategy", choices=STRATEGIES, default="bm25")
    search.add_argument("--top-k", type=int, default=10)
    search.add_argument("--entity-id", action="append")
    search.add_argument("--units", action="store_true")
    search.add_argument("--trace", action="store_true")
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn

        uvicorn.run("arc.entrypoints.api:factory", factory=True, host=args.host, port=args.port)
        return
    try:
        # Third-party startup notices belong on stderr, leaving stdout as one JSON value.
        with redirect_stdout(sys.stderr):
            harness = configured_harness()
            query = SearchQuery(
                args.query,
                args.domain or harness.domain,
                args.top_k,
                frozenset(args.entity_id) if args.entity_id is not None else None,
            )
            response = harness.search(query, args.strategy)
    except (KeyError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(present(response, units=args.units, trace=args.trace), ensure_ascii=True))


if __name__ == "__main__":
    main()
