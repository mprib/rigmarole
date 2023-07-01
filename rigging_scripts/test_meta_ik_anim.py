import bpy

############################## CLEAN SLATE ##############################
# create a clean slate for adding the armature
## get a list of all the objects
all_objects = bpy.context.scene.objects
## Delete all but the ones you want
for obj in all_objects:
    # If the object is not a camera or light, delete it
    print(obj.name)
    if obj.type not in ['CAMERA', 'LIGHT']:
        bpy.data.objects.remove(obj, do_unlink=True)

# reset the cursor location to the origin
bpy.context.scene.cursor.location = (0,0,0)

########################## ADD RIG######################################
# place in a new metahuman rig
bpy.ops.object.armature_human_metarig_add()
metahuman = bpy.context.object
metahuman.pose.ik_solver = 'ITASC'   # non-standard IK solver 
metahuman.name = "human_rig"

########################### Shift rig origin to mid hips for ease of rig movement #########
# change to pose mode to apply the pose of the metarig
bpy.ops.object.mode_set(mode='POSE')

# get the mid hip location in a global frame of reference
left_hip_local = metahuman.pose.bones["thigh.L"].head
right_hip_local = metahuman.pose.bones["thigh.R"].head

left_hip_global = metahuman.matrix_world @ left_hip_local
right_hip_global = metahuman.matrix_world @ right_hip_local

mid_hips_global = (left_hip_global+right_hip_global)/2

# Move the 3D cursor to the target origin
bpy.context.scene.cursor.location = mid_hips_global

# switch back to object mode and select the rig
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
metahuman.select_set(True)

# Set the origin to the 3D cursor
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# Move the armature back to its original location
metahuman.location = mid_hips_global

# reset the cursor location to the origin
bpy.context.scene.cursor.location = (0,0,0)


####################### GET A LIST OF ALL BONES   ########################
# Switch to pose mode
bpy.context.view_layer.objects.active = metahuman
bpy.ops.object.mode_set(mode='POSE')

for bone in metahuman.pose.bones:
    # Bone's head and tail in local space
    head_local = bone.head
    tail_local = bone.tail

    # Convert head and tail locations to global space
    head_global = metahuman.matrix_world @ head_local
    tail_global = metahuman.matrix_world @ tail_local

    # Print the bone name and the locations of head and tail
    print("Bone name:", bone.name)
    # print("Head location (global):", head_global)
    # print("Tail location (global):", tail_global)
    # print("---") # just to separate the info about each bone

# Switch back to object mode
bpy.ops.object.mode_set(mode='OBJECT')

# Apply the transformation
# bpy.ops.object.select_all(action='DESELECT')
# metahuman.select_set(True)
# bpy.context.view_layer.objects.active = metahuman
# bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Delete the empty

# frame_num = 1  # start on frame 1
# bpy.context.scene.frame_set(frame_num)  # set the initial frame
# ## reset the cursort location to the origin
# bpy.context.scene.cursor.location = (0,0,0)

# ##################################################

# for i in range(0,10):
#     root_empty.location.x -= .1
#     root_empty.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     # metahuman.location.x -= .15
#     # metahuman.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
#     frame_num += 10  # increment frame
#     bpy.context.scene.frame_set(frame_num)  # update the current frame

# # for i in range(0,10):
# #     test_empty.location.y += .1
# #     test_empty.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
# #     metahuman.location.x += .15
# #     metahuman.keyframe_insert(data_path="location", frame=frame_num)  # insert keyframe
# #     frame_num += 10  # increment frame
# #     bpy.context.scene.frame_set(frame_num)  # update the current frame

# # # Select the armature object
# metahuman.select_set(True)
# bpy.context.view_layer.objects.active = metahuman 

# # Switch to Edit Mode
# bpy.ops.object.mode_set(mode='EDIT')

# # NOTE: This seems to elongate one bone at the expense of the other because the tail of one bone is the head of another perhaps...
# # Select the bone you want to modify

# # armature.data.edit_bones["upper_arm.L"].use_connect=False

# # armature.data.edit_bones["upper_arm.L"].tail.y +=.5
# # armature.data.edit_bones["forearm.L"].tail.y += .5

# # armature.data.edit_bones["upper_arm.L"].use_connect= True
# # armature.data.edit_bones["hand.L"].tail.y += .5

# # Switch back to Object Mode
# # bpy.ops.object.mode_set(mode='OBJECT')

# # # Select the armature object
# # armature = bpy.data.objects["test_human"]
# # armature.select_set(True)
# # bpy.context.view_layer.objects.active = armature

# # Bake the animation
# bpy.ops.nla.bake(frame_start=1, frame_end=180, only_selected=True, visual_keying=True)

# # Select all the pose bones in the armature
# # for bone in armature.pose.bones:
# #     bone.bone.select = True

# # Bake the animation for the bones
# #bpy.ops.nla.bake(frame_start=1, frame_end=180, only_selected=True, visual_keying=True)