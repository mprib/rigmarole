
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bpy
from importlib import reload
import import_empties
reload(import_empties)
import holistic_model
reload(holistic_model)
from holistic_model import HolisticModel, clear_scene
from import_empties import import_empties, set_rig_to_anchor, create_anchor
import csv
import time
from pathlib import Path
import toml

IMPORT_EMPTIES = True 
APPLY_IK = False
BAKE_ANIMATION = False

clear_scene()
# scale_json = r"C:\Users\Mac Prible\repos\rigmarole\sample\metarig_config_HOLISTIC_OPENSIM.json"
scale_json = r"C:\Users\Mac Prible\OneDrive\pyxy3d\20230818_do\recording_2\\HOLISTIC_OPENSIM\metarig_config_HOLISTIC_OPENSIM.json"
model = HolisticModel("test")
model.scale_to_config(scale_json)

# processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\4_cam_A\recording_4\HOLISTIC_OPENSIM")
processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\20230818_do\recording_3\\HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")

if IMPORT_EMPTIES:
    # load in trajectory data
    # Create an empty list to hold the data
    data = []
    data_row_count = 1
    print(f"beginning to load csv data at {time.time()}")
    with open(trajectory_data_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
            data_row_count+=1
    print(f"Completing load of csv data at {time.time()}")

    import_empties(data)


if APPLY_IK:
    rig_anchors = ["right_hip", "left_hip"]
    track_to_anchor = rig_anchors[0]

    create_anchor(rig_anchors,track_to_anchor, data)
    set_rig_to_anchor(model)


    # Ensure we're in Pose mode
    # bpy.ops.object.mode_set(mode='POSE')

    # dict[bone:empty_target]
    bone_targets = {
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
    chain_counts = {
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


    for bone_name, target_name in bone_targets.items():
        bone = model.rig.pose.bones[bone_name]    # Add the IK constraint to the bone 
        ik_constraint = bone.constraints.new('IK')
    
        # Set the target of the IK constraint
        ik_constraint.target = bpy.data.objects[target_name]
        print(f"Applying IK contstraint for bone {bone_name} to follow {target_name}")
        # Set the chain count
        if bone_name in chain_counts.keys():
            ik_constraint.chain_count = chain_counts[bone_name]
        else:
            ik_constraint.chain_count = 1


if BAKE_ANIMATION:
    # Baking animation
    start_frame = 1
    end_frame = data_row_count
    step = 1
    # Select the object

    # Set to Object Mode and bake the object's animation
    print("Setting OBJECT mode")
    model.enable_object()
    print("Initiate baking of object animation")
    bpy.ops.nla.bake(frame_start=start_frame, frame_end=end_frame, step = step, only_selected=True, visual_keying=True,
                    clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})


    # Set to Pose Mode and bake the pose's animation
    print("Setting POSE mode")
    model.enable_pose()
    print("Initiate baking of POSE animation")
    bpy.ops.nla.bake(frame_start=start_frame, frame_end=end_frame, step=step, only_selected=False, visual_keying=True,
                    clear_constraints=True, use_current_action=True, bake_types={'POSE'})
                 
    print("removing empties now that animation is baked")
    for obj in bpy.data.objects:
        if obj.type == 'EMPTY':
            bpy.data.objects.remove(obj)
    print("empties successfully removed")