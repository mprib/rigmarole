import bpy

scaling_frame = 280

bpy.context.scene.frame_set(scaling_frame)

# Make sure we're in object mode
bpy.ops.object.mode_set(mode='OBJECT')

# Get the rig object
rig = bpy.data.objects['human_rig']
bpy.context.view_layer.objects.active = rig
# rig.select_set(True)


distal_shift = {
    "forearm.R":"right_wrist",
    "forearm.L":"left_wrist",
                }







head_bones = {
    "thigh.L":"left_hip",
    "thigh.R":"right_hip",
    "upper_arm.L": "left_shoulder",
    "upper_arm.R": "right_shoulder"
}

tail_bones = {
    "upper_arm.L":"left_elbow",
    "upper_arm.R":"right_elbow",
    "thigh.L":"left_knee",
    "thigh.R":"right_knee",
    "shin.L":"left_ankle",
    "shin.R":"right_ankle",
    "forearm.L":"left_wrist",
    "forearm.R":"right_wrist"
}


for bone in rig.data.bones:
    # Get the corresponding empties
    adjust_head = bone.name in head_bones.keys()
    adjust_tail = bone.name in tail_bones.keys()

    if adjust_head or adjust_tail:
        
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bone = rig.data.edit_bones[bone.name]
        
        if adjust_head:
            target_empty = bpy.data.objects.get(head_bones[bone.name])
            edit_bone.head = rig.matrix_world.inverted() @ target_empty.matrix_world.to_translation()
        if adjust_tail:
            target_empty = bpy.data.objects.get(tail_bones[bone.name])
            edit_bone.tail = rig.matrix_world.inverted() @ target_empty.matrix_world.to_translation()
