#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "abstractMesh.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #  Author: James O'Beirne <james.obeirne@gmail.com>
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

__all__ = []

from fipy.tools import numerix
from fipy.meshes.mesh1D import Mesh1D
from fipy.meshes.mesh2D import Mesh2D
from fipy.meshes.mesh import Mesh
 
class _Gridlike(object):

    @staticmethod
    def __getstate__(grid):
        """
        Used internally to collect the necessary information to ``pickle`` the 
        `Grid2D` to persistent storage.
        """
        return grid.args

    @staticmethod
    def __setstate__(grid, dict):
        """
        Used internally to create a new `Grid2D` from ``pickled`` 
        persistent storage.
        """
        grid.__init__(**dict)

    @staticmethod
    def _isOrthogonal(grid):
        return True

    @staticmethod
    def repr_(grid, dns):
        dnstr = []
        for d, n in dns:
            dnstr.append(d + "=" + str(grid.args[d]))
            if grid.args[n] is not None:
                dnstr.append(n + "=" + str(grid.args[n]))

        return "%s(%s)" % (grid.__class__.__name__, ", ".join(dnstr))
                               
class _Gridlike1D(_Gridlike):

    @staticmethod
    def __repr__(grid):
        return _Gridlike.repr_(grid, [("dx", "nx")])

    _concatenatedClass = Mesh1D
                                                            
    @staticmethod
    def _globalNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Does not include the IDs of boundary cells.

        E.g., would return [0, 1] for mesh A

            A        B
        ------------------
        | 0 | 1 || 2 | 3 |
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """

        return numerix.arange(grid.offset + grid.overlap['left'], 
                              grid.offset + grid.nx - grid.overlap['right'])

    @staticmethod
    def _globalOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2] for mesh A

            A        B
        ------------------
        | 0 | 1 || 2 | 3 |
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.offset, grid.offset + grid.nx)

    @staticmethod
    def _localNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Does not include the IDs of boundary cells.
        
        E.g., would return [0, 1] for mesh A

            A        B
        ------------------
        | 0 | 1 || 1 | 2 |
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.overlap['left'], 
                              grid.nx - grid.overlap['right'])

    @staticmethod
    def _localOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2] for mesh A

            A        B
        ------------------
        | 0 | 1 || 2 |   |
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(0, grid.nx)

    @staticmethod
    def _globalNonOverlappingFaceIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Does not include the IDs of boundary cells.

        E.g., would return [0, 1, 2] for mesh A

            A    ||   B
        ------------------
        0   1    2   3   4
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.offset + grid.overlap['left'], 
                              grid.offset + grid.numberOfFaces - grid.overlap['right'])

    @staticmethod
    def _globalOverlappingFaceIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2, 3] for mesh A

            A    ||   B
        ------------------
        0   1    2   3   4
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.offset, grid.offset + grid.numberOfFaces)

    @staticmethod
    def _localNonOverlappingFaceIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Does not include the IDs of boundary cells.
        
        E.g., would return [0, 1, 2] for mesh A

            A    ||   B
        ------------------
        0   1   2/1  2   3
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.overlap['left'], 
                              grid.numberOfFaces - grid.overlap['right'])

    @staticmethod
    def _localOverlappingFaceIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2, 3] for mesh A

            A   ||   B
        ------------------
        0   1   2   3    |
        ------------------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(0, grid.numberOfFaces)
     
class _Gridlike2D(_Gridlike):

    @staticmethod
    def __repr__(grid):
        return _Gridlike.repr_(grid, [("dx", "nx"), ("dy", "ny")])
             
    _concatenatedClass = Mesh2D
     
    @staticmethod
    def _globalNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Does not include the IDs of boundary cells.

        E.g., would return [0, 1] for mesh A

        ---------
        | 4 | 5 |     
        ---------  B
        | 2 | 3 |     
        =========
        | 0 | 1 |  A
        ---------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange((grid.offset[1] + grid.overlap['bottom']) * grid.nx, 
                              (grid.offset[1] + grid.ny - grid.overlap['top']) * grid.nx)

    @staticmethod
    def _globalOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2, 3] for mesh A

        ---------
        | 4 | 5 |     
        ---------  B
        | 2 | 3 |     
        =========
        | 0 | 1 |  A
        ---------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.offset[1] * grid.nx, (grid.offset[1] + grid.ny) * grid.nx)

    @staticmethod
    def _localNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Does not include the IDs of boundary cells.
        
        E.g., would return [0, 1] for mesh A

        ---------
        | 4 | 5 |     
        ---------  B
        | 2 | 3 |     
        =========
        | 0 | 1 |  A
        ---------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.overlap['bottom'] * grid.nx, 
                              (grid.ny - grid.overlap['top']) * grid.nx)

    @staticmethod
    def _localOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Includes the IDs of boundary cells.
        
        E.g., would return [0, 1, 2, 3] for mesh A

        ---------
        |   |   |     
        ---------  B
        | 2 | 3 |     
        =========
        | 0 | 1 |  A
        ---------
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(0, grid.ny * grid.nx)

class _Gridlike3D(_Gridlike):
 
    @staticmethod
    def __repr__(grid):
        return _Gridlike.repr_(grid, [("dx", "nx"), ("dy", "ny"), ("dz", "nz")])
 
    _concatenatedClass = Mesh
     
    @staticmethod
    def _globalNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Does not include the IDs of boundary cells.
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange((grid.offset[2] + grid.overlap['front']) * grid.nx * grid.ny, 
                              (grid.offset[2] + grid.nz - grid.overlap['back']) * grid.nx * grid.ny)

    @staticmethod
    def _globalOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in the context of the
        global parallel mesh. Includes the IDs of boundary cells.
        
        .. note:: Trivial except for parallel meshes
        """
        
        return numerix.arange(grid.offset[2] * grid.nx * grid.ny, 
                              (grid.offset[2] + grid.nz) * grid.nx * grid.ny)

    @staticmethod
    def _localNonOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Does not include the IDs of boundary cells.
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(grid.overlap['front'] * grid.nx * grid.ny, 
                              (grid.nz - grid.overlap['back']) * grid.nx * grid.ny)

    @staticmethod
    def _localOverlappingCellIDs(grid):
        """
        Return the IDs of the local mesh in isolation. 
        Includes the IDs of boundary cells.
        
        .. note:: Trivial except for parallel meshes
        """
        return numerix.arange(0, grid.ny * grid.nx * grid.nz)
     
