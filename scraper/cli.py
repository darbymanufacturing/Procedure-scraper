"""CLI entry point for the car repair manual scraper.

Usage:
    python -m scraper --make Toyota --model Camry --year 2018
    python -m scraper --make Ford --model Mustang --year 1989 --all
    python -m scraper --make Saab --model 9-5 --year 2003 --top 10 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from scraper.search import search_manuals


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="repair-manual",
        description="Search the internet for legitimate car repair manuals and return links.",
    )
    p.add_argument("--make", "-m", required=True, help='Vehicle make, e.g. "Toyota"')
    p.add_argument("--model", "-M", required=True, help='Vehicle model, e.g. "Camry"')
    p.add_argument("--year", "-y", required=True, type=int, help="Four-digit model year, e.g. 2018")
    p.add_argument(
        "--top",
        "-n",
        type=int,
        default=5,
        help="Maximum number of results to show (default: 5)",
    )
    p.add_argument(
        "--all",
        "-a",
        action="store_true",
        default=False,
        help="Show all results from all sources (overrides --top)",
    )
    p.add_argument(
        "--json",
        "-j",
        action="store_true",
        default=False,
        help="Output as JSON",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.year < 1900 or args.year > 2100:
        print(f"Error: year {args.year} looks wrong. Use a four-digit year.", file=sys.stderr)
        sys.exit(1)

    print(
        f"\n🔍 Searching for repair manuals: {args.year} {args.make} {args.model} …\n",
        file=sys.stderr,
    )

    results = search_manuals(
        make=args.make,
        model=args.model,
        year=args.year,
        top_n=args.top,
        all_results=getattr(args, "all"),
    )

    if not results:
        print("No results found. Try different make/model/year or check your internet connection.")
        sys.exit(0)

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        print(f"Found {len(results)} result(s):\n")
        for i, result in enumerate(results, 1):
            print(f"#{i}  {result}\n")


if __name__ == "__main__":
    main()
