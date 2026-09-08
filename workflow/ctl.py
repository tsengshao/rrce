"""Generate CTL files for one validated case at a time."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


LEVELS = """0 37 112 194 288 395 520 667 843 1062
 1331 1664 2055 2505 3000 3500 4000 4500 5000 5500
 6000 6500 7000 7500 8000 8500 9000 9500 10000 10500
 11000 11500 12000 12500 13000 13500 14000 14500"""


def render_ctl(kind: str, experiment: str, total_t: int, dt: int) -> str:
    common = (
        "DTYPE netcdf\nOPTIONS template\nTITLE RRCE workflow product\nUNDEF 99999.\n"
        "CACHESIZE 10000000\nXDEF 384 LINEAR -5.1674137 .0269838\n"
        "YDEF 384 LINEAR -5.1674137 .0269838\n"
    )
    time = f"TDEF {total_t} LINEAR 01JAN1998 {dt}mn\n"
    if kind == "wp":
        return (f"DSET ^./{experiment}/wp-%tm6.nc\n" + common + "ZDEF 1 LEVELS 1000\n" + time +
                "VARS 3\ncwv=>cwv 0 t,y,x cwv\nlwp=>lwp 0 t,y,x lwp\niwp=>iwp 0 t,y,x iwp\nENDVARS\n")
    if kind == "sf":
        return (f"DSET ^./{experiment}/horimsf-%tm6.nc\n" + common + f"ZDEF 38 LEVELS {LEVELS}\n" + time +
                "VARS 1\nsf=>msf 38 t,z,y,x horizontal mass stream function\nENDVARS\n")
    if kind == "convolve":
        return ("DSET ^./%e/conv-%tm6.nc\n" + common + f"ZDEF 38 LEVELS {LEVELS}\n" + time +
                "EDEF 1 NAMES 150km\nVARS 3\nzeta=>zeta 38 t,z,y,x zeta\n"
                "u=>u 38 t,z,y,x u\nv=>v 38 t,z,y,x v\nENDVARS\n")
    raise ValueError(f"unknown CTL kind: {kind}")


def atomic_write(path: Path, text: str, allow_overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not allow_overwrite:
        raise FileExistsError(path)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("wp", "sf", "convolve"), required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--total-t", type=int, required=True)
    parser.add_argument("--dt", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-overwrite", action="store_true")
    args = parser.parse_args()
    atomic_write(args.output, render_ctl(args.kind, args.experiment, args.total_t, args.dt), args.allow_overwrite)


if __name__ == "__main__":
    main()
