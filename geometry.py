"""Деталь варіанта 4: пластина W×H з дугами R зверху/знизу, 4 отвори Ø d, квадратний виріз."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Part:
    W: float = 90      # ширина пластини
    H: float = 60      # висота пластини
    R: float = 40      # радіус дуги (Ø80)
    hole_d: float = 14
    hole_x: float = 30  # центри отворів (±hole_x, ±hole_y)
    hole_y: float = 15
    sq: float = 30     # сторона квадратного вирізу

    def _arc(self, r, a0, a1, n=48):
        t = np.linspace(a0, a1, n)
        return np.c_[r * np.cos(t), r * np.sin(t)]

    def contours(self):
        """Список замкнених контурів (зовнішній, 4 отвори, квадрат) як масиви точок."""
        W, H, R = self.W / 2, self.H / 2, self.R
        assert R > H and np.sqrt(R * R - H * H) < W, "R має бути > H/2 і дуга має вкладатися в ширину"
        xa = np.sqrt(R * R - H * H)           # дуга перетинає прямі y=±H/2 — звідси кінці відрізків
        a = np.arctan2(H, xa)
        outer = np.vstack([
            [[W, -H], [W, H], [xa, H]], self._arc(R, a, np.pi - a),
            [[-W, H], [-W, -H], [-xa, -H]], self._arc(R, np.pi + a, 2 * np.pi - a),
        ])
        circ = self._arc(self.hole_d / 2, 0, 2 * np.pi, 72)
        holes = [circ + [sx * self.hole_x, sy * self.hole_y] for sx in (1, -1) for sy in (1, -1)]
        s = self.sq / 2
        square = np.array([[-s, -s], [s, -s], [s, s], [-s, s]])
        return [outer, *holes, square]
