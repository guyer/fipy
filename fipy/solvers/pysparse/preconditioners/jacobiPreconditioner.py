from __future__ import unicode_literals
from pysparse.precon import precon

from fipy.solvers.pysparse.preconditioners.pysparsePreconditioner import PysparsePreconditioner

__all__ = ["JacobiPreconditioner"]
from future.utils import text_to_native_str
__all__ = [text_to_native_str(n) for n in __all__]

class JacobiPreconditioner(PysparsePreconditioner):
    """Jacobi preconditioner for :class:`~fipy.solvers.pysparse.pysparseSolver.PysparseSolver`.

    Wrapper class for :func:`pysparse.precon.jacobi`.
    """

    def _applyToMatrix(self, matrix):
        return precon.jacobi(matrix), matrix.to_csr()
