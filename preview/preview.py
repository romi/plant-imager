#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

from romi.remote_device import OquamXYTheta

if __name__ == "__main__":

    print("In preview.py")

    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', type=str, nargs='?', default="10.42.0.1",
                    help='IP address of the registry')
    args = parser.parse_args()

    cnc = OquamXYTheta("cnc", args.registry)
    cnc.power_up()

    xc = 0.3
    yc = 0.3
    r = 0.15
    n = 5
    speed = 0.4
    delta_alpha = -2.0 * math.pi / n

    cnc.moveto(xc - r, yc, math.pi/2, speed)

    while True:
        for i in range(n):
            input("Press Enter to continue...")
            cnc.helix(xc, yc, delta_alpha, delta_alpha, speed)
        cmd = input("Press Enter to scan or any other key + Enter to do the preview again ")
        if cmd == "":
            print("Preview quit")
            break
        else:
            input("Press Enter when ready to start again the preview")
            cnc.homing()
            cnc.moveto(xc - r, yc, math.pi/2, speed)