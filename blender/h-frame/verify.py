"""Verify the saved production rig and its open, looping hero framing."""

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
index = scene.objects["RIG / J9"]
loader = scene.objects["RIG / Loader / flange"]
welder = scene.objects["RIG / Welder / flange"]
arc = scene.objects["Weld arc - animated TCP"]
tcp = scene.objects["MIG tool TCP - arc point"]
part = scene.objects["RIG / part:1"]
base = scene.objects["Skid · lower flange"]
camera = scene.camera


def world_corners(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def assert_same_pose(actual, expected, tolerance=0.002):
    assert all(abs(a - b) < tolerance for row, old in zip(actual, expected) for a, b in zip(row, old))


assert not bpy.data.libraries
assert len(bpy.data.scenes) == 1
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 2211, 24)
assert abs(scene.render.fps / scene.render.fps_base - 24) < 0.01
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 720)
assert base.parent is None and scene.objects["Recessed deck floor"].parent is None
assert not any("enclosure" in c.name.lower() for c in scene.collection.children)
assert "Cycle stand 26" in scene.objects

rig = scene.collection.children["01  |  Editable production controls"]
action = index.animation_data.action
animated_controls = [o for o in rig.objects if o.animation_data]
assert len(animated_controls) >= 38
assert all(o.animation_data.action == action and o.animation_data.action_slot for o in animated_controls)
assert len({o.animation_data.action_slot.handle for o in animated_controls}) == len(animated_controls)
assert scene.objects["Weld arc light"].data.animation_data.action == action

for role in ("Welder", "Loader"):
    parent = scene.objects["War Machine - MASTER"]
    for joint in ("base", "turret", "upper_arm", "elbow", "forearm", "wrist", "flange"):
        control = scene.objects[f"RIG / {role} / {joint}"]
        assert control.type == 'EMPTY' and control.parent == parent
        assert any(child.type == 'MESH' and not child.hide_render for child in control.children)
        parent = control

scene.frame_set(601)
start_camera = camera.matrix_world.copy()
start_arc = arc.matrix_world.translation.copy()
start_index = index.matrix_world.to_quaternion()
start_base = base.matrix_world.copy()
start_flanges = [obj.matrix_world.copy() for obj in (loader, welder)]
components = ("plate", "web", "seam 1", "seam 2")
start_parts = [
    world_corners(scene.objects[f"Cycle part {part_id} / {component}"])
    for part_id in (0, 1, 6) for component in components
]
parked_loader = loader.matrix_world.translation.copy()
start_welder = welder.matrix_world.translation.copy()
assert arc.scale.length > 0.01
assert (start_arc - tcp.matrix_world.translation).length < 0.002

scene.frame_set(1071)
station_axis = Vector((1, 0, 0))
assert abs((start_index @ station_axis).dot(index.matrix_world.to_quaternion() @ station_axis)) < 0.2
assert arc.scale.length == 0
assert base.matrix_world == start_base

scene.frame_set(1350)
staged = part.matrix_world.translation.copy()
assert staged.x > 1.4 and staged.y > 0.8
assert (loader.matrix_world.translation - parked_loader).length > 0.3

scene.frame_set(1455)
placed = part.matrix_world.translation
assert abs(placed.x - 0.5) < 0.002 and abs(placed.y) < 0.002
assert abs(placed.z - staged.z) < 0.002
assert (arc.matrix_world.translation - tcp.matrix_world.translation).length < 0.002
assert (welder.matrix_world.translation - start_welder).length > 0.05

# The bays are exchanged at the cut. Camera and welding TCP meet their opening
# poses, while the fixture has rotated exactly one native half turn.
scene.frame_set(1707)
assert_same_pose(camera.matrix_world, start_camera, tolerance=1e-5)
assert (arc.matrix_world.translation - start_arc).length < 0.002
assert (start_index @ station_axis).dot(index.matrix_world.to_quaternion() @ station_axis) < -0.999
for flange, start_pose in zip((loader, welder), start_flanges):
    assert_same_pose(flange.matrix_world, start_pose)

# Different part IDs occupy the same stations and supply stand after the swap.
end_parts = [
    world_corners(scene.objects[f"Cycle part {part_id} / {component}"])
    for part_id in (1, 2, 0) for component in components
]
for start_corners, end_corners in zip(start_parts, end_parts):
    assert all((start - end).length < 0.002 for start, end in zip(start_corners, end_corners))

meshes = [o for o in scene.objects if o.type == 'MESH' and o.name != "Studio ground"]
for frame in range(601, 1707, 2):
    scene.frame_set(frame)
    for obj in meshes:
        if obj.hide_render:
            continue
        for corner in world_corners(obj):
            view = world_to_camera_view(scene, camera, corner)
            assert 0.01 < view.x < 0.99 and 0.01 < view.y < 0.99, (frame, obj.name, view)

print("PASS: native editable production rig, loader placement, tracked weld arc, half-turn and full hero framing")
