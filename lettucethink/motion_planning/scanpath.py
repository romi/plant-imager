#!/usr/bin/env python3
import math

def circle(center_x, center_y, z, tilt, radius, num_points):
   res = []
   for i in range(num_points):
       angle = 2*i*math.pi / num_points
       x = center_x - radius * math.cos(angle)
       y = center_y - radius * math.sin(angle)
       res.append((x, y, z, angle, tilt))
   return res
