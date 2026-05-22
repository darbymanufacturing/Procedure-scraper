# Procedure Scraper — Car Repair Manual Finder

A Python CLI that searches the internet for **legitimate** car repair manuals (Haynes-style technician guides) and returns links to where they can be downloaded or accessed.

## What it searches

| Source | Type | Cost |
|---|---|---|
| [Haynes Online Manuals](https://haynes.com) | Official catalog | Paid / subscription |
| [AutoZone Repair Guides](https://www.autozone.com/repairguides) | Web-based technician guides | **Free** |
| [Internet Archive](https://archive.org) | Scanned/public-domain PDFs | **Free** |
| Manufacturer owner portals | Official owner's manuals | **Free** |
| DuckDuckGo web search | Filtered to reputable domains | varies |

> **Note:** The tool only surfaces legitimate sources. Pirated or unauthorized PDFs are intentionally filtered out.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Basic search — returns top 5 results
python -m scraper --make Toyota --model Camry --year 2018

# Older vehicle (exercises archive.org)
python -m scraper --make Ford --model Mustang --year 1989

# Show all results from every source
python -m scraper --make Saab --model 9-5 --year 2003 --all

# Show top 10 results as JSON
python -m scraper --make Honda --model Civic --year 2015 --top 10 --json

# Also available as the installed command
repair-manual --make Toyota --model Camry --year 2018
```

### Options

| Flag | Short | Description |
|---|---|---|
| `--make` | `-m` | Vehicle make (e.g. "Toyota") |
| `--model` | `-M` | Vehicle model (e.g. "Camry") |
| `--year` | `-y` | Four-digit model year (e.g. 2018) |
| `--top N` | `-n N` | Max results to show (default: 5) |
| `--all` | `-a` | Show everything from all sources |
| `--json` | `-j` | Output as JSON |

## Example output

```
#1  [WEB] AutoZone Repair Guide: 2018 Toyota Camry
    Source : AutoZone
    URL    : https://www.autozone.com/repairguides/toyota/camry/year-2018
    Note   : Free technician-grade repair guides — no account needed

#2  [PAID/SUBSCRIPTION] 2018 Toyota Camry Haynes Repair Manual
    Source : Haynes
    URL    : https://haynes.com/en-us/toyota/camry/2015-2018-manual
    Note   : Official Haynes manual — purchase or online subscription at haynes.com

#3  [PDF] Toyota Owners Portal: 2018 Toyota Camry Owner's Manual
    Source : Manufacturer Portal
    URL    : https://www.toyota.com/owners/resources/manuals-warranties
    Note   : Free owner's manual from Toyota — select your vehicle on the page
```

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Tests are fully offline — no real HTTP calls are made.

## Project structure

```
scraper/
├── cli.py            # argparse entry point
├── search.py         # concurrent orchestrator
├── models.py         # ManualResult dataclass
├── http.py           # shared session with retries & rate limiting
└── sources/
    ├── base.py       # abstract Source class
    ├── haynes.py
    ├── autozone.py
    ├── archive_org.py
    ├── manufacturer.py
    └── web_search.py
tests/
└── test_sources.py   # fixture-based offline tests
```
