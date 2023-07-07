#%%

from pathlib import Path
import os
import toml
import time
import csv
import bpy
import math

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

def import_empties(csv_list_dict):
    # create a list of all the empties that need to get populated in the animation
    all_columns = list(csv_list_dict[0].keys())
    empty_names = [field_name[0:-2] for field_name in all_columns if field_name[-2:] == "_x"]

    create_empties(empty_names)
    print(f"Empty names are {empty_names}")

    for frame in csv_list_dict:
        frame_index = int(frame["sync_index"])

        for empty_name in empty_names:
            location = get_landmark_location(frame, empty_name)
            if location is not None:
                set_empty_location_at_frame(empty_name,frame_index,location)

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

def get_landmark_location(sync_index_dict, empty_name):
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
    
def set_empty_location_at_frame(name, frame_index, location):
    """
    name:str
    frame_index:int
    location: tuple of (x,y,z)
    """
    empty = bpy.data.objects[name]
    empty.location = location
    empty.keyframe_insert(data_path='location', frame = frame_index)

def get_human_rig():
    """
    returns a human metarig that has been placed in the scene
    note that the origin of the rig has been shifted to the mid-hips
    """
    ########################## ADD RIG######################################
    # place in a new metahuman rig
    metahuman = bpy.ops.object.armature_human_metarig_add()
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

    # set the object origin to the mid hips 
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    metahuman.select_set(True)
    bpy.context.scene.cursor.location = mid_hips_global
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = (0,0,0)

    
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    rig_anchor = bpy.context.object
    rig_anchor.name = "rig_anchor"
    rig_anchor.location = metahuman.location

    return metahuman

def create_anchor(rig_anchors, track_to_anchor):
    """
    create an anchor empty to parent the rig to 
    """
   
    # rig_anchors = ["left_hip", "right_hip"] 
    # create a new anchor
    bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
    bpy.data.objects['Camera'].select_set(True)

    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].name = "Track To"
    bpy.context.object.constraints["Track To"].target = bpy.data.objects[track_to_anchor]
    bpy.context.object.constraints["Track To"].up_axis = 'UP_Z'
    bpy.context.object.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_X'
    empty = bpy.context.object
    empty.name = "anchor"

    ### setting human rig location based on rig_anchor points
    for frame in data:
        sync_index = int(frame["sync_index"])
    
        rig_anchor_locations = []
        # get an average location for a given set of anchors
        for anchor in rig_anchors:
            anchor_location = get_landmark_location(frame,anchor)
            # print(f"Location of {anchor} is {anchor_location}")
            rig_anchor_locations.append(anchor_location)     

        observed_anchor_locations = [loc for loc in rig_anchor_locations if loc is not None]
        # print(f"observed anchor locations are: {observed_anchor_locations}")
        anchor_count = len(observed_anchor_locations)
        partial_location = [(loc[0]/anchor_count, loc[1]/anchor_count, loc[2]/anchor_count) for loc in observed_anchor_locations]

        mean_anchor_location = [0,0,0]
        for loc in partial_location:
            mean_anchor_location[0]+=loc[0]
            mean_anchor_location[1]+=loc[1]
            mean_anchor_location[2]+=loc[2]

        empty.location = mean_anchor_location
        empty.keyframe_insert(data_path="location", frame=sync_index)  # insert keyframe
        bpy.context.scene.frame_set(sync_index)  # update the current frame


def set_rig_to_anchor(rig):
    # Get the rig and anchor
    # rig = bpy.data.objects['human_rig']
    anchor = bpy.data.objects['anchor']
    # Create a new copy location constraint
    constraint = rig.constraints.new('COPY_LOCATION')

    # Set the target of the constraint to the anchor
    constraint.target = anchor

    # If you want to copy rotation as well, you can create a COPY_ROTATION constraint in the same way:
    rotation_constraint = rig.constraints.new('COPY_ROTATION')
    rotation_constraint.target = anchor

##############################################

processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\4_cam_A\recording_4\HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")

clear_scene()

# load in trajectory data
# Create an empty list to hold the data
data = []
print(f"beginning to load csv data at {time.time()}")
with open(trajectory_data_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)
print(f"Completing load of csv data at {time.time()}")

import_empties(data)



print("getting human rig")
metahuman = get_human_rig()

print("Creating anchor")


rig_anchors = ["right_hip", "left_hip"]
track_to_anchor = rig_anchors[0]

create_anchor(rig_anchors,track_to_anchor)

print("setting rig to anchor")
anchor_name = "anchor"
set_rig_to_anchor(metahuman)



# %%
