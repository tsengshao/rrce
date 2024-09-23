import numpy as np

def qv_sat(t_K, p_Pa):
    ep_2 = 0.622
    i_type = np.where(t_K>=273.15, 0, 1)
    e_pres = polysvp1(t_K, i_type)  #Pa
    qv_sat = ep_2*e_pres/np.maximum(1.e-3,(p_Pa-e_pres))
    return qv_sat

import numpy as np

def polysvp1(T, i_type):
    """
    Compute the saturation vapor pressure for an array of temperatures.

    Parameters:
    T (array-like): Array of temperatures in Kelvin.
    i_type (array-like): Saturation with respect to liquid (0) or ice (1).

    Returns:
    array-like: Array of saturation vapor pressures in Pa.
    """
    # Convert input to numpy array
    T = np.asarray(T)

    # Constants for ice
    a0i, a1i, a2i, a3i, a4i, a5i, a6i, a7i, a8i = (
        6.11147274, 0.503160820, 0.188439774e-1,
        0.420895665e-3, 0.615021634e-5, 0.602588177e-7,
        0.385852041e-9, 0.146898966e-11, 0.252751365e-14
    )

    # Constants for liquid
    a0, a1, a2, a3, a4, a5, a6, a7, a8 = (
        6.11239921, 0.443987641, 0.142986287e-1,
        0.264847430e-3, 0.302950461e-5, 0.206739458e-7,
        0.640689451e-10, -0.952447341e-13, -0.976195544e-15
    )

    dt = T - 273.15
    output = np.zeros(T.shape)

    # Ice conditions (i_type = 1 and T < 273.15)
    # ! use Goff-Gratch for T < 195.8 K and Flatau et al. equal or above 195.8 K
    ice_mask = (i_type == 1) & (T < 273.15)
    ice_ge_1958_mask = ice_mask & (T >= 195.8)
    ice_lt_1958_mask = ice_mask & (T < 195.8)

    if np.any(ice_ge_1958_mask):
      dt_mask = dt[ice_ge_1958_mask]
      ice_ge_1958 = (a0i + dt_mask*(a1i + dt_mask*(a2i + dt_mask*(a3i + dt_mask*(a4i + dt_mask*(a5i + dt_mask*(a6i + dt_mask*(a7i + a8i*dt_mask))))))))
      ice_ge_1958 *= 100
      output[ice_ge_1958_mask] = ice_ge_1958
 
    if np.any(ice_lt_1958_mask):
      T_mask = T[ice_lt_1958_mask]
      ice_lt_1958 = (10.0**(-9.09718*(273.16/T_mask - 1.0) - 
                    3.56654*np.log10(273.16/T_mask) + 
                    0.876793*(1.0 - T_mask/273.16) + 
                    np.log10(6.1071))) * 100.0
      output[ice_lt_1958_mask] = ice_lt_1958

    # Liquid conditions (i_type = 0 or T >= 273.15)
    # ! use Goff-Gratch for T < 202.0 K and Flatau et al. equal or above 202.0 K
    liquid_mask = (i_type == 0) | (T >= 273.15)
    liquid_ge_2020_mask = liquid_mask & (T >= 202.0)
    liquid_lt_2020_mask = liquid_mask & (T < 202.0)

    if np.any(liquid_ge_2020_mask):
      dt_mask = dt[liquid_ge_2020_mask]
      liquid_ge_2020 = (a0 + dt_mask*(a1 + dt_mask*(a2 + dt_mask*(a3 + dt_mask*(a4 + dt_mask*(a5 + dt_mask*(a6 + dt_mask*(a7 + a8*dt_mask))))))))
      liquid_ge_2020 *= 100.0
      output[liquid_ge_2020_mask] = liquid_ge_2020

    # ! note: uncertain below -70 C, but produces physical values (non-negative) unlike flatau
    if np.any(liquid_lt_2020_mask):
      T_mask  = T[liquid_lt_2020_mask]
      liquid_lt_2020 = (10.0**(-7.90298*(373.16/T_mask - 1.0) + 
                       5.02808*np.log10(373.16/T_mask) - 
                       1.3816e-7*(10.0**(11.344*(1.0 - T_mask/373.16)) - 1.0) + 
                       8.1328e-3*(10.0**(-3.49149*(373.16/T_mask - 1.0)) - 1.0) + 
                       np.log10(1013.246))) * 100.0
      output[liquid_lt_2020_mask] = liquid_lt_2020

    return output

def polysvp1_dot_version(T, i_type):
    """
    Compute the saturation vapor pressure for an array of temperatures.

    Parameters:
    T (array-like): Array of temperatures in Kelvin.
    i_type (int): Saturation with respect to liquid (0) or ice (1).

    Returns:
    array-like: Array of saturation vapor pressures in Pa.
    """
    # Convert input to numpy array
    T = np.asarray(T)

    # Constants for ice
    a0i, a1i, a2i, a3i, a4i, a5i, a6i, a7i, a8i = (
        6.11147274, 0.503160820, 0.188439774e-1,
        0.420895665e-3, 0.615021634e-5, 0.602588177e-7,
        0.385852041e-9, 0.146898966e-11, 0.252751365e-14
    )

    # Constants for liquid
    a0, a1, a2, a3, a4, a5, a6, a7, a8 = (
        6.11239921, 0.443987641, 0.142986287e-1,
        0.264847430e-3, 0.302950461e-5, 0.206739458e-7,
        0.640689451e-10, -0.952447341e-13, -0.976195544e-15
    )

    # Precompute constants to avoid recalculating in loops
    log10_273_16 = np.log10(273.16)
    log10_373_16 = np.log10(373.16)

    # Initialize output array with the same shape as T
    output = np.zeros_like(T)

    # Ice conditions (i_type = 1 and T < 273.15)
    ice_mask = (i_type == 1) & (T < 273.15)
    ice_ge_1958_mask = ice_mask & (T >= 195.8)
    ice_lt_1958_mask = ice_mask & (T < 195.8)

    if np.any(ice_ge_1958_mask):
        dt_ice = T[ice_ge_1958_mask] - 273.15
        dt_ice_powers = np.array([dt_ice**i for i in range(9)])  # Precompute powers of dt_ice
        output[ice_ge_1958_mask] = np.dot([a0i, a1i, a2i, a3i, a4i, a5i, a6i, a7i, a8i], dt_ice_powers)
        output[ice_ge_1958_mask] *= 100.0

    if np.any(ice_lt_1958_mask):
        output[ice_lt_1958_mask] = (
            10.0**(
                -9.09718 * (273.16 / T[ice_lt_1958_mask] - 1.0) -
                3.56654 * (log10_273_16 - np.log10(T[ice_lt_1958_mask])) +
                0.876793 * (1.0 - T[ice_lt_1958_mask] / 273.16) +
                log10_273_16
            ) * 100.0
        )

    # Liquid conditions (i_type = 0 or T >= 273.15)
    liquid_mask = (i_type == 0) | (T >= 273.15)
    liquid_ge_2020_mask = liquid_mask & (T >= 202.0)
    liquid_lt_2020_mask = liquid_mask & (T < 202.0)

    if np.any(liquid_ge_2020_mask):
        dt_liquid = T[liquid_ge_2020_mask] - 273.15
        dt_liquid_powers = np.array([dt_liquid**i for i in range(9)])  # Precompute powers of dt_liquid
        output[liquid_ge_2020_mask] = np.dot([a0, a1, a2, a3, a4, a5, a6, a7, a8], dt_liquid_powers)
        output[liquid_ge_2020_mask] *= 100.0

    if np.any(liquid_lt_2020_mask):
        output[liquid_lt_2020_mask] = (
            10.0**(
                -7.90298 * (373.16 / T[liquid_lt_2020_mask] - 1.0) +
                5.02808 * (log10_373_16 - np.log10(T[liquid_lt_2020_mask])) -
                1.3816e-7 * (10.0**(11.344 * (1.0 - T[liquid_lt_2020_mask] / 373.16)) - 1.0) +
                8.1328e-3 * (10.0**(-3.49149 * (373.16 / T[liquid_lt_2020_mask] - 1.0)) - 1.0) +
                np.log10(1013.246)
            ) * 100.0
        )

    return output




