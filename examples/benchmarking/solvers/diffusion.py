import argparse
import json
import os
import uuid

import fipy as fp
from fipy.tools import numerix
from fipy.tools import parallelComm

parser = argparse.ArgumentParser()
parser.add_argument("--output", help="directory to store results in",
                    default=None)
parser.add_argument("--numberOfElements", help="number of total cells in a Grid2D",
                    type=int, default=10000)
parser.add_argument("--solver", help="solver class to use",
                    choices=("cg", "pcg", "cgs", "gmres", "lu"), default="cg")
parser.add_argument("--preconditioner", help="preconditioner class to use",
                    choices=("jacobi", "ilu", "ssor", "icc", "none"), default="none")
parser.add_argument("--sweeps", help="number of nonlinear sweeps to take",
                    type=int, default=10)
parser.add_argument("--iterations", help="maximum number of linear iterations to take for each sweep",
                    type=int, default=1000)
parser.add_argument("--tolerance", help="linear solver tolerance",
                    type=float, default=1e-10)
parser.add_argument("--left", help="value of left-hand Dirichlet condition",
                    type=float, default=1.)
parser.add_argument("--right", help="value of right-hand Dirichlet condition",
                    type=float, default=0.)

args, unknowns = parser.parse_known_args()

N = int(numerix.sqrt(args.numberOfElements))
mesh = fp.Grid2D(nx=N, Lx=1., ny=N, Ly=1.)

var = fp.CellVariable(mesh=mesh, value=1., hasOld=True)
var.constrain(args.left, where=mesh.facesLeft)
var.constrain(args.right, where=mesh.facesRight)

eq = fp.TransientTerm() == fp.DiffusionTerm(coeff=var.harmonicFaceValue)

precon = None

if args.preconditioner == "jacobi":
    precon = fp.JacobiPreconditioner()
elif args.preconditioner == "ilu":
    precon = fp.ILUPreconditioner()
elif args.preconditioner == "ssor":
    precon = fp.SSORPreconditioner
elif args.preconditioner == "icc":
    precon = fp.ICPreconditioner
elif args.preconditioner == "none":
    precon = None

if args.solver == "cgs":
    solver_class = fp.LinearCGSSolver
elif args.solver == "gmres":
    solver_class = fp.LinearGMRESSolver
elif args.solver == "lu":
    if args.preconditioner != "none":
        # preconditioned lu doesn't make any sense
        exit()

    solver_class = fp.LinearLUSolver
elif args.solver == "pcg":
    solver_class = fp.LinearPCGSolver

with solver_class(tolerance=args.tolerance, criterion="initial",
                  iterations=args.iterations, precon=precon) as solver:

    if (args.output is not None) and (parallelComm.procID == 0):
        suite = solver.__module__.split('.')[2]
        if args.preconditioner is None:
            preconditioner_name = "none"
        else:
            preconditioner_name = precon.__class__.__name__
        path = os.path.join(args.output, suite,
                            solver.__class__.__name__,
                            preconditioner_name,
                            str(N**2))

        os.makedirs(path)

    state = dict(state="START", numberOfElements=N**2, sweeps=args.sweeps)
    if precon is None:
        state["preconditioner"] = None
    else:
        state["preconditioner"] = precon.__class__.__name__

    solver._log.debug(json.dumps(state))

    for sweep in range(args.sweeps):
        eq.cacheMatrix()
        eq.cacheRHSvector()
        res = eq.sweep(var=var, dt=1., solver=solver)

    state["state"] = "END"
    solver._log.debug(json.dumps(state))

    if (args.output is not None) and (parallelComm.procID == 0):
        filename = os.path.join(path, "solution.npz")
        x, y, value = [field.reshape((mesh.nx, mesh.ny))
                       for field in mesh.x, mesh.y, var.value]
        numerix.savez(filename, x=mesh.x, y=mesh.y, value=value)
