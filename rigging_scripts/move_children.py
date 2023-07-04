import bpy

# Get the armature
armature = bpy.data.objects['human_rig']

bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='EDIT')

def select_children(bone):
    for child in bone.children:
        child.select = True
        child.select_head = True
        child.select_tail = True
        select_children(child)

# Select 'forearm.R' and all bones distal to it
root_bone = armature.data.edit_bones['forearm.R']
root_bone.select = False
root_bone.select_head = False
root_bone.select_tail = True
select_children(root_bone)

# Get the empty object
empty = bpy.data.objects['right_wrist']

# Calculate the required translation
translation = armature.matrix_world.inverted() @ empty.matrix_world.to_translation() - root_bone.tail

# I believe some locations are being moved twice because of heads/tails
new_locations = []

# Apply the translation to selected bones
for bone in armature.data.edit_bones:
    if bone.select:
        if bone.head not in new_locations:
            bone.head += translation
            new_locations.append(bone.head)
        if bone.tail not in new_locations:
            bone.tail += translation
            new_locations.append(bone.head)


#bpy.ops.object.mode_set(mode='OBJECT')