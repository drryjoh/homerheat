"""Moist-air density from the ideal gas law + Dalton's law of partial pressures.

rho = (p_d * M_d + p_v * M_v) / (R * T),  with p_v = RH * e_s(T), p_d = P - p_v.
Because M_v (18.015 g/mol) < M_d (28.965 g/mol), swapping dry-air molecules for
water molecules at fixed T and P lowers the density.
(Fallback used only if src/air.py is not available.)
"""
import numpy as np

R = 8.314462618        # J/(mol K)
M_D = 0.028965         # kg/mol, dry air
M_V = 0.018015         # kg/mol, water vapor
P0 = 101325.0          # Pa, sea-level standard pressure


def f_to_k(t_f):
    return (np.asarray(t_f, float) - 32.0) * 5.0 / 9.0 + 273.15


def sat_vapor_pressure(t_k):
    """Saturation vapor pressure over water [Pa], Magnus/Bolton (1980) form."""
    t_c = np.asarray(t_k, float) - 273.15
    return 611.2 * np.exp(17.67 * t_c / (t_c + 243.5))


def pressure_at_altitude(h_m):
    """ISA barometric pressure [Pa] at altitude h [m] (troposphere)."""
    return P0 * (1.0 - 2.25577e-5 * np.asarray(h_m, float)) ** 5.25588


def air_density(t_f, rh, p_pa=P0):
    """Moist-air density [kg/m^3]. t_f in deg F, rh in 0..1, p in Pa."""
    t_k = f_to_k(t_f)
    p_v = np.asarray(rh, float) * sat_vapor_pressure(t_k)
    p_d = p_pa - p_v
    return (p_d * M_D + p_v * M_V) / (R * t_k)


if __name__ == "__main__":
    print("Air density at sea level (kg/m^3) and % change dry -> saturated")
    for t in (60, 75, 90):
        r0, r1 = air_density(t, 0.0), air_density(t, 1.0)
        print(f"  {t:>3} F: RH0 {r0:.4f}  RH100 {r1:.4f}  change {100*(r1/r0-1):+.2f}%")
    r60, r90 = air_density(60, 0.5), air_density(90, 0.5)
    print(f"  60->90 F at 50% RH: {100*(r90/r60-1):+.2f}%")
    rden = air_density(75, 0.5, pressure_at_altitude(1600))
    print(f"  Denver (1600 m) vs sea level, 75 F 50% RH: {100*(rden/air_density(75, 0.5)-1):+.2f}%")
