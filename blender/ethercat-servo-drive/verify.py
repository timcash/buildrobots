"""Check the saved EtherCAT scene in background Blender via the router."""

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
objects = bpy.data.objects
camera = scene.camera
groups = [obj for obj in objects if obj.type == 'EMPTY' and obj.name[:2].isdigit()]
parts = [obj for group in groups for obj in group.children if obj.type == 'MESH']
overlay = objects['Camera-space captions']
highlights = {
    52: 'Enclosure highlight',
    88: 'Port highlight',
    118: 'Control highlight',
    151: 'Power highlight',
    187: 'Thermal highlight',
}
intensities = {
    name: bpy.data.materials[name].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    for name in (*highlights.values(), 'EtherCAT link status')
}


def snapshot(frame):
    scene.frame_set(frame)
    transforms = {obj.name: tuple(v for row in obj.matrix_world for v in row)
                  for obj in objects if not obj.hide_render}
    visibility = {obj.name: (obj.hide_render, obj.hide_viewport) for obj in objects}
    materials = tuple(socket.default_value for socket in intensities.values())
    return transforms, visibility, materials, camera.data.ortho_scale


assert (scene.frame_start, scene.frame_end, scene.render.fps, scene.render.fps_base) == (1, 240, 24, 1)
assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) == (1280, 1024, 100)
assert len(groups) == 6 and len(parts) >= 225
assert len([font for font in bpy.data.fonts if font.packed_file]) == 1
assert not bpy.data.libraries and not bpy.data.images
assert snapshot(1) == snapshot(241), 'Visible scene or camera jumps at the loop boundary'

for frame, caption in ((18, 'Synchronized motion'), (52, 'Vented enclosure'), (88, 'EtherCAT ports'),
                       (118, 'Control board'), (151, 'Three-phase inverter'), (187, 'Finned heat sink'),
                       (215, 'Drive closes')):
    scene.frame_set(frame)
    assert not objects[caption].hide_render, (frame, caption)
    assert {name for name in highlights.values() if intensities[name].default_value >= .45} == (
        {highlights[frame]} if frame in highlights else set()), frame

for name, frame in (('Assembled data pulse / IN', 18), ('Exploded data pulse / OUT', 89),
                    ('Motion setpoint on PCB', 117), ('Motor phase switching pulse.001', 151)):
    scene.frame_set(frame)
    obj = objects[name]
    assert not obj.hide_render and obj.data.bevel_factor_end > obj.data.bevel_factor_start, (name, frame)

scene.frame_set(145)
assert all(group.location.length > .5 for group in groups)
scene.frame_set(230)
assert all(group.location.length < 1e-6 for group in groups)

# Test animated framing between the photographed poses, including the seam.
for frame in range(1, 242):
    scene.frame_set(frame)
    assert sum(obj.type == 'FONT' and not obj.hide_render for obj in overlay.children) == 5, frame
    for obj in parts:
        for corner in obj.bound_box:
            p = world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
            assert .01 < p.x < .99 and .19 < p.y < .999, (frame, obj.name, tuple(p))

print('PASS: editable assemblies, five highlights, signal and power pulses, framing and loop closure')
