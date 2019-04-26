"""

Input file for chemotaxis modeling.

Here are some test cases for the model.

    >>> for i in range(28):
    ...     for var, eqn in eqs:
    ...         var.updateOld()
    ...     for var, eqn in eqs:
    ...         eqn.solve(var, dt = 1.0)

    >>> accuracy = 1e-2
    >>> print(KMVar.allclose(params['KM'], atol = accuracy))
    1
    >>> print(TMVar.allclose(params['TM'], atol = accuracy))
    1
    >>> print(TCVar.allclose(params['TC'], atol = accuracy))
    1
    >>> print(P2Var.allclose(params['P2'], atol = accuracy))
    1
    >>> print(P3Var.allclose(params['P3'], atol = accuracy))
    1
    >>> print(KCVar.allclose(params['KC'], atol = accuracy))
    1

"""
from __future__ import division

from past.utils import old_div
from examples.chemotaxis.parameters import parameters

from fipy import CellVariable, Grid1D, TransientTerm, DiffusionTerm, ImplicitSourceTerm, Viewer

params = parameters['case 2']

nx = 50
dx = 1.
L = nx * dx

mesh = Grid1D(nx = nx, dx = dx)

shift = 1.

KMVar = CellVariable(mesh = mesh, value = params['KM'] * shift, hasOld = 1)
KCVar = CellVariable(mesh = mesh, value = params['KC'] * shift, hasOld = 1)
TMVar = CellVariable(mesh = mesh, value = params['TM'] * shift, hasOld = 1)
TCVar = CellVariable(mesh = mesh, value = params['TC'] * shift, hasOld = 1)
P3Var = CellVariable(mesh = mesh, value = params['P3'] * shift, hasOld = 1)
P2Var = CellVariable(mesh = mesh, value = params['P2'] * shift, hasOld = 1)
RVar = CellVariable(mesh = mesh, value = params['R'], hasOld = 1)

PN = P3Var + P2Var

KMscCoeff = params['chiK'] * (RVar + 1) * (1 - KCVar - KMVar.cellVolumeAverage)
KMspCoeff = old_div(params['lambdaK'], (1 + old_div(PN, params['kappaK'])))
KMEq = TransientTerm() - KMscCoeff + ImplicitSourceTerm(KMspCoeff)

TMscCoeff = params['chiT'] * (1 - TCVar - TMVar.cellVolumeAverage)
TMspCoeff = params['lambdaT'] * (KMVar + params['zetaT'])
TMEq = TransientTerm() - TMscCoeff + ImplicitSourceTerm(TMspCoeff)

TCscCoeff = params['lambdaT'] * (TMVar * KMVar).cellVolumeAverage
TCspCoeff = params['lambdaTstar']
TCEq = TransientTerm() - TCscCoeff + ImplicitSourceTerm(TCspCoeff)

PIP2PITP = old_div(PN, (old_div(PN, params['kappam']) + old_div(PN.cellVolumeAverage, params['kappac']) + 1)) + params['zetaPITP']

P3spCoeff = params['lambda3'] * (TMVar + params['zeta3T'])
P3scCoeff = params['chi3'] * KMVar * (old_div(PIP2PITP, (1 + old_div(KMVar, params['kappa3']))) + params['zeta3PITP']) + params['zeta3']
P3Eq = TransientTerm() - DiffusionTerm(params['diffusionCoeff']) - P3scCoeff + ImplicitSourceTerm(P3spCoeff)

P2scCoeff = scCoeff = params['chi2'] + params['lambda3'] * params['zeta3T'] * P3Var
P2spCoeff = params['lambda2'] * (TMVar + params['zeta2T'])
P2Eq = TransientTerm() - DiffusionTerm(params['diffusionCoeff']) - P2scCoeff + ImplicitSourceTerm(P2spCoeff)

KCscCoeff = params['alphaKstar'] * params['lambdaK'] * (old_div(KMVar, (1 + old_div(PN, params['kappaK'])))).cellVolumeAverage
KCspCoeff = old_div(params['lambdaKstar'], (params['kappaKstar'] + KCVar))
KCEq = TransientTerm() - KCscCoeff + ImplicitSourceTerm(KCspCoeff)

eqs = ((KMVar, KMEq), (TMVar, TMEq), (TCVar, TCEq), (P3Var, P3Eq), (P2Var, P2Eq), (KCVar, KCEq))

if __name__ == '__main__':

    v1 = old_div(KMVar, KMVar.cellVolumeAverage)
    v2 = old_div(PN, PN.cellVolumeAverage)
    v3 = old_div(TMVar, TMVar.cellVolumeAverage)
    v1.setName('KM')
    v2.setName('PN')
    v3.setName('TM')

    KMViewer = Viewer((v1, v2, v3), title = 'Gradient Stimulus: Profile')

    KMViewer.plot()

    for i in range(100):
        for var, eqn in eqs:
            var.updateOld()
        for var, eqn in eqs:
            eqn.solve(var, dt = 1.)

    RVar[:] = params['S'] + (1 + params['S']) * params['G'] * cos(old_div((2 * pi * mesh.cellCenters[0]), L))

    for i in range(100):
        for var, eqn in eqs:
            var.updateOld()
        for var, eqn in eqs:
            eqn.solve(var, dt = 0.1)
        KMViewer.plot()

    KMViewer.plot()

    input("finished")

