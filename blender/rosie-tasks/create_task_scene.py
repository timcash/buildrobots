"""Build three process stations around the editable AMR rigs from slide 2."""

import sys
from math import cos, pi, radians, sin, tau
from pathlib import Path
from random import Random

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'rosie'))
from create_scene import aim, collection, finish, line, linear, object_in


FRAMES = 144
JOINT_AXES = tuple(Vector(axis) for axis in (
    (0, 0, 1), (0, 1, 0), (0, 1, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
))
JOINT_LIMITS = np.radians((177.617, 108.862, 148.969, 177.617, 126.051, 177.617))
BENCH_Z = 0.40


def smooth(t):
    t = min(1, max(0, t))
    return t * t * (3 - 2 * t)


def set_key(owner, prop, value, frame):
    setattr(owner, prop, value)
    owner.keyframe_insert(data_path=prop, frame=frame)


def primitive(group, name, parent, location, material, add, **kwargs):
    add(**kwargs)
    obj = bpy.context.object
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    group.objects.link(obj)
    obj.name, obj.parent, obj.location = name, parent, location
    obj.data.materials.append(material)
    return obj


def block(group, name, parent, center, dimensions, material, bevel=0.008):
    obj = primitive(group, name, parent, center, material, bpy.ops.mesh.primitive_cube_add, size=1)
    obj.data.transform(Matrix.Diagonal((*dimensions, 1)))
    if bevel:
        edges = obj.modifiers.new('Machined edges', 'BEVEL')
        edges.width, edges.segments = bevel, 2
        obj.modifiers.new('Corner normals', 'WEIGHTED_NORMAL')
    return obj


def nozzle(group, name, parent, start, end, radius_start, radius_end, material):
    start, end = Vector(start), Vector(end)
    direction = end - start
    obj = primitive(group, name, parent, (start + end) / 2, material,
                    bpy.ops.mesh.primitive_cone_add, vertices=24, radius1=radius_start,
                    radius2=radius_end, depth=direction.length)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def emission(name, color, strength):
    material = finish(name, color)
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = linear(color)
    shader.inputs['Emission Strength'].default_value = strength
    return material


def fade(material, frame, phase):
    alpha = smooth((phase - 0.03) / 0.13) * (1 - smooth((phase - 0.77) / 0.16))
    socket = material.node_tree.nodes.get('Principled BSDF').inputs['Alpha']
    set_key(socket, 'default_value', alpha, frame)


def duplicate_arm(source, group, station):
    copies = {original: original.copy() for original in source}
    for original, obj in copies.items():
        group.objects.link(obj)
        obj.name = f'{group.name[5:]} | {original.name}'
        obj.animation_data_clear()
        obj.parent = copies.get(original.parent, station)
    links = [copies[bpy.data.objects[f'link_{i}']] for i in range(1, 7)]
    return copies[bpy.data.objects['base_link']], links, copies[bpy.data.objects['tool0']]


def tool_pose(base, links, tool, angles):
    """Evaluate the kit's link transforms and revolute Jacobian in station space."""
    rotation = Matrix.Identity(3)
    position = base.location.copy()
    centers, directions = [], []
    for link, axis, angle in zip(links, JOINT_AXES, angles):
        position = position + rotation @ link.location
        centers.append(position)
        directions.append(rotation @ axis)
        rotation = rotation @ Matrix.Rotation(angle, 3, axis)
    position = position + rotation @ tool.location
    rotation = rotation @ tool.rotation_euler.to_matrix()
    jacobian = np.array([(*axis.cross(position - center), *axis)
                         for center, axis in zip(centers, directions)]).T
    return position, rotation, jacobian


def solve_pose(base, links, tool, seed, target, orientation):
    angles = seed.copy()
    for _ in range(80):
        position, rotation, jacobian = tool_pose(base, links, tool, angles)
        difference = (orientation @ rotation.transposed()).to_quaternion()
        difference.make_compatible(Matrix.Identity(3).to_quaternion())
        axis, angle = difference.to_axis_angle()
        error = np.array([*(target - position), *(axis * angle)])
        if np.linalg.norm(error) < 2e-5:
            return angles
        step = jacobian.T @ np.linalg.solve(jacobian @ jacobian.T + np.eye(6) * 0.0025, error)
        angles = np.clip(angles + np.clip(step, -0.22, 0.22), -JOINT_LIMITS, JOINT_LIMITS)
    raise ValueError(f'Cannot reach {tuple(target)} with residual {np.linalg.norm(error):.4f}')


def progress(phase):
    """Move through the work stroke, then return above the piece."""
    stroke = smooth((phase - 0.06) / 0.64)
    retract = smooth((phase - 0.72) / 0.26)
    height = 0.10 * sin(pi * retract)
    return stroke * (1 - retract), height


def paint_path(t):
    return Vector((1.09, -0.34 + 0.68 * t, BENCH_Z + 0.033))


def cut_path(t):
    angle = tau * t - pi / 2
    return Vector((1.08 + 0.17 * cos(angle), 0.31 * sin(angle), BENCH_Z + 0.028))


def weld_path(t):
    return Vector((1.035, -0.35 + 0.70 * t, BENCH_Z + 0.033))


def build_bench(group, station, kind, metal):
    block(group, 'Fixture | welded frame', station, (1.10, 0, 0.205), (0.52, 0.89, 0.33), metal['ink'])
    block(group, 'Fixture | upper rail', station, (1.10, 0, 0.38), (0.61, 0.94, 0.055), metal['alloy'])
    block(group, 'Fixture | foot', station, (1.10, 0, 0.035), (0.65, 0.98, 0.07), metal['alloy'])
    for y in (-0.28, 0.28):
        block(group, 'Fixture | upright', station, (1.367, y, 0.20), (0.033, 0.082, 0.27), metal['dark'])
    if kind == 'cut':
        for index in range(10):
            block(group, 'Slat bed', station, (1.10, -0.40 + index * 0.089, 0.409),
                  (0.56, 0.022, 0.024), metal['ink'], bevel=0.002)
        block(group, 'Cutting blank', station, (1.08, 0, 0.422), (0.43, 0.79, 0.012), metal['steel'], bevel=0.003)
    else:
        surface = metal['primer'] if kind == 'paint' else metal['steel']
        block(group, 'Workpiece', station, (1.10, 0, 0.417), (0.50, 0.83, 0.026), surface, bevel=0.004)
    if kind == 'weld':
        block(group, 'Upright | fillet joint', station, (1.006, 0, 0.49), (0.054, 0.79, 0.114),
              metal['steel'], bevel=0.003)
    for y in (-0.45, 0.45):
        block(group, 'Fixture clamp', station, (1.14, y, 0.432), (0.26, 0.038, 0.043), metal['dark'])


def build_tool(group, tool, kind, metal):
    nozzle(group, 'ISO flange adapter', tool, (0, 0, 0), (0, 0, 0.035), 0.061, 0.052, metal['ink'])
    if kind == 'paint':
        block(group, 'Spray gun body', tool, (0, 0, 0.072), (0.13, 0.093, 0.078), metal['cobalt'])
        nozzle(group, 'Spray air cap', tool, (0, 0, 0.105), (0, 0, 0.162), 0.041, 0.024, metal['steel'])
        nozzle(group, 'Fluid feed', tool, (0.055, 0, 0.058), (0.11, 0, 0.094), 0.022, 0.017, metal['ink'])
        return 0.162
    if kind == 'cut':
        nozzle(group, 'Plasma torch body', tool, (0, 0, 0.032), (0, 0, 0.127), 0.046, 0.035, metal['ink'])
        nozzle(group, 'Ceramic shield', tool, (0, 0, 0.115), (0, 0, 0.157), 0.038, 0.028, metal['primer'])
        nozzle(group, 'Copper orifice', tool, (0, 0, 0.155), (0, 0, 0.182), 0.027, 0.012, metal['copper'])
        return 0.182
    nozzle(group, 'MIG torch handle', tool, (0, 0, 0.027), (0, 0, 0.103), 0.045, 0.032, metal['ink'])
    nozzle(group, 'Insulated neck', tool, (0, 0, 0.101), (0, 0, 0.168), 0.027, 0.017, metal['dark'])
    nozzle(group, 'Copper gas shroud', tool, (0, 0, 0.162), (0, 0, 0.211), 0.024, 0.023, metal['copper'])
    return 0.211


def process_mark(group, station, kind, path, metal):
    if kind == 'paint':
        material = metal['cobalt'].copy()
        material.name = 'Cured cobalt paint'
        coat = block(group, 'Growing paint stripe', station, (1.09, -0.34, BENCH_Z + 0.033),
                     (0.36, 0.68, 0.002), material, bevel=0)
        return coat, material
    material = metal['ink' if kind == 'cut' else 'bead'].copy()
    material.name = 'Cut kerf' if kind == 'cut' else 'Cooling weld bead'
    mark = line(group, material.name, [path(i / 144) for i in range(145)],
                0.007 if kind == 'cut' else 0.012, material)
    mark.parent = station
    return mark, material


def make_effects(group, station, kind, metal):
    material = metal[{'paint': 'mist', 'cut': 'amber', 'weld': 'spark'}[kind]]
    streaks = []
    for index in range(26 if kind == 'paint' else 20):
        streak = line(group, f'{kind.title()} | streak {index + 1:02}',
                      [(0, 0, 0), (0, 0, 1)], 0.004 if kind == 'paint' else 0.003, material)
        streak.parent = station
        streaks.append(streak)
    core_material = metal['cut_core' if kind == 'cut' else 'weld_core']
    core = line(group, 'Process light', [(0, 0, 0), (0, 0, 1)], 0.011, core_material)
    core.parent = station
    light = bpy.data.lights.new('Arc spill', 'POINT')
    light.color = (0.31, 0.53, 1) if kind == 'weld' else (1, 0.26, 0.045)
    light.shadow_soft_size = 0.065
    lamp = object_in(group, light.name, light)
    lamp.parent = station
    return streaks, core, lamp


def streak_pose(streak, start, end, frame):
    direction = end - start
    set_key(streak, 'location', start, frame)
    set_key(streak, 'rotation_quaternion', direction.to_track_quat('Z', 'Y'), frame)
    set_key(streak, 'scale', (1, 1, direction.length), frame)


def animate_station(group, station, source, kind, path, offset, metal):
    base, links, tool = duplicate_arm(source, group, station)
    build_bench(group, station, kind, metal)
    length = build_tool(group, tool, kind, metal)
    mark, mark_material = process_mark(group, station, kind, path, metal)
    streaks, core, lamp = make_effects(group, station, kind, metal)
    for streak in [*streaks, core]:
        streak.rotation_mode = 'QUATERNION'
    rng = Random(123)
    rays = [(rng.random(), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in streaks]
    tilt = {'paint': -7, 'cut': 0, 'weld': 27}[kind]
    orientation = Matrix.Rotation(radians(tilt), 3, 'Y') @ Matrix.Rotation(pi, 3, 'X')
    axis = orientation @ Vector((0, 0, 1))
    clearance = {'paint': 0.19, 'cut': 0.025, 'weld': 0.037}[kind]
    seed = np.radians((0, 35, 13, 0, -48 + tilt, 0))
    for frame in range(1, FRAMES + 2):
        tick = (frame - 1 + offset) % FRAMES
        phase = tick / FRAMES
        t, lift = progress(phase)
        contact = path(t)
        tip = contact - axis * clearance + Vector((0, 0, lift))
        if frame <= FRAMES:
            seed = solve_pose(base, links, tool, seed, tip - axis * length, orientation)
        if frame == 1:
            opening = seed.copy()
        angles = opening if frame == FRAMES + 1 else seed
        for link, joint_axis, angle in zip(links, JOINT_AXES, angles):
            set_key(link, 'rotation_euler', joint_axis * angle, frame)

        deposit = smooth((phase - 0.06) / 0.64)
        if kind == 'paint':
            set_key(mark, 'location', (1.09, -0.34 + 0.34 * deposit, BENCH_Z + 0.033), frame)
            set_key(mark, 'scale', (1, max(0.0001, deposit), 1), frame)
        else:
            set_key(mark.data, 'bevel_factor_end', deposit, frame)
        fade(mark_material, frame, phase)

        active = 0.065 < phase < 0.70
        for streak, (phase_offset, spread_x, spread_y) in zip(streaks, rays):
            age = (tick / (6 if kind == 'paint' else 11) + phase_offset) % 1
            if kind == 'paint':
                destination = contact + Vector((0.18 * spread_x, 0.028 * spread_y, 0.005))
                start = tip.lerp(destination, age)
                end = tip.lerp(destination, min(1, age + 0.13))
            else:
                spark_origin = path(progress((tick - age * 11) / FRAMES)[0])
                reach = 0.18 if kind == 'cut' else 0.24
                rise = 0.065 if kind == 'cut' else 0.36
                start = spark_origin + Vector((reach * age * (0.8 + 0.55 * spread_x),
                                               reach * age * spread_y, rise * age * (1 - age) + 0.012))
                end = start + Vector((0.032, 0.025 * spread_y, 0.017 * (1 - 2 * age)))
            streak_pose(streak, start, end, frame)
            set_key(streak, 'hide_render', not active, frame)
            set_key(streak, 'hide_viewport', not active, frame)
        arc_active = active and kind != 'paint'
        streak_pose(core, contact, tip, frame)
        set_key(core, 'hide_render', not arc_active, frame)
        set_key(core, 'hide_viewport', not arc_active, frame)
        set_key(lamp, 'location', contact + Vector((0, 0, 0.045)), frame)
        set_key(lamp.data, 'energy', (8 + 3 * cos(tick * 2.2)) if arc_active else 0, frame)
    station['operation'] = kind
    station['cycle_offset_frames'] = offset


def camera_label(group, camera, font, x, name, number, metal):
    for text, size, y, material in (
        (number, 0.105, -0.69, metal['label_blue']),
        (name, 0.173, -0.89, metal['label_ink']),
    ):
        data = bpy.data.curves.new(text, 'FONT')
        data.body, data.font, data.size, data.align_x = text, font, size, 'CENTER'
        data.materials.append(material)
        obj = object_in(group, text, data)
        obj.parent, obj.location = camera, (x, y, -4)


def main(destination, font_path):
    scene = bpy.context.scene
    source_group = bpy.data.collections['01 | AMR CAD and joint hierarchy']
    source = list(source_group.objects)
    studio = bpy.data.collections['02 | Camera and lighting']
    bpy.data.collections.remove(bpy.data.collections['03 | Illustrative joint and floor marks'])
    for obj in list(bpy.data.objects):
        if not obj.users_collection:
            bpy.data.objects.remove(obj, do_unlink=True)

    metal = {
        'ink': finish('Graphite fixture | #1a1a1a', '1a1a1a', 0.27),
        'dark': finish('Blue-black clamps', '394756', 0.45),
        'alloy': finish('Fixture rails', '83909f', 0.46),
        'steel': finish('Brushed steel workpiece', 'a6b1bf', 0.58, 0.31),
        'primer': finish('White primer and ceramic', 'e1e6ec', 0.13),
        'cobalt': finish('Cobalt coating | #1f5fd6', '1f5fd6', 0.15, 0.29),
        'copper': finish('Copper torch tips', 'bc7046', 0.54),
        'bead': finish('Weld bead', '495363', 0.44),
        'mist': emission('Blue paint mist', '2679f3', 0.45),
        'amber': emission('Hot cut ejecta', 'f87920', 1.9),
        'spark': emission('Weld spatter', 'ffba57', 1.4),
        'cut_core': emission('Plasma core', 'ff9c46', 3.8),
        'weld_core': emission('White-blue welding arc', 'abdcff', 4.5),
        'label_ink': emission('Label | #1a1a1a', '1a1a1a', 1),
        'label_blue': emission('Label | #1f5fd6', '1f5fd6', 1),
    }
    for name in ('label_ink', 'label_blue'):
        material = metal[name]
        shader = material.node_tree.nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = material.diffuse_color
        material.node_tree.links.new(shader.outputs[0], material.node_tree.nodes.get('Material Output').inputs[0])

    for index, (name, kind, path, offset) in enumerate((
        ('Painting', 'paint', paint_path, 34),
        ('Cutting', 'cut', cut_path, 27),
        ('Welding', 'weld', weld_path, 42),
    )):
        group = collection(f'{index + 1:02} | {name}')
        station = object_in(group, f'{name} station', None)
        station.location, station.rotation_euler.z = ((index - 1) * 2.26 - 0.23, 0.18, 0), radians(-57)
        station['CAD source'] = 'https://advancedmetalresearch.com/assets/sim/1400/glb/rosie_1400.glb'
        animate_station(group, station, source, kind, path, offset, metal)
    for obj in source:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(source_group)
    studio.name = '04 | Studio'

    camera = scene.camera
    camera.animation_data_clear()
    camera.data.ortho_scale = 6.65
    for frame in range(1, FRAMES + 2):
        phase = tau * (frame - 1) / FRAMES
        camera.location = (0.29 + 0.32 * sin(phase), -7.9, 3.65 + 0.20 * cos(phase))
        aim(camera, (0.23, -0.28, 0.21))
        camera.keyframe_insert('location', frame=frame)
        camera.keyframe_insert('rotation_euler', frame=frame)
    scene.render.resolution_x, scene.render.resolution_y = 1440, 512
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.filepath = '//frames/rosie-tasks_'
    scene.cycles.samples = 10
    scene.render.image_settings.compression = 12
    for obj in list(studio.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
    for name, position, power, width, height in (
        ('Key', (-3.0, -4.0, 5.8), 590, 7.0, 4.4),
        ('Fill', (3.5, -1.8, 4.0), 240, 5.1, 4.0),
        ('Rim', (0, 3.5, 5.1), 660, 7.0, 3.2),
    ):
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.shape, light.size, light.size_y = power, 'RECTANGLE', width, height
        lamp = object_in(studio, name, light)
        lamp.location = position
        aim(lamp, (0, -0.3, 0.4))

    font = bpy.data.fonts.load(str(font_path.resolve()))
    font.pack()
    typography = collection('05 | Station labels')
    for x, title, number in ((-2.26, 'PAINTING', '01'), (0, 'CUTTING', '02'), (2.26, 'WELDING', '03')):
        camera_label(typography, camera, font, x, title, number, metal)
    scene.timeline_markers.clear()
    scene.timeline_markers.new('Process loop starts', frame=1)
    scene.timeline_markers.new('Closure reference', frame=FRAMES + 1)
    scene['Scale note'] = 'Illustrative process models, no engineering scale'
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.resolve()), compress=True)


if __name__ == '__main__':
    main(*(Path(arg) for arg in sys.argv[sys.argv.index('--') + 1:]))
