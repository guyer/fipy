from __future__ import unicode_literals
from fipy.solvers.pyamgx import PyAMGXSolver
from fipy.solvers.pyamgx.smoothers import BlockJacobiSmoother

__all__ = ["ClassicalAMGSolver"]
from future.utils import text_to_native_str
__all__ = [text_to_native_str(n) for n in __all__]

class ClassicalAMGSolver(PyAMGXSolver):
    """
    The `ClassicalAMGSolver` is an interface to the classical AMG solver in
    AMGX, with a Jacobi smoother by default.
    """

    CONFIG_DICT = {
        "config_version": 2,
        "determinism_flag": 1,
        "solver": {
            "algorithm": "CLASSICAL",
            "solver": "AMG",
            "monitor_residual": 1,
            "max_levels": 1000,
        }
    }

    DEFAULT_SMOOTHER = BlockJacobiSmoother
