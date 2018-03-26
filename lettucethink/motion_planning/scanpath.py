#!/usr/bin/env python3
import numpy as np

def circle(cx, cy, R, N):
   alpha = np.linspace(0, 2 * np.pi, N + 1)
   pan = np.linspace(0, -360.0, N + 1)
   x = cx + R * np.cos(alpha)
   y = cy + R * np.sin(alpha)
   return x, y, pan

def square(xs, ys, zs, d, ns):
    return []
