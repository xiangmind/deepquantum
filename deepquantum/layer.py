"""
Quantum layers
"""

from copy import deepcopy
from typing import List, Union

import torch
from torch import nn

from .operation import Layer
from .gate import PauliX, PauliY, PauliZ, U3Gate, Hadamard, Rx, Ry, Rz, CNOT
from .qmath import multi_kron


class SingleLayer(Layer):
    """A base class for layers of single-qubit gates."""
    def __init__(self, name=None, nqubit=1, wires=None, den_mat=False, tsr_mode=False):
        if wires is None:
            wires = [[i] for i in range(nqubit)]
        super().__init__(name=name, nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            assert len(wire) == 1

    def get_unitary(self):
        assert len(self.gates) > 0, 'There is no quantum gate'
        identity = torch.eye(2, dtype=torch.cfloat, device=self.gates[0].matrix.device)
        lst = [identity] * self.nqubit
        for gate in self.gates:
            lst[gate.wires[0]] = gate.update_matrix()
        return multi_kron(lst)


class DoubleLayer(Layer):
    """A base class for layers of two-qubit gates."""
    def __init__(self, name=None, nqubit=2, wires=None, den_mat=False, tsr_mode=False):
        if wires is None:
            wires = [[i, i + 1] for i in range(0, nqubit - 1, 2)]
        super().__init__(name=name, nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            assert len(wire) == 2


class Observable(SingleLayer):
    """A `Layer` that represents an observable which can be expressed by Pauli string.

    Args:
        nqubit (int, optional): The number of qubits in the quantum circuit. Default: 1
        wires (int, List[int] or None, optional): The wires to measure. Default: ``None`` (which means all 
            wires are measured)
        basis (str, optional): The measurement basis for each wire. It can be 'x', 'y', or 'z'. If only one
            character is given, it is repeated for all wires. Default: ``'z'``
        den_mat (bool, optional): Whether to use density matrix representation. Default: ``False``
        tsr_mode (bool, optional): Whether the input and output are represented by a tensor of
            shape (batch, 2, ..., 2). Default: ``False``
    """
    def __init__(
        self,
        nqubit: int = 1,
        wires: Union[int, List[int], None] = None,
        basis: str = 'z',
        den_mat: bool = False,
        tsr_mode: bool = False
    ) -> None:
        super().__init__(name='Observable', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        basis = basis.lower()
        if len(basis) == 1:
            self.basis = basis * len(self.wires)
        else:
            self.basis = basis
        assert len(self.wires) == len(self.basis), 'The number of wires is not equal to the number of bases'
        for i, wire in enumerate(self.wires):
            if self.basis[i] == 'x':
                gate = PauliX(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            elif self.basis[i] == 'y':
                gate = PauliY(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            elif self.basis[i] == 'z':
                gate = PauliZ(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            else:
                raise ValueError('Use illegal measurement basis')
            self.gates.append(gate)


class U3Layer(SingleLayer):
    """A layer of U3 gates."""
    def __init__(self, nqubit=1, wires=None, inputs=None, den_mat=False, tsr_mode=False, requires_grad=True):
        super().__init__(name='U3Layer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for i, wire in enumerate(self.wires):
            if inputs is None:
                thetas = None
            else:
                thetas = inputs[3*i:3*i+3]
            u3 = U3Gate(inputs=thetas, nqubit=nqubit, wires=wire, den_mat=den_mat,
                        tsr_mode=True, requires_grad=requires_grad)
            self.gates.append(u3)
            self.npara += u3.npara

    def inverse(self):
        layer = deepcopy(self)
        gates = nn.Sequential()
        for gate in self.gates[::-1]:
            gates.append(gate.inverse())
        layer.gates = gates
        layer.wires = self.wires[::-1]
        return layer


class XLayer(SingleLayer):
    """A layer of Pauli-X gates."""
    def __init__(self, nqubit=1, wires=None, den_mat=False, tsr_mode=False):
        super().__init__(name='XLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            x = PauliX(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            self.gates.append(x)


class YLayer(SingleLayer):
    """A layer of Pauli-Y gates."""
    def __init__(self, nqubit=1, wires=None, den_mat=False, tsr_mode=False):
        super().__init__(name='YLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            y = PauliY(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            self.gates.append(y)


class ZLayer(SingleLayer):
    """A layer of Pauli-Z gates."""
    def __init__(self, nqubit=1, wires=None, den_mat=False, tsr_mode=False):
        super().__init__(name='ZLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            z = PauliZ(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            self.gates.append(z)


class HLayer(SingleLayer):
    """A layer of Hadamard gates."""
    def __init__(self, nqubit=1, wires=None, den_mat=False, tsr_mode=False):
        super().__init__(name='HLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            h = Hadamard(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            self.gates.append(h)


class RxLayer(SingleLayer):
    """A layer of Rx gates."""
    def __init__(self, nqubit=1, wires=None, inputs=None, den_mat=False, tsr_mode=False, requires_grad=True):
        super().__init__(name='RxLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for i, wire in enumerate(self.wires):
            if inputs is None:
                theta = None
            else:
                theta = inputs[i]
            rx = Rx(inputs=theta, nqubit=nqubit, wires=wire, den_mat=den_mat,
                    tsr_mode=True, requires_grad=requires_grad)
            self.gates.append(rx)
            self.npara += rx.npara

    def inverse(self):
        layer = deepcopy(self)
        gates = nn.Sequential()
        for gate in self.gates[::-1]:
            gates.append(gate.inverse())
        layer.gates = gates
        layer.wires = self.wires[::-1]
        return layer


class RyLayer(SingleLayer):
    """A layer of Ry gates."""
    def __init__(self, nqubit=1, wires=None, inputs=None, den_mat=False, tsr_mode=False, requires_grad=True):
        super().__init__(name='RyLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for i, wire in enumerate(self.wires):
            if inputs is None:
                theta = None
            else:
                theta = inputs[i]
            ry = Ry(inputs=theta, nqubit=nqubit, wires=wire, den_mat=den_mat,
                    tsr_mode=True, requires_grad=requires_grad)
            self.gates.append(ry)
            self.npara += ry.npara

    def inverse(self):
        layer = deepcopy(self)
        gates = nn.Sequential()
        for gate in self.gates[::-1]:
            gates.append(gate.inverse())
        layer.gates = gates
        layer.wires = self.wires[::-1]
        return layer


class RzLayer(SingleLayer):
    """A layer of Rz gates."""
    def __init__(self, nqubit=1, wires=None, inputs=None, den_mat=False, tsr_mode=False, requires_grad=True):
        super().__init__(name='RzLayer', nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for i, wire in enumerate(self.wires):
            if inputs is None:
                theta = None
            else:
                theta = inputs[i]
            rz = Rz(inputs=theta, nqubit=nqubit, wires=wire, den_mat=den_mat,
                    tsr_mode=True, requires_grad=requires_grad)
            self.gates.append(rz)
            self.npara += rz.npara

    def inverse(self):
        layer = deepcopy(self)
        gates = nn.Sequential()
        for gate in self.gates[::-1]:
            gates.append(gate.inverse())
        layer.gates = gates
        layer.wires = self.wires[::-1]
        return layer


class CnotLayer(DoubleLayer):
    """A layer of CNOT gates."""
    def __init__(self, nqubit=2, wires=None, name='CnotLayer', den_mat=False, tsr_mode=False):
        super().__init__(name=name, nqubit=nqubit, wires=wires, den_mat=den_mat, tsr_mode=tsr_mode)
        for wire in self.wires:
            cnot = CNOT(nqubit=nqubit, wires=wire, den_mat=den_mat, tsr_mode=True)
            self.gates.append(cnot)

    def inverse(self):
        wires = []
        for wire in reversed(self.wires):
            wires.append(wire)
        return CnotLayer(nqubit=self.nqubit, wires=wires, name=self.name,
                         den_mat=self.den_mat, tsr_mode=self.tsr_mode)


class CnotRing(CnotLayer):
    """A layer of CNOT gates in a cyclic way."""
    def __init__(self, nqubit=2, minmax=None, step=1, reverse=False, den_mat=False, tsr_mode=False):
        if minmax is None:
            minmax = [0, nqubit-1]
        assert isinstance(minmax, list)
        assert len(minmax) == 2
        assert all(isinstance(i, int) for i in minmax)
        assert minmax[0] > -1 and minmax[0] < minmax[1] and minmax[1] < nqubit
        self.minmax = minmax
        self.step = step
        self.reverse = reverse
        nwires = minmax[1] - minmax[0] + 1
        if reverse: # from minmax[1] to minmax[0]
            wires = [[minmax[0] + i, minmax[0] + (i-step) % nwires] for i in range(minmax[1] - minmax[0], -1, -1)]
        else:
            wires = [[minmax[0] + i, minmax[0] + (i+step) % nwires] for i in range(minmax[1] - minmax[0] + 1)]
        super().__init__(nqubit=nqubit, wires=wires, name='CnotRing', den_mat=den_mat, tsr_mode=tsr_mode)
