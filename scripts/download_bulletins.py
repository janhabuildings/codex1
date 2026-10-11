"""Archive official NYC DOB Buildings Bulletins, using DOB's working navigation."""
import argparse
from pathlib import Path
import sys
from download_tppn import INDEX, archive, official_url

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('references/buildings-bulletins'))
    parser.add_argument('--index-url', default=INDEX)
    args = parser.parse_args()
    source = official_url(args.index_url)
    if not source:
        parser.error('Index URL must be an official NYC webpage')
    sys.exit(0 if archive(args.output,source,collection='bulletins') else 1)
