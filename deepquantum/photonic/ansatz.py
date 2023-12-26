from typing import Any, List, Optional, Union

import numpy as np
import torch

from .circuit import QumodeCircuit


class Clements(QumodeCircuit):
    def __init__(
        self,
        nmode: int,
        init_state: Any,
        cutoff: int = None,
        basis: bool = True,
        phi_first: bool = True,
        noise: bool = False,
        mu: float = 0,
        sigma: float = 0.1
    ) -> None:
        super().__init__(nmode=nmode, init_state=init_state, cutoff=cutoff, basis=basis, name='Clements',
                         noise=noise, mu=mu, sigma=sigma)
        self.phi_first = phi_first
        wires1 = self.wires[1::2]
        wires2 = self.wires[2::2]
        if not phi_first:
            for wire in self.wires:
                self.ps(wire, encode=True)
        for i in range(nmode):
            if i % 2 == 0:
                for j in range(len(wires1)):
                    self.mzi([wires1[j] - 1, wires1[j]], phi_first=phi_first, encode=True)
            else:
                for j in range(len(wires2)):
                    self.mzi([wires2[j] - 1, wires2[j]], phi_first=phi_first, encode=True)
        if phi_first:
            for wire in self.wires:
                self.ps(wire, encode=True)

    def dict2data(self, angle_dict):
        for key in angle_dict.keys():
            angle = angle_dict[key]
            if not isinstance(angle, torch.Tensor):
                angle = torch.tensor(angle)
            angle_dict[key] = angle.reshape(-1)
        data = []
        columns = np.array([0] * self.nmode)
        wires1 = self.wires[1::2]
        wires2 = self.wires[2::2]
        if not self.phi_first:
            for i in range(self.nmode):
                data.append(angle_dict[(i, columns[i])])
                columns[i] += 1
        for i in range(self.nmode):
            if i % 2 == 0:
                for j in range(len(wires1)):
                    wire = wires1[j] - 1
                    if self.phi_first:
                        phi   = angle_dict[(wire, columns[wire])]
                        theta = angle_dict[(wire, columns[wire] + 1)]
                    else:
                        theta = angle_dict[(wire, columns[wire])]
                        phi   = angle_dict[(wire, columns[wire] + 1)]
                    data.append(theta)
                    data.append(phi)
                    columns[wire] += 2
            else:
                for j in range(len(wires2)):
                    wire = wires2[j] - 1
                    if self.phi_first:
                        phi   = angle_dict[(wire, columns[wire])]
                        theta = angle_dict[(wire, columns[wire] + 1)]
                    else:
                        theta = angle_dict[(wire, columns[wire])]
                        phi   = angle_dict[(wire, columns[wire] + 1)]
                    data.append(theta)
                    data.append(phi)
                    columns[wire] += 2
        if self.phi_first:
            for i in range(self.nmode):
                data.append(angle_dict[(i, columns[i])])
                columns[i] += 1
        return torch.cat(data)
