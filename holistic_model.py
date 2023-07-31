"""

This following will create a blender metarig that scales to meet the specification
outlined in a json file that contains the following:

Single Value (trunk params)
Shoulder_Width:
Hip_Width:
Hip_Shoulder_Distance:
Inner_Eye_Distance:
Shoulder_Inner_Eye_Distance:

Bilateral (should be Left_ and Right_ versions)
Palm_Width: measured from MCP2 to MCP4
Foot_Length:
Upper_Arm_Length
Forearm_Length
Wrist_to_MCP1
Wrist_to_MCP2
Wrist_to_MCP3
Wrist_to_MCP4
Wrist_to_MCP5
Prox_Phalanx_1_Length
Prox_Phalanx_2_Length
Prox_Phalanx_3_Length
Prox_Phalanx_4_Length
Prox_Phalanx_5_Length
Mid_Phalanx_2_Length
Mid_Phalanx_3_Length
Mid_Phalanx_4_Length
Mid_Phalanx_5_Length
Dist_Phalanx_1_Length
Dist_Phalanx_2_Length
Dist_Phalanx_3_Length
Dist_Phalanx_4_Length
Dist_Phalanx_5_Length
Thigh_Length
Shin_Length

"""

from pathlib import Path
import os
import time
import csv
import bpy
import math
import copy
import json

import os

class HolisticModel():
    
    def __init__(self, name:str):
        # place in a new metahuman rig
        self.rig = bpy.ops.object.armature_human_metarig_add()
        self.rig = bpy.context.object
        self.rig.name = name
        self.rig.pose.ik_solver = 'ITASC'   # non-standard IK solver 

        self.set_midhip_origin()


    def set_midhip_origin(self):
        # change to pose mode to apply the pose of the metarig
        # bpy.ops.object.mode_set(mode='POSE')

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
        
        # reset cursor to global origin
        bpy.context.scene.cursor.location = (0,0,0)

    def scale_to_config(self, config_json):

        with open(config_json,"r") as f:
            scale = json.load(f)

        self.set_shoulder_width(scale["Shoulder_Width"])
        self.set_hip_width(scale["Hip_Width"])
        self.scale_torso(scale["Hip_Shoulder_Distance"])
        self.scale_face(scale["Inner_Eye_Distance"])
        self.scale_neck(scale["Shoulder_Inner_Eye_Distance"])

        for side in ["R", "L"]:
            self.resize_segment(f"upper_arm.{side}", scale["Upper_Arm"])
            self.resize_segment(f"forearm.{side}", scale["Forearm"])
            self.resize_segment(f"thigh.{side}", scale["Thigh_Length"])
            self.resize_segment(f"shin.{side}", scale["Shin_Length"])
            self.scale_foot(side, scale["Foot"])

            # scale the palm...because width and length get impacted by each other, dial in with a few iterations
            # choosing 3 here just as a guess that these things will not get distorted *that* much by the scaling
            # in an alternate dimension so will quickly stabilize
            for _ in range(0,3):
                self.scale_palm_width(scale["Palm"], side)
                self.scale_wrist_to_segment_tail("thumb.01", side, scale["Wrist_to_MCP1"] )
                self.scale_wrist_to_segment_tail("palm.01", side, scale["Wrist_to_MCP2"] )
                self.scale_wrist_to_segment_tail("palm.02", side, scale["Wrist_to_MCP3"] )
                self.scale_wrist_to_segment_tail("palm.03", side, scale["Wrist_to_MCP4"] )
                self.scale_wrist_to_segment_tail("palm.04", side, scale["Wrist_to_MCP5"] )
        
            # thumb needs to be handled seperately 
            self.resize_segment(f"thumb.02.{side}", scale["Prox_Phalanx_1"]) 
            self.resize_segment(f"thumb.03.{side}", scale["Dist_Phalanx_1"]) 

            finger_numbers = {"index":2, "middle":3, "ring":4, "pinky":5}
            for finger, number in finger_numbers.items():
                self.resize_segment(f"f_{finger}.01.{side}", scale[f"Prox_Phalanx_{number}"]) 
                self.resize_segment(f"f_{finger}.02.{side}", scale[f"Mid_Phalanx_{number}"]) 
                self.resize_segment(f"f_{finger}.03.{side}", scale[f"Dist_Phalanx_{number}"]) 

        # somewhere around here I think I may need to insert a new method that adjusts the ankle height 
        # to some target value
        self.shift_feet_to_floor()


    def select_children(self, bone, first_pass = True):

        skip_bones = []
        
        if first_pass:
            self.rig.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            bone.select_tail = True

            # only want to adjust the torso with adjustments to the spine segment length
            if bone.name == "spine":
                skip_bones = ["thigh.R", "thigh.L", "pelvis.R", "pelvis.L"]
                

        for child in bone.children:
            if child.name in skip_bones:
                continue
            child.select = True
            child.select_head = True
            child.select_tail = True
            self.select_children(child, first_pass=False)


    def scale_distal_segments(self, proximal_segment_name, scale_factor):

        self.enable_edit()

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
        self.enable_edit()

        target_segment = self.rig.data.edit_bones[segment_name]
    
        # find out where the tail would be if the segment were longer
        old_location = copy.copy(target_segment.tail) 
        # print(f"Old location of target segment tail is {old_location}")  
        original_length = target_segment.length
        # print(f"Old segment length is {target_segment.length}")

        target_segment.length = new_length
        new_location = copy.copy(target_segment.tail)

        # restore the segment to its original length 
        # print(f"After scaling of distal segments, target segment tail is now at {new_location}")
        target_segment.length = original_length
        self.select_children(target_segment)

        # make the actual change in the rig to resize the segment
        move_selected(old_location, new_location)

    def enable_edit(self):
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')

    def enable_object(self):
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.armature.select_all(action='DESELECT')

    def set_hip_width(self, width):
        self.set_limb_root_width("thigh", "pelvis", width)
    
    def set_shoulder_width(self,width):
        self.set_limb_root_width("upper_arm", "shoulder", width)

    def set_limb_root_width(self, limb_segment_name, trunk_segment_name, width):
        
        self.enable_edit()

        unilateral_displacement = width/2
    
        for side in ["R", "L"]: 
            bone_name = f"{limb_segment_name}.{side}"
            bone = self.rig.data.edit_bones[bone_name]
            initial_global_location = self.rig.matrix_world @ bone.head
            current_x = initial_global_location[0]

            print(f"current x position is {current_x}")

            if current_x >0:
                target_x = unilateral_displacement
            else:
                target_x = -unilateral_displacement

            print(f"target x position is {target_x}")

            target_global_location = initial_global_location.copy()
            target_global_location[0] = target_x

            self.select_children(bone)
            bone.select = True
            bone.select_head = True

            bone_name = f"{trunk_segment_name}.{side}"
            bone = self.rig.data.edit_bones[bone_name]
            bone.select = True
            bone.select_tail = True
    
            move_selected(initial_global_location, target_global_location)    
        
        self.enable_edit()
   
        

    def scale_group_to_target(self, current_distance_function, target_distance, scaling_function, cutoff_delta = 0.001):
        
        loop_count = 0

        while True:
            current_distance = current_distance_function()
            
            print(f"Current distance is {current_distance}")
            delta = abs(current_distance - target_distance)
            print(f"Current delta is {delta}")
            if delta < cutoff_delta:
                print("Breaking out of loop. Target close enough")
                break
       
            step_size = (delta/current_distance) 

            # if it's bouncing around too much and not converging. Force smaller steps as iterations proceed
            if loop_count > 10:
                step_size = step_size * (1000-loop_count)/1000
         
            if current_distance > target_distance:
                factor = 1-step_size
            else:
                factor = 1+ step_size
  
            scaling_function(factor)
            
            loop_count+=1
           
            # for testing purposes to figure out what is going on ... 
            if loop_count > 200:
                break
        
    def scale_neck(self,target_distance):
        
        def get_shoulder_inner_eye_distance():
        
            r_inner_eye = self.rig.data.edit_bones["lid.B.R"].head
            l_inner_eye = self.rig.data.edit_bones["lid.B.L"].head

            r_shoulder = self.rig.data.edit_bones["upper_arm.R"].head
            l_shoulder = self.rig.data.edit_bones["upper_arm.L"].head

            r_dist = (r_shoulder - r_inner_eye).length
            l_dist = (l_shoulder - l_inner_eye).length

            # Compute the mean distance
            mean_distance = (r_dist + l_dist) / 2

            return mean_distance
        
        def scale_neck_by_factor(factor):
            scaled_bones = ["spine.004", "spine.005", "spine.006"]
       
            for bone in scaled_bones:
                self.scale_single_segment(bone, factor)

        self.scale_group_to_target(get_shoulder_inner_eye_distance, target_distance,scale_neck_by_factor)
        
    def scale_single_segment(self, segment_name, factor):
        self.enable_edit()
        
        old_length = self.rig.data.edit_bones[segment_name].length
        new_length = factor*old_length
        
        self.resize_segment(segment_name, new_length)
        
    def scale_torso(self, target_hip_shoulder_distance):
        """
        Note that this must be used *after* the shoulder and hip width is set     
        """

        def shoulder_hip_distance():
            self.enable_edit()
           
            r_hip = self.rig.data.edit_bones["thigh.R"].head
            l_hip = self.rig.data.edit_bones["thigh.L"].head

            r_shoulder = self.rig.data.edit_bones["upper_arm.R"].head
            l_shoulder = self.rig.data.edit_bones["upper_arm.L"].head

            # Compute the distances between the corresponding hip and shoulder
            r_dist = (r_shoulder - r_hip).length
            l_dist = (l_shoulder - l_hip).length

            # Compute the mean distance
            mean_distance = (r_dist + l_dist) / 2

            return mean_distance
            
            
        def scale_spine_bones_by_factor(factor):
            scaled_bones = ["spine", "spine.001", "spine.002", "spine.003"]
            for bone in scaled_bones:
                self.scale_single_segment(bone, factor)
   
        self.scale_group_to_target(shoulder_hip_distance, target_hip_shoulder_distance,scale_spine_bones_by_factor) 

    def scale_face(self, target_inner_eye_distance):
        print(f"About to scale face to targetted inner eye distance of {target_inner_eye_distance}")

        def inner_eye_distance():
            self.enable_edit()
        
            r_inner_eye = self.rig.data.edit_bones["lid.B.R"].head
            l_inner_eye = self.rig.data.edit_bones["lid.B.L"].head
         
            inner_eye_distance = (r_inner_eye-l_inner_eye).length
            print(f"inner eye distance is {inner_eye_distance}")
        
            return inner_eye_distance

        
        def scale_face_by_factor(factor):
            self.scale_distal_segments("face", factor)

        self.scale_group_to_target(inner_eye_distance, target_inner_eye_distance,scale_face_by_factor) 

    def scale_palm_width(self,target_hand_width, side):
        
        def hand_width():
            self.enable_edit()
            
            mcp_head_2 = self.rig.data.edit_bones[f"palm.01.{side}"].tail
            mcp_head_4 = self.rig.data.edit_bones[f"palm.04.{side}"].tail

            mcp_distance = (mcp_head_2-mcp_head_4).length
            return mcp_distance
        
        def scale_hand_by_factor(factor):
            self.scale_distal_segments(f"forearm.{side}", factor)

        self.scale_group_to_target(hand_width, target_hand_width,scale_hand_by_factor)
        
    def scale_wrist_to_segment_tail(self, target_segment_name,side:str, target_length): 
        """
        The hand contains major landmarks (e.g. heads of metacarpals) that don't have an 
        analogue in the holistic mediapipe output. Need to scale single segment to fit an
        overarching total length from wrist to knuckle
        
        
        target_segment: name of bone in the hand the scale. Will be palm.0# or thumb.01
        side: 'R' or 'L'
        """
        # note this is in the context of metarig, not anatomy
        
        segment_name_w_side = f"{target_segment_name}.{side}"

        def wrist_to_segment_tail_length():
            wrist = self.rig.data.edit_bones[f"hand.{side}"].head
            print(f"wrist: {wrist}")
            mcp = self.rig.data.edit_bones[segment_name_w_side].tail
            print(f"segment tail: {mcp}")

            distance = (mcp-wrist).length

            return distance 

        def scale_segment_by_factor(factor):
            segment = self.rig.data.edit_bones[segment_name_w_side]
            print(f"Current length of segment is {segment.length}")
            new_length = segment.length * factor
            print(f"New target length of segment to reflect factor is {new_length}")
            self.resize_segment(segment_name_w_side, new_length)
            print(f"Following resize, length is {segment.length}")
        
        self.scale_group_to_target(wrist_to_segment_tail_length, target_length,scale_segment_by_factor)
    
    def scale_foot(self, side:str, target_length):
        
        def foot_length():
            self.enable_edit()
        
            heel = self.rig.data.edit_bones[f"heel.02.{side}"].head
            toe = self.rig.data.edit_bones[f"toe.{side}"].tail

            distance = (heel-toe).length
            return distance
        
        def scale_foot_by_factor(factor):
            self.scale_distal_segments(f"shin.{side}", factor)

        self.scale_group_to_target(foot_length, target_length,scale_foot_by_factor)

    def shift_feet_to_floor(self):
        
        right_heel_head = self.rig.data.edit_bones["heel.02.R"].head
        left_heel_head = self.rig.data.edit_bones["heel.02.L"].head

        right_heel_global = self.rig.matrix_world @ right_heel_head
        left_heel_global = self.rig.matrix_world @ left_heel_head
    
        right_depth = right_heel_global[2]
        left_depth = left_heel_global[2]
    
        mean_depth = (right_depth + left_depth)/2
        self.enable_object()
    
        bpy.ops.transform.translate(value=(0,0,-mean_depth)) 

def move_selected(old_location, new_location):
    
    translation = (
        new_location[0]-old_location[0], 
        new_location[1]-old_location[1], 
        new_location[2]-old_location[2]) 
    
    bpy.ops.transform.translate(value=translation)


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
    scale_json = r"C:\Users\Mac Prible\repos\rigmarole\sample\metarig_config_HOLISTIC_OPENSIM.json"
    rig = HolisticModel("test")
    rig.scale_to_config(scale_json)

    