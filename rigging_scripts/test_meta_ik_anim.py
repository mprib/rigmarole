# This is a test
# ok. Trying to write in that scripting window is horrible...here we are now..

import bpy
import time

all_objects = bpy.context.scene.objects

# Iterate over all objects
for obj in all_objects:
    # If the object is not a camera or light, delete it
    print(obj.name)
    if obj.type not in ['Camera', 'Light']:
        bpy.data.objects.remove(obj, do_unlink=True)
        
bpy.ops.object.armature_basic_human_metarig_add()
metahuman = bpy.context.object
metahuman.name = "test_human"

bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(1, 0, 1), scale=(1, 1, 1))
test_empty = bpy.context.object 
test_empty.name = "left_hand_empty"
 
metahuman.pose.bones["hand.L"].constraints.new('IK').target = test_empty

frame_num = 1  # start on frame 1
bpy.context.scene.frame_set(frame_num)  # set the initial frame


for i in range(0,10):
    test_empty.location.x -= .1
    test_empty.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
    frame_num += 10  # increment frame
    bpy.context.scene.frame_set(frame_num)  # update the current frame

# Select the armature object
armature = bpy.data.objects["test_human"]
armature.select_set(True)
bpy.context.view_layer.objects.active = armature

# Switch to Edit Mode
bpy.ops.object.mode_set(mode='EDIT')

# Select the bone you want to modify
bone = armature.data.edit_bones["hand.L"]
# Change the length of the bone by moving its tail
bone.tail.y += 0.25  # Adjust as needed

armature.data.edit_bones["forearm.L"].tail.y += .25

# Switch back to Object Mode
bpy.ops.object.mode_set(mode='OBJECT')


