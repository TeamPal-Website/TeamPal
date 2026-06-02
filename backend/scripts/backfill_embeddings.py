import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tasks.embeddings import recompute_all_embeddings


def main() -> int:
    result = recompute_all_embeddings()
    print('Backfill complete:', result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
