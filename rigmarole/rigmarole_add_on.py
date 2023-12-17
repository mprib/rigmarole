import bpy
import copy
import json
import time
import csv

bl_info = {
    "name": "Comprehensive Rigging and Animation Tool",
    "author": "Mac Prible",
    "version": (0, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > Rigging Tab",
    "description": "An add-on for rigging and animation based on output from Pyxy3D",
    "category": "Animation"
}

######################################## BEGIN CODE USED FOR DATA IMPORT ##############################
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

def import_empties(csv_list_dict):
    # create a list of all the empties that need to get populated in the animation
    all_columns = list(csv_list_dict[0].keys())
    empty_names = [field_name[0:-2] for field_name in all_columns if field_name[-2:] == "_x"]

    create_empties(empty_names)
    print(f"Empty names are {empty_names}")

    # This code takes a long time...
    for frame in csv_list_dict:
        frame_index = int(frame["sync_index"])
        print(f"Loading in trajectories for frame {frame_index}")
        for empty_name in empty_names:
            location = get_landmark_location(frame, empty_name)
            if location is not None:
                set_empty_location_at_frame(empty_name,frame_index,location)


###################################################### BEGIN HOLISTIC MODEL CREATION ###################################

class HolisticModel():
    def __init__(self, name:str):
        print(f"Creating Model with name {name}")
        # place in a new metahuman rig
        self.rig = bpy.ops.object.armature_human_metarig_add()
        print("Armature added")
        self.rig = bpy.context.object
        self.rig.name = name
        # self.rig.pose.ik_solver = 'ITASC'   # non-standard IK solver 
        self.rig.pose.ik_solver = 'LEGACY' 
        
        # delete untracked breast bones
        self.delete_untracked()

        self.set_midhip_origin()

    def delete_untracked(self):
        delete_bones = ['breast.L', 'breast.R']
        self.enable_edit()
        # replace 'bone_name' with the bone you want to remove
        for bone_name in delete_bones:
            bone = self.rig.data.edit_bones.get(bone_name)
            if bone:
                self.rig.data.edit_bones.remove(bone)

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
        bpy.context.view_layer.objects.active = self.rig
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')

    def enable_object(self):
        bpy.context.view_layer.objects.active = self.rig
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.armature.select_all(action='DESELECT')

    def enable_pose(self):
        bpy.context.view_layer.objects.active = self.rig
        print("Selecting all elements of the rig")
        self.rig.select_set(True)
        # Make sure you know you are in object mode for the rig
        print("Attempting to shift to POSE mode")
        bpy.ops.object.mode_set(mode='POSE')

        # bpy.ops.object.mode_set(mode='POSE')
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

###################################################### BEGIN IK RELATED CODE  ##########################################

# def create_anchor(rig_anchors, track_to_anchor, empty_data):
#     """
#     create an anchor empty to parent the rig to. 
    
#     Note that this will have not just position, but also orientation. 
    
#     2 point tracking of the hips seems to manage well and evokes sensible pelvic tilt in the sagittal plane,
#     This is likely owing to the IK.
    
#     """
   
#     bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
#     bpy.data.objects['Camera'].select_set(True)

#     bpy.ops.object.empty_add(type='PLAIN_AXES')
#     bpy.ops.object.constraint_add(type="TRACK_TO")
#     bpy.context.object.constraints["Track To"].name = "Track To"
#     bpy.context.object.constraints["Track To"].target = bpy.data.objects[track_to_anchor]
#     bpy.context.object.constraints["Track To"].up_axis = 'UP_Z'
#     bpy.context.object.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_X'
#     empty = bpy.context.object
#     empty.name = "anchor"


#     # Need to figure out how many 
#     ### setting human rig location based on rig_anchor points
#     for frame in empty_data:
#         sync_index = int(frame["sync_index"])
    
#         ############ BEGIN COMPLICATED MEAN ANCHOR POSITION
#         # I believe I set this up to accomodate instances where an empty blinks out of view
#         # it is a complicated way to take an average of two positions
#         rig_anchor_locations = []
#         for anchor in rig_anchors:
#             anchor_location = get_landmark_location(frame,anchor)
#             rig_anchor_locations.append(anchor_location)     

#         observed_anchor_locations = [loc for loc in rig_anchor_locations if loc is not None]
#         anchor_count = len(observed_anchor_locations)
#         partial_location = [(loc[0]/anchor_count, loc[1]/anchor_count, loc[2]/anchor_count) for loc in observed_anchor_locations]

#         mean_anchor_location = [0,0,0]
#         for loc in partial_location:
#             mean_anchor_location[0]+=loc[0]
#             mean_anchor_location[1]+=loc[1]
#             mean_anchor_location[2]+=loc[2]
#         ########  END COMPLICATED MEAN POSITION CALCULATION
        
#         empty.location = mean_anchor_location
#         empty.keyframe_insert(data_path="location", frame=sync_index)  # insert keyframe
#         bpy.context.scene.frame_set(sync_index)  # update the current frame


def get_animated_frames(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return []

    animated_frames = set()
    for fcurve in obj.animation_data.action.fcurves:
        for keyframe_point in fcurve.keyframe_points:
            animated_frames.add(int(keyframe_point.co.x))  # co.x is the frame number

    return sorted(list(animated_frames))

def create_anchor(rig_anchors, track_to_anchor):
    """
    create an anchor empty to parent the rig to. 
    
    Note that this will have not just position, but also orientation. 
    
    2 point tracking of the hips seems to manage well and evokes sensible pelvic tilt in the sagittal plane,
    This is likely owing to the IK.
    
    """
   
    bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
    bpy.data.objects['Camera'].select_set(True)

    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].name = "Track To"
    bpy.context.object.constraints["Track To"].target = bpy.data.objects[track_to_anchor]
    bpy.context.object.constraints["Track To"].up_axis = 'UP_Z'
    bpy.context.object.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_X'
    anchor = bpy.context.object
    anchor.name = "anchor"
    
    # Get a combined list of all animated frames for the rig anchors
    all_frames = set()
    for anchor_name in rig_anchors:
        all_frames.update(get_animated_frames(anchor_name))
    all_frames = sorted(list(all_frames))

    # Iterate over each frame and calculate the mean location
    for frame in all_frames:
        bpy.context.scene.frame_set(frame)  # update the current frame
        mean_location = [0, 0, 0]
        for anchor_name in rig_anchors:
            empty = bpy.data.objects.get(anchor_name)
            if empty:
                mean_location[0] += empty.location.x
                mean_location[1] += empty.location.y
                mean_location[2] += empty.location.z

        # Calculate mean location
        mean_location = [coord / len(rig_anchors) for coord in mean_location]

        # Set and keyframe the anchor's location
        anchor.location = mean_location
        anchor.keyframe_insert(data_path="location", frame=frame)

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


BONE_TARGETS = {
    "lid.T.R.003":"right_inner_eye",
    "lid.T.L.003":"left_inner_eye",
    "shoulder.R":"right_shoulder",
    "shoulder.L":"left_shoulder",
    "upper_arm.R":"right_elbow",
    "upper_arm.L":"left_elbow",
    "forearm.R":"right_wrist",
    "forearm.L":"left_wrist",
    "thigh.R":"right_knee",
    "thigh.L":"left_knee",
    "shin.R":"right_ankle",
    "shin.L":"left_ankle",
    "foot.R":"right_foot_index",
    "foot.L":"left_foot_index",

    "f_pinky.03.R":"right_pinky_tip",
    "f_pinky.02.R":"right_pinky_DIP",
    "f_pinky.01.R":"right_pinky_PIP",
    "palm.04.R":"right_pinky_MCP",
   
    "f_pinky.03.L":"left_pinky_tip",
    "f_pinky.02.L":"left_pinky_DIP",
    "f_pinky.01.L":"left_pinky_PIP",
    "palm.04.L":"left_pinky_MCP",

    "f_ring.03.R":"right_ring_finger_tip",
    "f_ring.02.R":"right_ring_finger_DIP",
    "f_ring.01.R":"right_ring_finger_PIP",
    "palm.03.R":"right_ring_finger_MCP",

    "f_ring.03.L":"left_ring_finger_tip",
    "f_ring.02.L":"left_ring_finger_DIP",
    "f_ring.01.L":"left_ring_finger_PIP",
    "palm.03.L":"left_ring_finger_MCP",

    "f_middle.03.L":"left_middle_finger_tip",
    "f_middle.02.L":"left_middle_finger_DIP",
    "f_middle.01.L":"left_middle_finger_PIP",
    "palm.02.L":"left_middle_finger_MCP",

    "f_middle.03.R":"right_middle_finger_tip",
    "f_middle.02.R":"right_middle_finger_DIP",
    "f_middle.01.R":"right_middle_finger_PIP",
    "palm.02.R":"right_middle_finger_MCP",

    "f_index.03.L":"left_index_finger_tip",
    "f_index.02.L":"left_index_finger_DIP",
    "f_index.01.L":"left_index_finger_PIP",
    "palm.01.L":"left_index_finger_MCP",

    "f_index.03.R":"right_index_finger_tip",
    "f_index.02.R":"right_index_finger_DIP",
    "f_index.01.R":"right_index_finger_PIP",
    "palm.01.R":"right_index_finger_MCP",

    
    "thumb.03.L":"left_thumb_tip",
    "thumb.02.L":"left_thumb_IP",
    "thumb.01.L":"left_thumb_MCP",

    "thumb.03.R":"right_thumb_tip",
    "thumb.02.R":"right_thumb_IP",
    "thumb.01.R":"right_thumb_MCP",

}

# by default, chain counts will be set to 1 , if something else is wanted configure it here
CHAIN_COUNTS = {
    "lid.T.R.003":0,
    "lid.T.L.003":0,
    # "palm.01.L":2,
    # "palm.02.L":2,
    # "palm.03.L":2,
    # "palm.04.L":2,
    # "palm.01.R":2,
    # "palm.02.R":2,
    # "palm.03.R":2,
    # "palm.04.R":2,

    # "f_pinky.03.R":5,
    # "f_pinky.03.L":5,
    # "f_ring.03.R":5,
    # "f_ring.03.L":5,
}


######################################################  BEGIN ACTUAL ADD ON SCRIPT ##########################################
# Operator for Creating Scaled Rig
class OT_CreateScaledRig(bpy.types.Operator):
    bl_idname = "rigmarole.create_scaled_rig"
    bl_label = "Import Scaled Rig"
    bl_description = "Create a scaled rig based on JSON input"


    # Define the file filter
    filter_glob: bpy.props.StringProperty(
        default='*.json',
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        print(f"Creating scaled rig based on {self.filepath}")
        # Ensure we are in Object mode
        if bpy.context.object:
            if bpy.context.object.mode != 'OBJECT':
                # Switch to Object mode
                bpy.ops.object.mode_set(mode='OBJECT')

        # clear_scene()
        # holistic_model.create_scaled_rig(self.filepath)
        model = HolisticModel("Rigmarole")
        model.scale_to_config(self.filepath)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Operator for Importing Empties
class OT_ImportEmpties(bpy.types.Operator):
    bl_idname = "rigmarole.import_empties"
    bl_label = "Import Empties"
    bl_description = "Import empties from a CSV file"

    # Define the file filter
    filter_glob: bpy.props.StringProperty(
        default='*labelled.csv',
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        print(f"Importing empties from {self.filepath}")
        # load in trajectory data
        # Create an empty list to hold the data
        data = []
        data_row_count = 1
        print(f"beginning to load csv data at {time.time()}")
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
                data_row_count+=1
        print(f"Completing load of csv data at {time.time()}")

        import_empties(data)
        return {'FINISHED'}

    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}        


# Operator for Applying IK
class OT_ApplyIK(bpy.types.Operator):
    bl_idname = "rigmarole.apply_ik"
    bl_label = "Apply IK"
    bl_description = "Apply Inverse Kinematics to the rig"

    def execute(self, context):
        print("Applying Inverse Kinematics...")
        rig_anchors = ["right_hip", "left_hip"]
        track_to_anchor = rig_anchors[0]

        rig_name = "Rigmarole"  # Replace with the name of your rig
        rig = bpy.data.objects.get(rig_name)
        if rig is not None:
            print(f"Rig found: {rig.name}")
        else:
            print("Rig not found.")

        create_anchor(rig_anchors,track_to_anchor)
        print("Setting rig to anchor")
        print(f"Tracking of anchored segment based off of {track_to_anchor}")

        set_rig_to_anchor(rig)

        print("Adding IK constraints")
        for bone_name, target_name in BONE_TARGETS.items():
            bone = rig.pose.bones[bone_name]    # Add the IK constraint to the bone 
            ik_constraint = bone.constraints.new('IK')
    
            # Set the target of the IK constraint
            ik_constraint.target = bpy.data.objects[target_name]
            print(f"Applying IK contstraint for bone {bone_name} to follow {target_name}")
            # Set the chain count
            if bone_name in CHAIN_COUNTS.keys():
                ik_constraint.chain_count = CHAIN_COUNTS[bone_name]
            else:
                ik_constraint.chain_count = 1
 
        
        # Your IK application logic here
        return {'FINISHED'}

# Operator for Baking Animation
class OT_BakeAnimation(bpy.types.Operator):
    bl_idname = "rigmarole.bake_animation"
    bl_label = "Bake Animation"
    bl_description = "Bake animation onto the rig"

    def execute(self, context):
        # get rig 
        rig_name = "Rigmarole"  # Replace with the name of your rig
        rig = bpy.data.objects.get(rig_name)
        if rig is not None:
            print(f"Rig found: {rig.name}")
        else:
            print("Rig not found.")
        
        # get set of frames 
        # Get a combined list of all animated frames for the rig anchors
        all_frames = set()
        all_frames.update(get_animated_frames("anchor"))
        all_frames = sorted(list(all_frames))
        start_frame = all_frames[0]
        end_frame = all_frames[-1]
        step = 1
         
        print("Setting OBJECT mode")

        bpy.context.view_layer.objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
        print("Initiate baking of object animation")
        bpy.ops.nla.bake(frame_start=start_frame, frame_end=end_frame, step = step, only_selected=True, visual_keying=True,
                        clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})


        # Set to Pose Mode and bake the pose's animation
        print("Setting POSE mode")
        bpy.context.view_layer.objects.active = rig
        print("Selecting all elements of the rig")
        rig.select_set(True)
        # Make sure you know you are in object mode for the rig
        print("Attempting to shift to POSE mode")
        bpy.ops.object.mode_set(mode='POSE')
        print("Initiate baking of POSE animation (time intensive operation)")
        bpy.ops.nla.bake(frame_start=start_frame, frame_end=end_frame, step=step, only_selected=False, visual_keying=True,
                        clear_constraints=True, use_current_action=True, bake_types={'POSE'})
                 
        print("removing empties now that animation is baked")
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                bpy.data.objects.remove(obj)
        print("empties successfully removed")
        
        return {'FINISHED'}

# UI Panel for the Add-on
class RIG_PT_Rigmarole_Panel(bpy.types.Panel):
    bl_label = "Rigmarole"
    bl_idname = "RIG_PT_RigmarolePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rigmarole'

    def draw(self, context):
        layout = self.layout
        layout.operator("rigmarole.create_scaled_rig")
        layout.operator("rigmarole.import_empties")
        layout.operator("rigmarole.apply_ik")
        layout.operator("rigmarole.bake_animation")

def register():
    bpy.utils.register_class(OT_CreateScaledRig)
    bpy.utils.register_class(OT_ImportEmpties)
    bpy.utils.register_class(OT_ApplyIK)
    bpy.utils.register_class(OT_BakeAnimation)
    bpy.utils.register_class(RIG_PT_Rigmarole_Panel)

def unregister():
    bpy.utils.unregister_class(OT_CreateScaledRig)
    bpy.utils.unregister_class(OT_ImportEmpties)
    bpy.utils.unregister_class(OT_ApplyIK)
    bpy.utils.unregister_class(OT_BakeAnimation)
    bpy.utils.unregister_class(RIG_PT_Rigmarole_Panel)

if __name__ == "__main__":
    register()
