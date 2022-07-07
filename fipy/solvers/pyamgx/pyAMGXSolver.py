from __future__ import unicode_literals
import numpy
from scipy.sparse import csr_matrix

import pyamgx

from fipy.solvers.solver import Solver
from fipy.matrices.scipyMatrix import _ScipyMeshMatrix
from fipy.tools import numerix

__all__ = ["PyAMGXSolver"]
from future.utils import text_to_native_str
__all__ = [text_to_native_str(n) for n in __all__]

class PyAMGXSolver(Solver):

    def __init__(self, config_dict, tolerance=1e-10, criterion="default",
                 iterations=2000, precon=None, smoother=None, **kwargs):
        """
        Parameters
        ----------
        config_dict : dict
            AMGX configuration options
        tolerance : float
            Required error tolerance.
        criterion : {'default', 'unscaled', 'RHS', 'matrix', 'initial'}
            Interpretation of ``tolerance``.
            See :ref:`CONVERGENCE` for more information.
        iterations : int
            Maximum number of iterative steps to perform.
        precon : ~fipy.solvers.pyamgx.preconditioners.preconditioners.Preconditioner, optional
        smoother : ~fipy.solvers.pyamgx.smoothers.smoothers.Smoother, optional
        **kwargs
            Other AMGX solver options
        """
        # update solver config:
        self.config_dict = config_dict.copy()

        self.config_dict["solver"]["max_iters"] = iterations
        if precon is not None:
            self.config_dict["solver"]["preconditioner"] = precon
        if smoother is not None:
            self.config_dict["solver"]["smoother"] = smoother
        self.config_dict["solver"].update(kwargs)

        # create AMGX objects:
        self.cfg = pyamgx.Config().create_from_dict(self.config_dict)
        self.resources = pyamgx.Resources().create_simple(self.cfg)
        self.x_gpu = pyamgx.Vector().create(self.resources)
        self.b_gpu = pyamgx.Vector().create(self.resources)
        self.A_gpu = pyamgx.Matrix().create(self.resources)

        super(PyAMGXSolver, self).__init__(tolerance=tolerance, criterion=criterion, iterations=iterations)

    def __exit__(self, *args):
        # destroy AMGX objects:
        self.A_gpu.destroy()
        self.b_gpu.destroy()
        self.x_gpu.destroy()
        self.resources.destroy()
        self.cfg.destroy()

    @property
    def _matrixClass(self):
        return _ScipyMeshMatrix

    def _storeMatrix(self, var, matrix, RHSvector):
        self.var = var
        self.matrix = matrix
        self.RHSvector = RHSvector
        self.A_gpu.upload_CSR(self.matrix.matrix)
        self.solver.setup(self.A_gpu)

    def _adaptDefaultTolerance(self, L, x, b):
        return self._adaptInitialTolerance(L, x, b)

    def _adaptUnscaledTolerance(self, L, x, b):
        return (1., "ABSOLUTE")

    def _adaptRHSTolerance(self, L, x, b):
        return (self.rhsNorm(L, x, b), "ABSOLUTE")

    def _adaptMatrixTolerance(self, L, x, b):
        return (self.matrixNorm(L, x, b), "ABSOLUTE")

    def _adaptInitialTolerance(self, L, x, b):
        return (1., "RELATIVE_INI_CORE")

    def _solve_(self, L, x, b):
        # transfer data from CPU to GPU
        self.x_gpu.upload(x)
        self.b_gpu.upload(b)

        tolerance_factor, suite_criterion = self._adaptTolerance(L, x, b)
        config_dict = self.config_dict.copy()
        config_dict["solver"]["tolerance"] = self.tolerance * tolerance_factor
        config_dict["solver"]["convergence"] = suite_criterion

        cfg = pyamgx.Config().create_from_dict(config_dict)
        solver = pyamgx.Solver().create(self.resources, cfg)

        # solve system on GPU
        self.solver.solve(self.b_gpu, self.x_gpu)

        # download values from GPU to CPU
        self.x_gpu.download(x)

        self._setConvergence(suite="pyamgx",
                             code=self.solver.status,
                             iterations=self.solver.iterations_number,
                             residual=(self.solver.get_residual()
                                       / tolerance_factor))

        self.convergence.warn()

        solver.destroy()
        cfg.destroy()

        return x

    def _solve(self):
         if self.var.mesh.communicator.Nproc > 1:
             raise Exception("SciPy solvers cannot be used with multiple processors")

         self.var[:] = numerix.reshape(self._solve_(self.matrix, self.var.ravel(), numerix.array(self.RHSvector)), self.var.shape)
