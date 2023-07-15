from pathlib import Path
import os
import toml
import time
import csv
import bpy
import math
import copy

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

    return metahuman
    # bpy.ops.object.empty_add(type='PLAIN_AXES')
    # rig_anchor = bpy.context.object
    # rig_anchor.name = "rig_anchor"
    # rig_anchor.location = metahuman.location


def select_children(rig, bone, tail_also = True):

    if tail_also:
        rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        bone.select_tail = True

    for child in bone.children:
        child.select = True
        child.select_head = True
        child.select_tail = True
        select_children(rig, child, tail_also=False)

def move_selected(old_location, new_location):
    
    translation = (
        old_location[0]-new_location[0], 
        old_location[1]-new_location[1], 
        old_location[2]-new_location[2]) 
    
    print(f"The total amount translated is {translation}")
    bpy.ops.transform.translate(value=translation, orient_axis_ortho='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=False, use_snap_nonedit=False, use_snap_selectable=False)


def scale_selected(factor):
#    bpy.ops.transform.resize(value=(factor, factor, factor), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=False, use_snap_nonedit=False, use_snap_selectable=False)
   bpy.ops.transform.resize(value=(factor, factor, factor))
  

if __name__ == "__main__":

    clear_scene()
    rig = get_human_rig()

    target_segment_name = "upper_arm.R"
    target_length = 0.5

    bpy.ops.object.mode_set(mode='EDIT')
    target_segment = rig.data.edit_bones[target_segment_name]
   
    old_location = copy.copy(target_segment.tail) 
    print(f"Old location of target segment tail is {old_location}")  
    select_children(rig, target_segment, tail_also=True)
    scale_selected(.75) # this will cause the proximal segment to also change length and that needs to be reset 
    new_location = copy.copy(target_segment.tail)
    print(f"After scaling of distal segments, target segment tail is now at {new_location}")
    translation = new_location-old_location
    move_selected(old_location, new_location)
    # target_segment.tail = old_location


    