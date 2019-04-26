from __future__ import division
from builtins import range
from past.utils import old_div
__docformat__ = 'restructuredtext'

from fipy.tools import numerix
from fipy.tools.numerix import random
from fipy.tools.dimensions.physicalField import PhysicalField

from fipy.meshes.mesh2D import Mesh2D
from fipy.meshes import Grid2D

__all__ = ["SkewedGrid2D"]

class SkewedGrid2D(Mesh2D):
    """
    Creates a 2D grid mesh with horizontal faces numbered first and then
    vertical faces.  The points are skewed by a random amount (between `rand`
    and `-rand`) in the X and Y directions.
    """
    def __init__(self, dx = 1., dy = 1., nx = None, ny = 1, rand = 0, *args, **kwargs):
        self.args = {
            'dx': dx,
            'dy': dy,
            'nx': nx,
            'ny': ny,
            'rand': rand
        }

        self.nx = nx
        self.ny = ny

        self.dx = PhysicalField(value = dx)
        scale = PhysicalField(value = 1, unit = self.dx.unit)
        self.dx /= scale

        self.dy = PhysicalField(value = dy)
        if self.dy.unit.isDimensionless():
            self.dy = dy
        else:
            self.dy /= scale

        self.grid = Grid2D(nx=nx, ny=ny, dx=dx, dy=dy)

        self.numberOfVertices = self.grid._numberOfVertices

        vertices = self.grid.vertexCoords

        changedVertices = numerix.zeros(vertices.shape, 'd')

        for i in range(len(vertices[0])):
            if((i % (nx+1)) != 0 and (i % (nx+1)) != nx and (old_div(i, nx)+1) != 0 and (old_div(i, nx)+1) != ny):
                changedVertices[0, i] = vertices[0, i] + (rand * ((random.random() * 2) - 1))
                changedVertices[1, i] = vertices[1, i] + (rand * ((random.random() * 2) - 1))
            else:
                changedVertices[0, i] = vertices[0, i]
                changedVertices[1, i] = vertices[1, i]


        faces = self.grid.faceVertexIDs

        cells = self.grid.cellFaceIDs

        Mesh2D.__init__(self, changedVertices, faces, cells, *args, **kwargs)

        self.scale = scale

    @property
    def physicalShape(self):
        """Return physical dimensions of Grid2D.
        """
        return PhysicalField(value = (self.nx * self.dx * self.scale, self.ny * self.dy * self.scale))

    @property
    def _meshSpacing(self):
        return numerix.array((self.dx, self.dy))[..., numerix.newaxis]

    @property
    def shape(self):
        return (self.nx, self.ny)
