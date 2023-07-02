#%%

from pathlib import Path
import os
import toml
import time
import csv
import bpy

def clear_scene():
    # create a clean slate for adding the armature
    ## get a list of all the objects
    all_objects = bpy.context.scene.objects
    ## Delete all but the ones you want
    for obj in all_objects:
        # If the object is not a camera or light, delete it
        print(obj.name)
        if obj.type not in ['CAMERA', 'LIGHT']:
            bpy.data.objects.remove(obj, do_unlink=True)

    # reset cursor to origin, just in case
    bpy.context.scene.cursor.location = (0,0,0)
    

def create_empties(names): 
    """
    names: list of strings
    """
    # an object must be selected to go into object mode...
    # The scene must have something named 'Camera'
    bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
    bpy.data.objects['Camera'].select_set(True)

    bpy.ops.object.mode_set(mode="OBJECT")
    for name in names:
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.object
        empty.name = name

    
def set_empty_location_at_frame(name, frame_index, location):
    """
    name:str
    frame_index:int
    location: tuple of (x,y,z)
    """
    empty = bpy.data.objects[name]
    empty.location = location
    empty.keyframe_insert(data_path='location', frame = frame_index)


#%%
def export_empties(csv_list_dict):
    # create a list of all the empties that need to get populated in the animation
    all_columns = list(csv_list_dict[0].keys())
    empty_names = [field_name[0:-2] for field_name in all_columns if field_name[-2:] == "_x"]

    create_empties(empty_names)
    print(f"Empty names are {empty_names}")

    for frame in csv_list_dict:
        frame_index = int(frame["sync_index"])

        for empty_name in empty_names:
        
            location = get_location(frame, empty_name)
            if location is not None:
                set_empty_location_at_frame(empty_name,frame_index,location)
                
def get_location(sync_index_dict, empty_name):
    """
    sync_index_dict: dictionary containng a single row of data from the trajectory csv file
    because this is written for use in blender, standard csv library import is used providing
    a list of dictionaries for accessing values.    
    """ 
    x = sync_index_dict[f"{empty_name}_x"]
    y = sync_index_dict[f"{empty_name}_y"]
    z = sync_index_dict[f"{empty_name}_z"]

    if x != '':    
        x = float(x)
        y = float(y)
        z = float(z)

        location = (x,y,z)
    else:
        location = None
    
    return location




# %%

processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\4_cam\recording_1\HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")

clear_scene()
# load in trajectory data
# Create an empty list to hold the data
data = []
# Open the CSV file and process the inputs one by one
print(f"beginning to load csv data at {time.time()}")
with open(trajectory_data_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)
print(f"Completing load of csv data at {time.time()}")


export_empties(data)

def get_human_rig():
    """
    returns a human metarig that has been placed in the scene
    note that the origin of the rig has been shifted to the mid-hips
    """
    ########################## ADD RIG######################################
    # place in a new metahuman rig
    bpy.ops.object.armature_human_metarig_add()
    metahuman = bpy.context.object
    metahuman.pose.ik_solver = 'ITASC'   # non-standard IK solver 
    metahuman.name = "human_rig"

    ########################### Shift rig origin to mid hips for ease of rig movement #########
    # change to pose mode to apply the pose of the metarig
    bpy.ops.object.mode_set(mode='POSE')

    # get the mid hip location in a global frame of reference
    left_hip_local = metahuman.pose.bones["thigh.L"].head
    right_hip_local = metahuman.pose.bones["thigh.R"].head

    left_hip_global = metahuman.matrix_world @ left_hip_local
    right_hip_global = metahuman.matrix_world @ right_hip_local

    mid_hips_global = (left_hip_global+right_hip_global)/2

    # Move the 3D cursor to the target origin
    bpy.context.scene.cursor.location = mid_hips_global

    # switch back to object mode and select the rig
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    metahuman.select_set(True)

    # Set the origin to the 3D cursor
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    # Move the armature back to its original location
    metahuman.location = mid_hips_global

    # reset the cursor location to the origin
    bpy.context.scene.cursor.location = (0,0,0)

    return metahuman


metahuman = get_human_rig()