"""Tool path configuration and discovery (Phase 3 / M3.1).

Resolution order for every tool path:
CLI argument > environment variable > configs/tools.yml > PATH probe > built-in
candidates. CLI arguments are passed in later by the pipeline (M3.3); this
module exposes them as explicit-override parameters.

The discovery behavior ports scripts/evaluation/eval_checker.sh, which is the
reference implementation for CodeFuse path resolution.
"""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

TOOLS_CONFIG_FILE = Path("configs/tools.yml")

# Built-in CodeFuse candidates, ported from eval_checker.sh.
CODEFUSE_FALLBACK_HOMES = (
    "{home}/Workspace/Tools/static-analysis-tools/codefuse/sparrow-cli",
    "{home}/tools/static-analysis-tools/codefuse/sparrow-cli",
    "/opt/codefuse/sparrow-cli",
)

LOCAL_LIB_REL = Path("rules/codefuse-query/lib")


@dataclass
class CodeFuseToolConfig:
    """`codefuse:` section of configs/tools.yml (null = probe at runtime)."""
    home: Optional[str] = None
    godel_bin: Optional[str] = None
    official_lib: Optional[str] = None


@dataclass
class CodeQLToolConfig:
    """`codeql:` section of configs/tools.yml."""
    bin: str = "codeql"


@dataclass
class DatabasesConfig:
    """`databases:` section of configs/tools.yml (relative to project root)."""
    codefuse: Path = Path("dataset/codefuse-db")
    codeql: Path = Path("dataset/codeql-db/benchmark-java")


@dataclass
class EnvChecksConfig:
    """`env_checks:` section of configs/tools.yml."""
    codefuse_java_env: bool = True


@dataclass
class ToolsConfig:
    """Parsed configs/tools.yml. Tool paths stay raw; discovery resolves them."""
    codefuse: CodeFuseToolConfig = field(default_factory=CodeFuseToolConfig)
    codeql: CodeQLToolConfig = field(default_factory=CodeQLToolConfig)
    databases: DatabasesConfig = field(default_factory=DatabasesConfig)
    env_checks: EnvChecksConfig = field(default_factory=EnvChecksConfig)
    source_file: Optional[Path] = None


@dataclass(frozen=True)
class CodeFusePaths:
    """Fully resolved CodeFuse paths for one machine."""
    home: Path
    godel_bin: Path
    official_lib: Path
    local_lib: Path


def load_tools_config(
    config_file: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> ToolsConfig:
    """Load configs/tools.yml; missing file or keys fall back to defaults."""
    root = _project_root(project_root)
    path = config_file if config_file is not None else root / TOOLS_CONFIG_FILE

    config = ToolsConfig()
    if not path.is_file():
        return config

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    codefuse = data.get("codefuse") or {}
    config.codefuse = CodeFuseToolConfig(
        home=codefuse.get("home"),
        godel_bin=codefuse.get("godel_bin"),
        official_lib=codefuse.get("official_lib"),
    )

    codeql = data.get("codeql") or {}
    config.codeql = CodeQLToolConfig(bin=codeql.get("bin") or "codeql")

    databases = data.get("databases") or {}
    config.databases = DatabasesConfig(
        codefuse=Path(databases.get("codefuse") or DatabasesConfig.codefuse),
        codeql=Path(databases.get("codeql") or DatabasesConfig.codeql),
    )

    env_checks = data.get("env_checks") or {}
    config.env_checks = EnvChecksConfig(
        codefuse_java_env=bool(env_checks.get("codefuse_java_env", True)),
    )
    config.source_file = path
    return config


def discover_codefuse(
    config: ToolsConfig,
    project_root: Optional[Path] = None,
    home_override: Optional[str] = None,
    godel_bin_override: Optional[str] = None,
    official_lib_override: Optional[str] = None,
) -> Tuple[Optional[CodeFusePaths], List[str]]:
    """Resolve CodeFuse paths. Returns (paths, notes); paths is None when no
    usable home directory was found. Notes describe non-obvious fallbacks."""
    root = _project_root(project_root)
    cfg = config.codefuse
    notes: List[str] = []

    home = _first_existing_str([
        home_override,
        os.environ.get("CODEFUSE_HOME"),
        cfg.home,
    ])
    source = "explicit" if home else "probe"
    if not home:
        home = _codefuse_home_from_path_sparrow()
        if home:
            source = "sparrow-in-PATH"
    if not home:
        home, note = _codefuse_home_from_fallbacks()
        if home:
            source = "built-in candidates"
            notes.append(note)

    if not home:
        return None, notes

    home_path = Path(home).expanduser().resolve()

    godel_bin = _first_existing_str([
        godel_bin_override,
        os.environ.get("GODEL_BIN"),
        cfg.godel_bin,
    ])
    godel_path = (
        Path(godel_bin).expanduser().resolve()
        if godel_bin
        else home_path / "godel-script" / "usr" / "bin" / "godel"
    )

    official_lib = _first_existing_str([
        official_lib_override,
        os.environ.get("OFFICIAL_LIB"),
        cfg.official_lib,
    ])
    official_path = (
        Path(official_lib).expanduser().resolve()
        if official_lib
        else home_path / "lib"
    )

    paths = CodeFusePaths(
        home=home_path,
        godel_bin=godel_path,
        official_lib=official_path,
        local_lib=(root / LOCAL_LIB_REL).resolve(),
    )
    if source == "explicit":
        notes.append(f"CodeFuse home: {home_path}")
    return paths, notes


def discover_codeql(
    config: ToolsConfig,
    project_root: Optional[Path] = None,
    bin_override: Optional[str] = None,
) -> Tuple[Optional[Path], List[str]]:
    """Resolve the CodeQL CLI. Returns (path_or_None, notes)."""
    candidate = _first_existing_str([
        bin_override,
        os.environ.get("CODEQL_BIN"),
        config.codeql.bin,
    ])
    if not candidate:
        return None, []

    if os.sep in candidate or "/" in candidate:
        return Path(candidate).expanduser().resolve(), []

    found = shutil.which(candidate)
    if found:
        return Path(found).resolve(), []
    return None, []


def _codefuse_home_from_path_sparrow() -> Optional[str]:
    """Port of eval_checker.sh: derive home from the sparrow binary in PATH."""
    sparrow = shutil.which("sparrow")
    if not sparrow:
        return None
    return os.path.dirname(os.path.realpath(sparrow))


def _codefuse_home_from_fallbacks() -> Tuple[Optional[str], str]:
    """Probe the built-in candidates; a candidate qualifies only when it looks
    like a complete sparrow-cli installation (godel + lib), matching
    eval_checker.sh."""
    for raw in CODEFUSE_FALLBACK_HOMES:
        candidate = Path(raw.format(home=os.environ.get("HOME", "")).rstrip("/"))
        godel = candidate / "godel-script" / "usr" / "bin" / "godel"
        if godel.is_file() and os.access(godel, os.X_OK) and (candidate / "lib").is_dir():
            note = (
                f"⚠️  CodeFuse 从内置候选路径自动回退找到: {candidate}；"
                "建议设置 CODEFUSE_HOME 或在 configs/tools.yml 固化。"
            )
            return str(candidate), note
    return None, ""


def _first_existing_str(values: List[Optional[str]]) -> Optional[str]:
    for value in values:
        if value:
            return value
    return None


def _project_root(project_root: Optional[Path]) -> Path:
    if project_root is not None:
        return project_root
    return Path(__file__).resolve().parents[2]
