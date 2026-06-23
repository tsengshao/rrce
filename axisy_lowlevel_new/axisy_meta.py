# axisy_meta.py
"""
Helpers for RRCE axisymmetric (ring-mean) diagnostics.

This module centralizes:
- restart_day parsing from experiment name
- how to map restart_day -> "init" averaging window in CTRL (RRCE_3km_f00)
- the default "last" averaging window (it=145..216 inclusive; i.e., range(145, 217))

So you don't have to duplicate fragile string-parsing logic across scripts.
"""

from __future__ import annotations

def parse_restart_day(exp: str) -> float:
    """
    Parse restart_day from experiment name.

    Rules (matching your current project):
    - exp == 'RRCE_3km_f00' or 'RRCE_3km_f10' -> rday = 0
    - otherwise, the last token like '14p986' becomes 14.986
    - cluster_*_d20 uses the final token d20 -> 20
    """
    if exp in ("RRCE_3km_f00", "RRCE_3km_f10"):
        return 0.0
    token = exp.split("_")[-1]
    if token.startswith("d"):
        token = token[1:]
    return float(token.replace("p", "."))


def ctrl_day_from_case_day(case_day: float, force_exact: bool = False, tolerance_hours: float = 3.0) -> float:
    """
    Map original case_day to the CTRL day used for plotting.

    - If force_exact is True, keep the original case_day.
    - Otherwise, case_day within +/- tolerance_hours of an integer day is rounded
      to that integer day.
    - Other fractional days are kept as-is.
    """
    case_day = float(round(float(case_day), 10))
    if force_exact:
        return case_day

    tolerance_day = tolerance_hours / 24.0
    nearest_integer = round(case_day)
    if abs(case_day - nearest_integer) <= tolerance_day:
        return float(nearest_integer)
    return case_day


def init_window_from_restart_day(rday: float, nperday: int = 72) -> tuple[int, int]:
    """
    Map restart_day -> (it0, it1) in CTRL (RRCE_3km_f00) for the "init daily mean".

    Your confirmed convention:
    - rday == 0: use a single sample as "daily mean" -> (0, 1)
    - else: use day-mean window with 72 samples/day:
        it0 = int((rday-1)*72)
        it1 = int(rday*72)
      meaning average over range(it0, it1)
    """
    if rday == 0:
        return 0, 1
    it0 = int((rday - 1) * nperday)
    it1 = int(rday * nperday)
    return it0, it1


def last_window_default() -> tuple[int, int]:
    """
    Default "last day" window.

    Your confirmed convention: range(145, 217) (72 samples).
    """
    return 145, 217
