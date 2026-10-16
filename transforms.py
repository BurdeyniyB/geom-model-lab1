"""Лінійні перетворення в однорядкових однорідних координатах: P' = P · M, P = [x, y, 1]."""
import numpy as np


def apply(pts, M):
    """Множення вектора точки на матрицю перетворення (+ ділення на w для проективних)."""
    p = np.c_[pts, np.ones(len(pts))] @ M          # [x', y', w']
    w = np.where(np.abs(p[:, 2:]) < 1e-9, 1e-9, p[:, 2:])  # ponytail: w≈0 (точка на лінії обрію) не відсікається
    return p[:, :2] / w


def shift(dx, dy):
    return np.array([[1, 0, 0], [0, 1, 0], [dx, dy, 1]], float)


def rotate(cx, cy, deg):
    """Обертання навколо довільної точки C: T(-C) · R(φ) · T(C)."""
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    return shift(-cx, -cy) @ R @ shift(cx, cy)


def scale(cx, cy, sx, sy):
    """Масштабування відносно точки C."""
    S = np.diag([sx, sy, 1.0])
    return shift(-cx, -cy) @ S @ shift(cx, cy)


def point_symmetry(cx, cy):
    """Симетрія відносно точки C = масштаб (-1, -1) відносно C."""
    return scale(cx, cy, -1, -1)


def affine(Xx, Xy, Yx, Yy, Ox, Oy):
    """Нова система координат: образи базисних векторів X, Y та початку O."""
    return np.array([[Xx, Xy, 0], [Yx, Yy, 0], [Ox, Oy, 1]], float)


def projective(Xx, Xy, wX, Yx, Yy, wY, Ox, Oy, w0):
    return np.array([[Xx, Xy, wX], [Yx, Yy, wY], [Ox, Oy, w0]], float)


if __name__ == "__main__":
    p = np.array([[10.0, 5.0], [-3, 7]])
    assert np.allclose(apply(p, rotate(70, 70, 360)), p)
    assert np.allclose(apply(p, rotate(2, 3, 90) @ rotate(2, 3, -90)), p)
    assert np.allclose(apply([[1, 0]], rotate(0, 0, 90)), [[0, 1]])
    assert np.allclose(apply(p, point_symmetry(1, 1)), 2 - p)
    assert np.allclose(apply(p, projective(1, 0, 0, 0, 1, 0, 0, 0, 1)), p)
    assert np.allclose(apply(p, affine(2, 0, 0, 3, 1, 1)), p * [2, 3] + 1)
    print("ok")
