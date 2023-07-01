
# Note: successful running of this script requires running Blender as Administrator. Type "Blender" into the 
# launch box and right click on the Blender option. Select "Run as administrator"

import subprocess
import sys
import os
 
python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
target = os.path.join(sys.prefix, 'lib', 'site-packages')
 
subprocess.call([python_exe, '-m', 'ensurepip'])
subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])

#example package to install (SciPy):
subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'polars', '-t', target])
 
print('DONE')