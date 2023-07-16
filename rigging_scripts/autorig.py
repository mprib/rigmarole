from pathlib import Path
import os
import toml
import time
import csv
import bpy
import math
import copy


class Autorig():
    
    def __init__(self, name:str):
        # place in a new metahuman rig
        self.rig = bpy.ops.object.armature_human_metarig_add()
        self.rig = bpy.context.object
        self.rig.name = name
        self.rig.pose.ik_solver = 'ITASC'   # non-standard IK solver 

        self.set_midhip_origin()
        
        
    def set_midhip_origin(self):
        # change to pose mode to apply the pose of the metarig
        bpy.ops.object.mode_set(mode='POSE')

        # get the mid hip location in a global frame of reference
        left_hip_local = self.rig.pose.bones["thigh.L"].head
        right_hip_local = self.rig.pose.bones["thigh.R"].head

        left_hip_global = self.rig.matrix_world @ left_hip_local
        right_hip_global = self.rig.matrix_world @ right_hip_local

        mid_hips_global = (left_hip_global+right_hip_global)/2

        # set the object origin to the mid hips 
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self.rig.select_set(True)
        bpy.context.scene.cursor.location = mid_hips_global
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = (0,0,0)


    def select_children(self, bone, first_pass = True):
        if first_pass:
            self.rig.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            bone.select_tail = True

        for child in bone.children:
            child.select = True
            child.select_head = True
            child.select_tail = True
            self.select_children(child, first_pass=False)


    def scale_distal_segments(self, proximal_segment_name, scale_factor):

        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')

        target_segment = self.rig.data.edit_bones[proximal_segment_name]
   
        old_location = copy.copy(target_segment.tail) 
        print(f"Old location of target segment tail is {old_location}")  

        self.select_children(target_segment)
        scale_selected(scale_factor) # this will cause the proximal segment to also change length and that needs to be reset 

        new_location = copy.copy(target_segment.tail)

        print(f"After scaling of distal segments, target segment tail is now at {new_location}")
        # restore distal segments to original location (basically resizing the proximal segment length)
        move_selected(new_location, old_location)


    def resize_segment(self, segment_name, new_length):

        # make sure that rig is in focus and correct mode enabled
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')

        target_segment = self.rig.data.edit_bones[segment_name]
    
        # find out where the tail would be if the segment were longer
        old_location = copy.copy(target_segment.tail) 
        print(f"Old location of target segment tail is {old_location}")  
        original_length = target_segment.length
        print(f"Old segment length is {target_segment.length}")

        target_segment.length = new_length
        new_location = copy.copy(target_segment.tail)
        # restore the segment to its original length 
        print(f"After scaling of distal segments, target segment tail is now at {new_location}")
        target_segment.length = original_length
        self.select_children(target_segment)

        # make the actual change in the rig to resize the segment
        move_selected(old_location, new_location)



def move_selected(old_location, new_location):
    
    translation = (
        new_location[0]-old_location[0], 
        new_location[1]-old_location[1], 
        new_location[2]-old_location[2]) 
    
    print(f"The total amount translated is {translation}")
    bpy.ops.transform.translate(value=translation, orient_axis_ortho='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=False, use_snap_nonedit=False, use_snap_selectable=False)


def scale_selected(factor):
   bpy.ops.transform.resize(value=(factor, factor, factor))

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

    
if __name__ == "__main__":

    clear_scene()
    rig = Autorig("test")

    rig.scale_distal_segments("forearm.R", 1.2)
    rig.scale_distal_segments("forearm.L", 1.2)
    rig.scale_distal_segments("shin.R", 1.2)
    rig.scale_distal_segments("shin.L", 1.2)
    rig.scale_distal_segments("face", 0.8)
    rig.resize_segment("spine.001", .6)
    