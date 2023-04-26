import bpy

C = bpy.context

print(C.object)

for i in range(0,4):
    bpy.ops.mesh.primitive_monkey_add(enter_editmode=False, align='WORLD', location=(0, i, i*2), scale=(1, 1, 1))

