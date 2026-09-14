import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
LOCAL_MODULES = {path.stem for path in SRC_DIR.iterdir() if path.suffix == ".py" or path.is_dir()}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_runtime_distributions() -> set[str]:
    declared: set[str] = set()
    for raw in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            declared.add(_normalize(re.split(r"[\[=<>~!; ]", line, maxsplit=1)[0]))
    return declared


def _third_party_imports() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for file in SRC_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top not in sys.stdlib_module_names and top not in LOCAL_MODULES:
                    found.setdefault(top, set()).add(str(file.relative_to(REPO_ROOT)))
    return found


def test_every_third_party_import_in_src_is_a_runtime_dependency() -> None:
    # La imagen Docker solo instala requirements.txt; lo que viva únicamente en
    # requirements-dev.txt pasa el CI pero rompe el arranque en producción.
    declared = _declared_runtime_distributions()
    installed = packages_distributions()

    missing = {
        module: sorted(files)
        for module, files in _third_party_imports().items()
        if not {_normalize(dist) for dist in installed.get(module, [module])} & declared
    }

    assert not missing, f"importados en src/ pero ausentes en requirements.txt: {missing}"
