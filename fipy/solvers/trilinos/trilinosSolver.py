#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 #
 #  FILE: "trilinosSolver.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #  Author: Maxsim Gibiansky <maxsim.gibiansky@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 #
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

from PyTrilinos import Epetra
from PyTrilinos import EpetraExt

from fipy.solvers.solver import Solver
from fipy.tools import numerix

class TrilinosSolver(Solver):

    """
    .. attention:: This class is abstract. Always create one of its subclasses.

    """
    def __init__(self, *args, **kwargs):
        if self.__class__ is TrilinosSolver:
            raise NotImplementedError, "can't instantiate abstract base class"
        else:
            Solver.__init__(self, *args, **kwargs)

        self._reset()

    def _storeMatrix(self, var, matrix, RHSvector):
        self.var = var
        if hasattr(self, 'matrix'):
            self.matrix.matrix = matrix.matrix
        else:
            self.matrix = matrix
        self.RHSvector = RHSvector

    def _reset(self):
        """Mark solver and matrix as needing to be rebuilt
        """
        self._dirty = True

    @property
    def _globalMatrixAndVectors(self):
        if not hasattr(self, 'globalVectors'):
            self._globalMatrix = self.matrix._getTrilinosMatrix()
            self._nonOverlappingVector = Epetra.Vector(self._globalMatrix.domainMap)
            self._nonOverlappingRHSvector = Epetra.Vector(self._globalMatrix.rangeMap)
            self._overlappingVector = Epetra.Vector(self._globalMatrix.colMap)

            self.globalVectors = (self._globalMatrix,
                                  self._nonOverlappingVector,
                                  self._nonOverlappingRHSvector,
                                  self._overlappingVector)

        if self._dirty:
            self.matrix.asTrilinosMeshMatrix(trilinosMatrix=self._globalMatrix)

            mesh = self.var.mesh
            localNonOverlappingCellIDs = mesh._localNonOverlappingCellIDs
            localOverlappingCellIDs = mesh._localOverlappingCellIDs

            ## The following conditional is required because empty indexing is
            ## not altogether functional.
            ## numpy.empty((0,))[[]] and
            ## numpy.empty((0,))[...,[]] both work, but
            ## numpy.empty((3, 0))[...,[]] is broken.
            if self.var.shape[-1] != 0:
                s = (Ellipsis, localNonOverlappingCellIDs)
            else:
                s = (localNonOverlappingCellIDs,)

            from fipy.variables.coupledCellVariable import _CoupledCellVariable
            if isinstance(self.var, _CoupledCellVariable):
                dim = len(self.var.vars)
            else:
                dim = numerix.prod(self.var.elementshape, dtype=int)
            offsets = numerix.arange(dim)[..., numerix.newaxis] * mesh.numberOfCells
            stackNonOverlappingCellIDs = numerix.stack([localNonOverlappingCellIDs] * dim) + offsets
            stackNonOverlappingCellIDs = stackNonOverlappingCellIDs.astype('int32')
            stackOverlappingCellIDs = numerix.stack([localOverlappingCellIDs] * dim) + offsets
            stackOverlappingCellIDs = stackOverlappingCellIDs.astype('int32')

            self._nonOverlappingVector.ReplaceMyValues(self.var[s].ravel(),
                                                       stackNonOverlappingCellIDs.flat)

            if isinstance(self.RHSvector, _CoupledCellVariable):
                RHSvector = self.RHSvector[localNonOverlappingCellIDs]
            else:
                RHSvector = numerix.reshape(numerix.array(self.RHSvector),
                                            self.var.shape)[s].ravel()

            self._nonOverlappingRHSvector.ReplaceMyValues(RHSvector,
                                                          stackNonOverlappingCellIDs.flat)

            del RHSvector

            self._overlappingVector.ReplaceMyValues(self.var.ravel(),
                                                    stackOverlappingCellIDs.flat)

            self._dirty = False

        return self.globalVectors

    def _deleteGlobalMatrixAndVectors(self):
        self.matrix.flush()
        del self.globalVectors

    def _solve(self):
        from fipy.terms import SolutionVariableNumberError

        (globalMatrix,
         nonOverlappingVector,
         nonOverlappingRHSvector,
         overlappingVector) = self._globalMatrixAndVectors

        if not (globalMatrix.rangeMap.SameAs(globalMatrix.domainMap)
                and globalMatrix.rangeMap.SameAs(nonOverlappingVector.Map())):

            raise SolutionVariableNumberError

        self._solve_(globalMatrix.matrix,
                     nonOverlappingVector,
                     nonOverlappingRHSvector)

        overlappingVector.Import(nonOverlappingVector,
                                 Epetra.Import(globalMatrix.colMap,
                                               globalMatrix.domainMap),
                                 Epetra.Insert)

        self.var.value = numerix.reshape(numerix.array(overlappingVector), self.var.shape)

#         self._deleteGlobalMatrixAndVectors()
#         del self.var
#         del self.RHSvector

    @property
    def _matrixClass(self):
        from fipy.solvers import _MeshMatrix
        return _MeshMatrix

    def _calcResidualVector(self, residualFn=None):
        if residualFn is not None:
            return residualFn(self.var, self.matrix, self.RHSvector)
        else:
	    residual, globalMatrix = self._calcResidualVectorNonOverlapping_()

            overlappingResidual = Epetra.Vector(globalMatrix.colMap)
            overlappingResidual.Import(residual,
				       Epetra.Import(globalMatrix.colMap,
						     globalMatrix.domainMap),
				       Epetra.Insert)

            return overlappingResidual

    def _calcResidualVectorNonOverlapping_(self):
	globalMatrix, nonOverlappingVector, nonOverlappingRHSvector, overlappingVector = self._globalMatrixAndVectors
	# If A is an Epetra.Vector with map M
	# and B is an Epetra.Vector with map M
        # and C = A - B
        # then C is an Epetra.Vector with *no map* !!!?!?!
	residual = globalMatrix * nonOverlappingVector
	residual -= nonOverlappingRHSvector
	return residual, globalMatrix

    def _calcResidual(self, residualFn=None):
        if residualFn is not None:
            return residualFn(self.var, self.matrix, self.RHSvector)
        else:
            comm = self.var.mesh.communicator
	    residual, globalMatrix = self._calcResidualVectorNonOverlapping_()
            return comm.Norm2(residual)

    def _calcRHSNorm(self):
        return self.nonOverlappingRHSvector.Norm2()
