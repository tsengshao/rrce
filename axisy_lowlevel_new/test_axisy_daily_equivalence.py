import numpy as np
import xarray as xr
import sys
sys.path.insert(1, "../")
import config

# =========================
# paths (adjust if needed)
# =========================
center_flag = "czeta0km_positivemean"
base = f"{config.dataPath}/axisy_lowlevel/{center_flag}"

old_cwv_npz    = f"{base}/cwv.npz"
old_inflow_npz = f"{base}/lowlevel_inflow_0-500m.npz"
new_nc         = f"{base}/axisy_daily_profiles.nc"

# =========================
# load new (reference)
# =========================
ds = xr.open_dataset(new_nc)

# convenience selectors (match old scripts)
# old scripts only used:
#   - period: init / last
#   - method: daily
#   - vtype: mean (index 0) or axisymmetricity (index 1)
ds_daily = ds.sel(method="daily")

# =========================
# load old outputs
# =========================
old_cwv = np.load(old_cwv_npz)
old_inf = np.load(old_inflow_npz)

# old shapes (from your project):
# cwv_daily_init  : (nexp, vtype, radius)
# cwv_daily_last  : (nexp, vtype, radius)
#
# rwind_daily_init: (nexp, vtype, radius)
# rwind_daily_last: (nexp, vtype, radius)
# twind_daily_init: (nexp, vtype, radius)
# twind_daily_last: (nexp, vtype, radius)

# =========================
# helpers
# =========================
def assert_zero_diff(name, diff, tol=1e-4):
    maxabs = np.nanmax(np.abs(diff))
    print(f"{name:30s} max|diff| = {maxabs:.3e}")
    if maxabs > tol:
        raise AssertionError(f"{name} NOT zero (>{tol})")

# =========================
# CWV / radial / tangential wind
# =========================
N = 20
for period in ["init", "last"]:
    # cwv
    new = ds_daily["cwv"].sel(period=period).values[:,:N, :, :]
    old = old_cwv[f"cwv_{period}"][:,:N, :, :].astype(np.float32)
    assert_zero_diff(f"cwv daily {period}", new - old)

    # winds
    new_r = ds_daily["radi_wind_lower"].sel(period=period).values[:,:N, :, :]
    old_r = old_inf[f"rwind_{period}"][:,:N, :, :].astype(np.float32)
    assert_zero_diff(f"rwind daily {period}", new_r - old_r)

    new_t = ds_daily["tang_wind_lower"].sel(period=period).values[:,:N, :, :]
    old_t = old_inf[f"twind_{period}"][:,:N, :, :].astype(np.float32)
    assert_zero_diff(f"twind daily {period}", new_t - old_t)

print("\n✅ ALL TESTS PASSED: new - old == 0")
