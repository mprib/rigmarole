import bpy
import time

# Get the armature
armature = bpy.data.objects['human_rig']

# Make sure the armature is the active object
bpy.context.view_layer.objects.active = armature
armature.select_set(True)
# Add a small delay to allow Blender to catch up
time.sleep(0.1)

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
    root_bone = armature.data.edit_bones[bone]
    root_bone.select = False
    root_bone.select_head = False
    root_bone.select_tail = True
    select_children(root_bone)

    # Get the empty object
    empty = bpy.data.objects[target]

    # Convert both the empty's location and the bone's tail location to the global space
    global_bone_tail = armature.matrix_world @ root_bone.tail
    global_empty_location = empty.matrix_world.to_translation()

    # Calculate the translation vector in the global space
    translation_vector = global_empty_location - global_bone_tail

    # Translate the selection
    bpy.ops.transform.translate(value=translation_vector)
    # # Calculate the required translation
    
    # Deselect all bones
    bpy.ops.armature.select_all(action='DESELECT')