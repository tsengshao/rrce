"""Load and validate the small, declarative contract exposed by a config file."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterable


TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Case:
    index: int
    experiment: str
    label: str
    total_t: int
    dt_minutes: int
    case_day: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "experiment": self.experiment,
            "label": self.label,
            "total_t": self.total_t,
            "dt_minutes": self.dt_minutes,
            "case_day": self.case_day,
        }


@dataclass(frozen=True)
class ConfigSnapshot:
    path: Path
    sha256: str
    vvm_path: Path
    data_path: Path
    dataset_tag: str
    dataset_tag_source: str
    cases: tuple[Case, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("_rrce_workflow_config", path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"config: cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise ConfigError(f"config: failed to load {path}: {exc}") from exc
    finally:
        sys.dont_write_bytecode = previous
    return module


def resolve_dataset_tag(config_path: Path, explicit: str | None) -> tuple[str, str]:
    if explicit is not None:
        tag, source = explicit, "explicit"
    else:
        match = re.fullmatch(r"config_(.+)\.py", config_path.name)
        if not match or not match.group(1):
            raise ConfigError("dataset_tag: required for config.py or a non config_<name>.py file")
        tag, source = match.group(1), "config_filename"
    if tag in {".", ".."} or not TAG_RE.fullmatch(tag):
        raise ConfigError("dataset_tag: use one component containing letters, digits, '_' or '-'")
    return tag, source


def parse_restart_day(experiment: str) -> float | None:
    if experiment in {"RRCE_3km_f00", "RRCE_3km_f10"}:
        return 0.0
    candidates = re.findall(r"(?:^|_)d(\d+(?:p\d+|\.\d+)?)(?=_|$)", experiment)
    if len(candidates) != 1:
        return None
    return float(candidates[0].replace("p", "."))


def _absolute_dir(module: ModuleType, name: str) -> Path:
    value = getattr(module, name, None)
    if not isinstance(value, (str, os.PathLike)):
        raise ConfigError(f"{name}: expected an absolute path string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ConfigError(f"{name}: expected an absolute path, got {value!r}")
    return path.resolve(strict=False)


def load_config(
    config: str | os.PathLike[str],
    indexes: Iterable[int],
    dataset_tag: str | None = None,
    case_days: dict[str, float] | None = None,
) -> ConfigSnapshot:
    path = Path(config).expanduser().resolve()
    if not path.is_file():
        raise ConfigError(f"config: not a regular file: {path}")
    module = _load_module(path)
    exp_list = getattr(module, "expList", None)
    total_t = getattr(module, "totalT", None)
    expdict = getattr(module, "expdict", None)
    if not isinstance(exp_list, (list, tuple)) or not exp_list:
        raise ConfigError("expList: expected a non-empty list")
    if not isinstance(total_t, (list, tuple)) or len(total_t) != len(exp_list):
        raise ConfigError("totalT: must be a list with the same length as expList")
    if not isinstance(expdict, dict):
        raise ConfigError("expdict: expected a mapping")

    selected = tuple(indexes)
    if not selected:
        raise ConfigError("cases: at least one zero-based index is required")
    if len(set(selected)) != len(selected):
        raise ConfigError("cases: duplicate indexes are not allowed")
    tag, tag_source = resolve_dataset_tag(path, dataset_tag)
    day_overrides = case_days or {}
    cases: list[Case] = []
    for index in selected:
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(exp_list):
            raise ConfigError(f"cases: index {index!r} is outside 0..{len(exp_list) - 1}")
        experiment = exp_list[index]
        if not isinstance(experiment, str) or not experiment or "/" in experiment or "\\" in experiment:
            raise ConfigError(f"expList[{index}]: expected a non-empty path-safe name")
        label = expdict.get(experiment)
        if not isinstance(label, str) or not label:
            raise ConfigError(f"expdict[{experiment!r}]: missing non-empty label")
        value = total_t[index]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"totalT[{index}]: expected a positive integer")
        try:
            dt = module.getExpDeltaT(experiment)
        except Exception as exc:
            raise ConfigError(f"getExpDeltaT({experiment!r}): {exc}") from exc
        if isinstance(dt, bool) or not isinstance(dt, (int, float)) or dt <= 0 or int(dt) != dt:
            raise ConfigError(f"getExpDeltaT({experiment!r}): expected positive whole minutes")
        day = day_overrides.get(experiment, parse_restart_day(experiment))
        cases.append(Case(index, experiment, label, value, int(dt), day))

    return ConfigSnapshot(
        path=path,
        sha256=sha256_file(path),
        vvm_path=_absolute_dir(module, "vvmPath"),
        data_path=_absolute_dir(module, "dataPath"),
        dataset_tag=tag,
        dataset_tag_source=tag_source,
        cases=tuple(cases),
    )
