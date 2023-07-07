
import bpy

# Ensure we're in Pose mode
bpy.ops.object.mode_set(mode='POSE')

# Get the armature object
rig = bpy.data.objects['human_rig']

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
    "f_pinky.03.L":"left_pinky_tip",
    "f_ring.03.R":"right_ring_finger_tip",
    "f_ring.03.L":"left_ring_finger_tip",
    "f_index.03.L":"left_index_finger_tip",
    "f_index.03.R":"right_index_finger_tip",
    "f_middle.03.L":"left_middle_finger_tip",
    "f_middle.03.R":"right_middle_finger_tip",
    "thumb.03.L":"left_thumb_tip",
    "thumb.03.R":"right_thumb_tip",
}

# by default, chain counts will be set to 1, if something else is wanted configure it here
chain_counts = {
    "lid.T.R.003":0,
    "lid.T.L.003":0,
    "f_pinky.03.R":5,
    "f_pinky.03.L":5,
    "f_ring.03.R":5,
    "f_ring.03.L":5,
}


for bone_name, target_name in bone_targets.items():
    bone = rig.pose.bones[bone_name]

    # Add the IK constraint to the bone
    ik_constraint = bone.constraints.new('IK')
    
    # Set the target of the IK constraint
    ik_constraint.target = bpy.data.objects[target_name]
    
    # Set the chain count
    if bone_name in chain_counts.keys():
        ik_constraint.chain_count = chain_counts[bone_name]
    else:
        ik_constraint.chain_count = 1

