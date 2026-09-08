"""Per-stage input/output inventory.

The inventory deliberately names individual scientific files.  Directory
existence alone never counts as a completed stage.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from .config_loader import Case, ConfigSnapshot


CENTER_FLAG = "czeta0km_positivemean"


@dataclass(frozen=True)
class Product:
    path: Path
    role: str
    case_index: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {"path": str(self.path), "role": self.role, "case_index": self.case_index}


NETCDF_VARIABLES: dict[str, tuple[str, ...]] = {
    "cwv": ("cwv", "lwp", "iwp"),
    "convolve": ("zeta", "u", "v"),
    "horisf": ("sf",),
    "axisy_convert": ("cwv", "rain", "radi_wind", "tang_wind"),
    "axisy_mean": ("cwv", "rain", "radi_wind", "tang_wind"),
    "axisy_process": ("radi_wind_lower", "tang_wind_lower", "conv_lower", "w_lower", "rain", "cwv"),
    "axisy_daily": ("cwv", "rain", "radi_wind", "tang_wind"),
}


def validation_for(stage_id: str) -> dict[str, object]:
    strategy = "count_and_last"
    if stage_id in {"center_0", "center_150", "center_sf"}:
        return {"kind": "center_text", "strategy": strategy}
    if stage_id in {"wp_ctl", "convolve_ctl", "sf_ctl"}:
        return {"kind": "ctl", "strategy": strategy}
    if stage_id in {
        "water", "wind", "center_zeta", "center_conzeta", "hov_radial", "hov_tangential",
        "tang_daily", "radi_daily", "mse_ccc_daily", "lowlevel_profiles", "scatter_dry", "scatter_dxx",
    }:
        return {"kind": "png", "strategy": strategy}
    if stage_id in {
        "cwv", "convolve", "horisf", "axisy_convert", "axisy_mean", "axisy_process", "axisy_daily",
        "lowlevel_exp",
    }:
        return {
            "kind": "netcdf",
            "required_variables": list(NETCDF_VARIABLES.get(stage_id, ())),
            "strategy": strategy,
        }
    return {"kind": "nonempty", "strategy": strategy}


def _center_text_error(path: Path, total_t: int | None) -> str | None:
    if total_t is None:
        return "center validation has no expected timestep count"
    timesteps: list[int] = []
    try:
        for line in path.read_text().splitlines():
            fields = line.split()
            if len(fields) < 2:
                continue
            try:
                timestep = int(fields[0])
                values = [float(value) for value in fields[1:]]
            except ValueError:
                continue
            if not all(math.isfinite(value) for value in values):
                return f"center row {timestep} contains a non-finite value"
            timesteps.append(timestep)
    except (OSError, UnicodeError) as exc:
        return f"cannot read center text: {exc}"
    if timesteps != list(range(total_t)):
        return f"center timesteps are incomplete: expected 0..{total_t - 1}, found {len(timesteps)} rows"
    return None


def product_error(
    product: Product | dict[str, Any],
    validation: dict[str, object] | None = None,
    case_total_t: int | None = None,
) -> str | None:
    """Return why a product is invalid, or ``None`` when it is reusable."""
    path = product.path if isinstance(product, Product) else Path(product["path"])
    role = product.role if isinstance(product, Product) else product.get("role")
    if not path.is_file():
        return "missing"
    try:
        if path.stat().st_size <= 0:
            return "empty file"
    except OSError as exc:
        return f"cannot stat file: {exc}"
    rule = dict(validation or {"kind": "nonempty"})
    kind = str(rule.get("kind", "nonempty"))
    if role == "ctl" or path.suffix.lower() == ".ctl":
        kind = "ctl"
    elif role == "figure" or path.suffix.lower() == ".png":
        kind = "png"
    if kind == "nonempty":
        return None
    if kind == "center_text":
        return _center_text_error(path, case_total_t)
    if kind == "ctl":
        try:
            text = path.read_text(errors="replace").upper()
        except OSError as exc:
            return f"cannot read CTL: {exc}"
        missing = [token for token in ("DSET", "TDEF", "VARS", "ENDVARS") if token not in text]
        return f"CTL missing directives: {', '.join(missing)}" if missing else None
    if kind == "png":
        try:
            with path.open("rb") as stream:
                signature = stream.read(8)
        except OSError as exc:
            return f"cannot read PNG: {exc}"
        return None if signature == b"\x89PNG\r\n\x1a\n" else "invalid PNG signature"
    if kind == "netcdf":
        try:
            from netCDF4 import Dataset
            with Dataset(path, "r") as dataset:
                required = [str(value) for value in rule.get("required_variables", [])]
                missing = [name for name in required if name not in dataset.variables]
                if missing:
                    return f"NetCDF missing variables: {', '.join(missing)}"
        except Exception as exc:
            return f"cannot open NetCDF: {exc}"
        return None
    return f"unknown validation kind: {kind}"


def _series(root: Path, prefix: str, count: int, case: Case) -> list[Product]:
    return [Product(root / f"{prefix}-{it:06d}.nc", "data", case.index) for it in range(count)]


def outputs_for(stage_id: str, cfg: ConfigSnapshot, product_settings: dict[str, object] | None = None) -> list[Product]:
    data = cfg.data_path
    settings = product_settings or {}
    products: list[Product] = []
    for case in cfg.cases:
        exp, n = case.experiment, case.total_t
        if stage_id == "cwv":
            products += _series(data / "wp" / exp, "wp", n, case)
        elif stage_id == "convolve":
            products += _series(data / "convolve" / exp / "150km", "conv", n, case)
        elif stage_id == "horisf":
            products += _series(data / "horimsf" / exp, "horimsf", n, case)
        elif stage_id == "center_0":
            products.append(Product(data / "find_center" / CENTER_FLAG / f"{exp}.txt", "data", case.index))
        elif stage_id == "center_150":
            products.append(Product(data / "find_center" / "czeta150km_positivemean" / f"{exp}.txt", "data", case.index))
        elif stage_id == "center_sf":
            products.append(Product(data / "find_center" / "sf_positivemean" / f"{exp}.txt", "data", case.index))
        elif stage_id == "cloud":
            for it in range(n):
                products.append(Product(data / "cloud" / exp / f"cld_{it:06d}.txt", "data", case.index))
                products.append(Product(data / "cloud" / exp / f"ccc_{it:06d}.txt", "data", case.index))
        elif stage_id == "wp_ctl":
            products.append(Product(data / "wp" / f"{exp}.ctl", "ctl", case.index))
        elif stage_id == "convolve_ctl":
            products.append(Product(data / "convolve" / exp / "convolve.ctl", "ctl", case.index))
        elif stage_id == "sf_ctl":
            products.append(Product(data / "horimsf" / f"msf_{exp}.ctl", "ctl", case.index))
        elif stage_id == "axisy_convert":
            products += _series(data / "axisy" / CENTER_FLAG / exp, "axisy", n, case)
            products.append(Product(data / "axisy" / CENTER_FLAG / f"axisy_{exp}.ctl", "ctl", case.index))
        elif stage_id == "axisy_mean":
            root = data / "axisy" / CENTER_FLAG / exp
            products += _series(root, "axmean", n, case)
        elif stage_id == "axisy_process":
            root = data / "axisy" / CENTER_FLAG / exp
            products += _series(root, "axmean_process", n, case)
        elif stage_id == "axisy_daily":
            root = data / "axisy" / CENTER_FLAG / exp
            products += _series(root, "axmean_daily", n // 72, case)
        elif stage_id in {"hov_radial", "hov_tangential"}:
            component = "radi_wind" if stage_id == "hov_radial" else "tang_wind"
            root = data / "workflow_figures" / cfg.dataset_tag / stage_id / exp
            products.append(Product(root / f"{component}_{exp}.png", "figure", case.index))
            products.append(Product(root / f"series_{component}_{exp}.png", "figure", case.index))
        elif stage_id in {"tang_daily", "radi_daily", "mse_ccc_daily"}:
            root = data / "workflow_figures" / cfg.dataset_tag / stage_id / exp
            day_count = (n - 1) // int(24 * 60 / case.dt_minutes)
            products += [Product(root / f"{day:06d}.png", "figure", case.index) for day in range(day_count)]
        elif stage_id in {"water", "wind", "center_zeta", "center_conzeta"}:
            root = data / "workflow_figures" / cfg.dataset_tag / stage_id / exp
            if stage_id in {"water", "wind"}:
                prefix = f"whi_{stage_id}"
            else:
                variable = "zeta" if stage_id == "center_zeta" else "conzeta"
                prefix = f"{variable}_9_150km"
            products += [Product(root / f"{prefix}_{it:06d}.png", "figure", case.index) for it in range(1, n + 1)]
    if stage_id == "lowlevel_exp":
        products.append(Product(
            data / "axisy_lowlevel" / CENTER_FLAG / f"axisy_exp_daily_profiles_{cfg.dataset_tag}.nc",
            "data",
        ))
    figure_root = data / "workflow_figures" / cfg.dataset_tag / "lowlevel"
    if stage_id == "lowlevel_profiles":
        for case in cfg.cases:
            for day in settings.get("lowlevel_days", (0, 3)):
                products.append(Product(
                    figure_root / f"{CENTER_FLAG}_sap_white" / "inflow_daily" / "exp" /
                    f"{case.experiment}_day{day}_daily.png", "figure", case.index
                ))
    elif stage_id == "scatter_dry":
        products.append(Product(figure_root / f"{CENTER_FLAG}_white" / "inflow_daily" / "scatter_DRY.png", "figure"))
    elif stage_id == "scatter_dxx":
        products.append(Product(figure_root / f"{CENTER_FLAG}_white" / "inflow_daily" / "scatter_DXX.png", "figure"))
    return products


def _product_path(product: Product | dict[str, Any]) -> Path:
    return product.path if isinstance(product, Product) else Path(product["path"])


def _product_case(product: Product | dict[str, Any]) -> int | None:
    return product.case_index if isinstance(product, Product) else product.get("case_index")


def _product_kind(product: Product | dict[str, Any], validation: dict[str, object]) -> str:
    path = _product_path(product)
    role = product.role if isinstance(product, Product) else product.get("role")
    if role == "ctl" or path.suffix.lower() == ".ctl":
        return "ctl"
    if role == "figure" or path.suffix.lower() == ".png":
        return "png"
    return str(validation.get("kind", "nonempty"))


def inspect_products(
    products: list[Product | dict[str, Any]],
    validation: dict[str, object] | None = None,
    case_total_t: dict[int, int] | None = None,
) -> dict[str, Any]:
    """Count every expected file, then content-check only the last file per kind/case."""
    rule = dict(validation or {"kind": "nonempty", "strategy": "count_and_last"})
    existing, valid, missing = [], [], []
    invalid: list[dict[str, str]] = []
    groups: dict[int | None, list[Product | dict[str, Any]]] = {}
    for product in products:
        groups.setdefault(_product_case(product), []).append(product)

    for case_index, group in groups.items():
        present: list[Product | dict[str, Any]] = []
        for product in group:
            path = _product_path(product)
            if path.is_file():
                existing.append(str(path))
                present.append(product)
            else:
                missing.append(str(path))
        if len(present) != len(group):
            continue

        last_by_kind: dict[str, Product | dict[str, Any]] = {}
        for product in group:
            last_by_kind[_product_kind(product, rule)] = product
        sample_errors: list[dict[str, str]] = []
        for product in last_by_kind.values():
            error = product_error(product, rule, (case_total_t or {}).get(case_index))
            if error is not None:
                sample_errors.append({"path": str(_product_path(product)), "reason": error})
        if sample_errors:
            invalid.extend(sample_errors)
        else:
            valid.extend(str(_product_path(product)) for product in group)
    return {"existing": existing, "valid": valid, "missing": missing, "invalid": invalid}


def inputs_for(stage_id: str, cfg: ConfigSnapshot, external: dict[str, str]) -> list[Path]:
    result: list[Path] = []
    if stage_id in {"lowlevel_profiles", "scatter_dry", "scatter_dxx"}:
        value = external.get("control_profile_nc")
        if value:
            result.append(Path(value).expanduser().resolve(strict=False))
    return result
