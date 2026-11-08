"""Exploratory squared-exponential time process with joint derivatives."""

from dataclasses import dataclass

import numpy as np


class StatisticsUncalibrated(ValueError):
    """Raised when a process is requested without sourced sigma/tau."""


def _grid(time_s: np.ndarray) -> np.ndarray:
    t = np.asarray(time_s, dtype=float)
    if t.ndim != 1 or len(t) < 2 or np.any(~np.isfinite(t)) or np.any(np.diff(t) <= 0):
        raise ValueError("time grid must be finite and strictly increasing")
    return t


def se_kernel(time_a: np.ndarray, time_b: np.ndarray, sigma_m: float, tau_s: float) -> np.ndarray:
    a = np.asarray(time_a, dtype=float)[:, None]
    b = np.asarray(time_b, dtype=float)[None, :]
    if not np.isfinite(sigma_m) or not np.isfinite(tau_s) or sigma_m < 0 or tau_s <= 0:
        raise ValueError("sigma must be nonnegative and tau positive")
    return sigma_m ** 2 * np.exp(-0.5 * ((a - b) / tau_s) ** 2)


def se_joint_covariance(time_s: np.ndarray, sigma_m: float, tau_s: float) -> np.ndarray:
    """Covariance of [e(t), e_dot(t)] for a stationary SE process."""
    t = _grid(time_s)
    delta = t[:, None] - t[None, :]
    k = se_kernel(t, t, sigma_m, tau_s)
    k_e_d = delta / (tau_s ** 2) * k
    k_d_e = -k_e_d
    k_d_d = (1.0 / tau_s ** 2 - delta ** 2 / tau_s ** 4) * k
    return np.block([[k, k_e_d], [k_d_e, k_d_d]])


@dataclass(frozen=True)
class SEProcess:
    sigma_m: float | None
    tau_s: float | None
    status: str = "STATISTICS_UNCALIBRATED"

    def validate(self) -> None:
        if self.status != "SUPPORTED" or self.sigma_m is None or self.tau_s is None:
            raise StatisticsUncalibrated("sigma/tau are not statistically calibrated")
        if not np.isfinite(self.sigma_m) or not np.isfinite(self.tau_s):
            raise StatisticsUncalibrated("sigma/tau must be finite")
        if self.sigma_m < 0 or self.tau_s <= 0:
            raise StatisticsUncalibrated("sigma must be nonnegative and tau positive")

    def sample(self, time_s: np.ndarray, seed: int) -> dict[str, np.ndarray]:
        self.validate()
        t = _grid(time_s)
        covariance = se_joint_covariance(t, float(self.sigma_m), float(self.tau_s))
        covariance = (covariance + covariance.T) * 0.5
        jitter = max(np.finfo(float).eps, np.max(np.diag(covariance)) * 1e-10)
        rng = np.random.default_rng(seed)
        try:
            chol = np.linalg.cholesky(covariance + jitter * np.eye(len(covariance)))
        except np.linalg.LinAlgError as exc:
            raise StatisticsUncalibrated("SE joint covariance is not positive definite") from exc
        draw = chol @ rng.standard_normal(len(covariance))
        n = len(t)
        return {
            "time_s": t.copy(),
            "error_m": draw[:n],
            "derivative_mps": draw[n:],
            "status": "exploratory",
            "joint_derivative": True,
        }


def sample_error_pair(time_s: np.ndarray, *, sigma_n_m: float | None,
                      tau_n_s: float | None, sigma_z_m: float | None,
                      tau_z_s: float | None, seed: int,
                      status_n: str = "STATISTICS_UNCALIBRATED",
                      status_z: str = "STATISTICS_UNCALIBRATED") -> dict[str, object]:
    n = SEProcess(sigma_n_m, tau_n_s, status_n).sample(time_s, seed)
    z = SEProcess(sigma_z_m, tau_z_s, status_z).sample(time_s, seed + 1)
    return {"N": n, "Z": z, "status": "exploratory"}
