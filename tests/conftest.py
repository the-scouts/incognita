from pathlib import Path
import sys

# https://github.com/pytest-dev/pytest/issues/2421#issuecomment-403724503
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
