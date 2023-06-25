# This is a test
# ok. Trying to write in that scripting window is horrible...here we are now..

import bpy
import time

# create a clean slate for adding the armature
## get a list of all the objects
all_objects = bpy.context.scene.objects
## Delete all but the ones you want
for obj in all_objects:
    # If the object is not a camera or light, delete it
    print(obj.name)
    if obj.type not in ['CAMERA', 'LIGHT']:
        bpy.data.objects.remove(obj, do_unlink=True)

## reset the cursort location to the origin
bpy.context.scene.cursor.location = (0,0,0)

# place in a new metahuman rig
bpy.ops.object.armature_basic_human_metarig_add()
metahuman = bpy.context.object
metahuman.name = "human"


# Move the cursor to the root of the metahuman rig
## Get the root bone
spine_root = metahuman.data.bones["spine"]  # replace "root" with the name of your root bone if it's different
## Get the head location of the root bone in world coordinates
spine_root_location = metahuman.matrix_world @ spine_root.head
# Move the 3D cursor
bpy.context.scene.cursor.location = spine_root_location



#bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

# create empty at metahuman root
bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=spine_root_location, scale=(1, 1, 1))
root_empty = bpy.context.object 
root_empty.name = "root_empty"

################ Everything up to here seems to be working the way that I would like

# Store the current location of the armature
original_location = metahuman.location.copy()

# Set the desired location for the new origin
desired_location = (0, 0, 0)  

# Move the armature to the desired location
metahuman.location = desired_location

# Select the armature
bpy.ops.object.select_all(action='DESELECT')
metahuman.select_set(True)

# Set the origin to the 3D cursor
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# Move the armature back to its original location
metahuman.location = original_location

##################################

# Parent the armature to the empty
metahuman.parent = root_empty

# Apply the transformation
#bpy.ops.object.select_all(action='DESELECT')
#metahuman.select_set(True)
#bpy.context.view_layer.objects.active = metahuman
#bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Delete the empty
#bpy.ops.object.select_all(action='DESELECT')
#empty.select_set(True)
#bpy.ops.object.delete()

# frame_num = 1  # start on frame 1
# bpy.context.scene.frame_set(frame_num)  # set the initial frame


# for i in range(0,10):
#     test_empty.location.x -= .1
#     test_empty.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     metahuman.location.x -= .15
#     metahuman.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     frame_num += 10  # increment frame
#     bpy.context.scene.frame_set(frame_num)  # update the current frame

# for i in range(0,10):
#     test_empty.location.y += .1
#     test_empty.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     metahuman.location.x += .15
#     metahuman.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     frame_num += 10  # increment frame
#     bpy.context.scene.frame_set(frame_num)  # update the current frame

# # Select the armature object
# armature = bpy.data.objects["test_human"]
# armature.select_set(True)
# bpy.context.view_layer.objects.active = armature

# Switch to Edit Mode
# bpy.ops.object.mode_set(mode='EDIT')

# NOTE: This seems to elongate one bone at the expense of the other because the tail of one bone is the head of another perhaps...
# Select the bone you want to modify

# armature.data.edit_bones["upper_arm.L"].use_connect=False

# armature.data.edit_bones["upper_arm.L"].tail.y +=.5
# armature.data.edit_bones["forearm.L"].tail.y += .5

# armature.data.edit_bones["upper_arm.L"].use_connect= True
# armature.data.edit_bones["hand.L"].tail.y += .5

# Switch back to Object Mode
# bpy.ops.object.mode_set(mode='OBJECT')

# # Select the armature object
# armature = bpy.data.objects["test_human"]
# armature.select_set(True)
# bpy.context.view_layer.objects.active = armature

# Bake the animation
#bpy.ops.nla.bake(frame_start=1, frame_end=180, only_selected=True, visual_keying=True)

# Select all the pose bones in the armature
# for bone in armature.pose.bones:
#     bone.bone.select = True

# Bake the animation for the bones
#bpy.ops.nla.bake(frame_start=1, frame_end=180, only_selected=True, visual_keying=True)