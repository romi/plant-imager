#!usr/bin/env python3

import os
from re import sub
import subprocess
import sys

def run():
     os.environ['PYTHONPATH'] = "$(python -c \"import sys; print(':'.join(x for x in sys.path if x)))"
     params = ' '.join(map(str,sys.argv[1:]))
     print("params = ", params)
     cmd = ["blender", "-E", "CYCLES", "-b", "-P", params]
     #subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__=="__main__":
     run()