# This stub runs a python script relative to the currently open
# blend file, useful when editing scripts externally.

import bpy
import os

# Use your own script name here:



def run_script(filename):
    filepath = os.path.join(os.path.dirname(bpy.data.filepath), filename)
    global_namespace = {"__file__": filepath, "__name__": "__main__"}
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)


filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\import_empties.py"
run_script(filename)


#filename = r"C:\Users\Mac Prible\repos\learn_blender\rigging_scripts\load_meta_ik_anim.py"
#run_script(filename)