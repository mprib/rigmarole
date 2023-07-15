# This stub runs a python script relative to the currently open
# blend file, useful when editing scripts externally.

import bpy
import os
import sys
from pathlib import Path
# Use your own script name here:



def run_script(filename):
    
    filepath = os.path.join(os.path.dirname(bpy.data.filepath), filename)
    global_namespace = {"__file__": filepath, "__name__": "__main__"}
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)  


# filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\import_rig.py"
# run_script(filename)

# scaling_frame = 75

# bpy.context.scene.frame_set(scaling_frame)

# filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\scale_rig.py"
# run_script(filename)


# filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\add_ik.py"
# run_script(filename)

filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\on_plane.py"
run_script(filename)
 