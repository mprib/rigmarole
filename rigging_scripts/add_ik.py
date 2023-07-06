
import bpy

# Ensure we're in Pose mode
bpy.ops.object.mode_set(mode='POSE')

# Get the armature object
rig = bpy.data.objects['human_rig']

# dict[bone:empty_target]
targets_IK = {
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
    "foot.L":"left_foot_index"
}

for bone_name, target_name in targets_IK.items():
    bone = rig.pose.bones[bone_name]

    # Add the IK constraint to the bone
    ik_constraint = bone.constraints.new('IK')
    
    # Set the target of the IK constraint
    ik_constraint.target = bpy.data.objects[target_name]
    
    # Set the chain count
    ik_constraint.chain_count = 1
