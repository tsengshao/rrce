"""Execute a snapshotted Python script with a snapshotted config module."""

from __future__ import annotations

import argparse
import importlib.util
import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    ns = parser.parse_args()
    args = ns.args[1:] if ns.args[:1] == ["--"] else ns.args
    config = ns.config.resolve(strict=True)
    script = ns.script.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("config", config)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load config snapshot: {config}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["config"] = module
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)

    snapshot_root = script.parents[1]
    helper = snapshot_root / "axisy"
    sys.path[:] = [str(script.parent), str(snapshot_root), str(helper), *sys.path]
    os.chdir(script.parent)
    sys.argv = [str(script), *args]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
