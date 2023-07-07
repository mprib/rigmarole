import bpy

scaling_frame = 280

bpy.context.scene.frame_set(scaling_frame)

# Make sure we're in object mode
bpy.ops.object.mode_set(mode='OBJECT')

# Get the rig object
rig = bpy.data.objects['human_rig']
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.armature.select_all(action='DESELECT')

distal_shifts = {
    "forearm.R":"right_wrist",
    "forearm.L":"left_wrist",
    "foot.R":"right_foot_index",
    "foot.L":"left_foot_index"
}

def select_children(bone):
    for child in bone.children:
        child.select = True
        child.select_head = True
        child.select_tail = True
        select_children(child)


for bone, target in distal_shifts.items():
    
    # Select 'forearm.R' and all bones distal to it
    root_bone = rig.data.edit_bones[bone]
    root_bone.select = False
    root_bone.select_head = False
    root_bone.select_tail = True
    select_children(root_bone)

    # Get the empty object
    empty = bpy.data.objects[target]

    # Convert both the empty's location and the bone's tail location to the global space
    global_bone_tail = rig.matrix_world @ root_bone.tail
    global_empty_location = empty.matrix_world.to_translation()

    # Calculate the translation vector in the global space
    translation_vector = global_empty_location - global_bone_tail

    # Translate the selection
    bpy.ops.transform.translate(value=translation_vector)
    # # Calculate the required translation
    
    # Deselect all bones
    bpy.ops.armature.select_all(action='DESELECT')


# Make sure we're in object mode
bpy.ops.object.mode_set(mode='OBJECT')


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
    "forearm.R":"right_wrist",
    "shoulder.L":"left_shoulder",
    "shoulder.R":"right_shoulder",
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
