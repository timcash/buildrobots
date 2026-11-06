"""Check CAD joints, process contact, camera framing and loop closure."""

import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_task_scene import FRAMES, JOINT_AXES, JOINT_LIMITS, cut_path, paint_path, progress, weld_path


scene = bpy.context.scene
assert not bpy.data.libraries
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, FRAMES, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1440, 512)
assert all(text.font.packed_file for text in bpy.data.curves if isinstance(text, bpy.types.TextCurve))

stations = []
for index, (name, kind, path, tip_length, clearance) in enumerate((
    ('Painting', 'paint', paint_path, 0.162, 0.19),
    ('Cutting', 'cut', cut_path, 0.182, 0.025),
    ('Welding', 'weld', weld_path, 0.211, 0.037),
), 1):
    group = bpy.data.collections[f'{index:02} | {name}']
    station = group.objects[f'{name} station']
    links = [group.objects[f'{name} | {link}'] for link in ('base_link', *(f'link_{i}' for i in range(1, 7)))]
    tool = group.objects[f'{name} | tool0']
    streaks = [obj for obj in group.objects if obj.name.startswith(f'{kind.title()} | streak')]
    assert station['operation'] == kind and tool.parent == links[-1] and streaks
    assert all(child.parent == parent for parent, child in zip(links, links[1:]))
    assert all(link.type == 'MESH' and len(link.data.polygons) > 1000 for link in links)
    stations.append((station, links, tool, streaks, path, tip_length, clearance))

assert all(a[0].location.x < b[0].location.x for a, b in zip(stations, stations[1:]))
assert all(a.data == b.data == c.data for a, b, c in zip(*(station[1] for station in stations)))

tracked = [scene.camera, *(obj for _, links, tool, streaks, *_ in stations for obj in [*links, tool, *streaks])]
scene.frame_set(1)
opening = [obj.matrix_world.copy() for obj in tracked]
tips = [[] for _ in stations]
for frame in range(1, FRAMES + 1):
    scene.frame_set(frame)
    for index, (station, links, tool, streaks, path, tip_length, clearance) in enumerate(stations):
        for link, axis, limit in zip(links[1:], JOINT_AXES, JOINT_LIMITS):
            euler = Vector(link.rotation_euler)
            angle = euler.dot(axis)
            assert (euler - angle * axis).length < 1e-5 and abs(angle) <= limit + 1e-5
        for obj in [*links, *(child for child in tool.children if child.type == 'MESH')]:
            for corner in obj.bound_box:
                view = world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(corner))
                assert 0.01 < view.x < 0.99 and 0.01 < view.y < 0.99, (frame, obj.name, view)
        phase = (frame - 1 + station['cycle_offset_frames']) % FRAMES / FRAMES
        active = 0.065 < phase < 0.70
        assert all(streak.hide_render != active for streak in streaks), (frame, station.name)
        if active:
            t, lift = progress(phase)
            actual = station.matrix_world.inverted() @ tool.matrix_world @ Vector((0, 0, tip_length + clearance))
            expected = path(t) + Vector((0, 0, lift))
            assert (actual - expected).length < 0.0003, (frame, station.name, actual, expected)
            tips[index].append(actual)

for positions in tips:
    assert max(tip.y for tip in positions) - min(tip.y for tip in positions) > 0.55
scene.frame_set(FRAMES + 1)
for initial, obj in zip(opening, tracked):
    assert all(abs(a - b) < 0.0001 for row, end in zip(initial, obj.matrix_world) for a, b in zip(row, end)), obj.name

print('PASS: three CAD rigs, attached tools, work paths, process timing, framing, and loop closure')
