from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
LOGS_ROOT = PROJECT_ROOT / "scripts/logs"


def ensure_roots_exist() -> None:
    """Ensure root dirs exist."""
    for root_path in (DATA_ROOT, SCRIPTS_ROOT, LOGS_ROOT):
        if not root_path.exists():
            root_path.mkdir(parents=True, exist_ok=True)


ensure_roots_exist()
