"""Small WGS84 geodetic conversion used only by the clean-room package."""

import math

import numpy as np


WGS84_A_M = 6378137.0
WGS84_F = 1.0 / 298.257223563


def dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_geodetic(latitude_deg: float, longitude_deg: float, height_m: float = 0.0) -> np.ndarray:
    lat = math.radians(latitude_deg)
    lon = math.radians(longitude_deg)
    e2 = WGS84_F * (2.0 - WGS84_F)
    n = WGS84_A_M / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    return np.array([
        (n + height_m) * math.cos(lat) * math.cos(lon),
        (n + height_m) * math.cos(lat) * math.sin(lon),
        (n * (1.0 - e2) + height_m) * math.sin(lat),
    ])


class ENUFrame:
    """Local WGS84 ENU frame with explicit origin and source status."""

    def __init__(self, latitude_deg: float, longitude_deg: float, height_m: float):
        self.latitude_deg = float(latitude_deg)
        self.longitude_deg = float(longitude_deg)
        self.height_m = float(height_m)
        lat = math.radians(self.latitude_deg)
        lon = math.radians(self.longitude_deg)
        self.origin_ecef = ecef_from_geodetic(self.latitude_deg, self.longitude_deg, self.height_m)
        self.rotation = np.array([
            [-math.sin(lon), math.cos(lon), 0.0],
            [-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat)],
            [math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)],
        ])

    def to_enu(self, latitude_deg: float, longitude_deg: float, height_m: float = 0.0) -> np.ndarray:
        return self.rotation @ (ecef_from_geodetic(latitude_deg, longitude_deg, height_m) - self.origin_ecef)


def parse_dms(value: dict[str, float | int]) -> tuple[float, float]:
    return (
        dms_to_decimal(int(value["lat_deg"]), int(value["lat_min"]), float(value["lat_sec"])),
        dms_to_decimal(int(value["lon_deg"]), int(value["lon_min"]), float(value["lon_sec"])),
    )
