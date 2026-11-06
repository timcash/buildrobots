"""Build an editable, self-contained strain-wave reducer animation in Blender 5.1."""

from math import cos, sin, tau
from pathlib import Path
import sys

import bpy
from mathutils import Vector


END = 241
FLEX_TEETH = 200
RING_TEETH = 202
OPEN = 108
CLOSE = 203
BLUE = '1f5fd6'


def linear(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb) + (1,)


def add(name, data, parent=None):
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def animate(owner, path, keys, interpolation='BEZIER'):
    for frame, value in keys:
        setattr(owner, path, value)
        owner.keyframe_insert(data_path=path, frame=frame)
    animation = owner.id_data.animation_data
    full_path = owner.path_from_id(path)
    for layer in animation.action.layers:
        for strip in layer.strips:
            for curve in strip.channelbag(animation.action_slot).fcurves:
                if curve.data_path == full_path:
                    for key in curve.keyframe_points:
                        key.interpolation = interpolation
                        key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'


def metal(name, color, roughness=.32, metallic=.76):
    material = bpy.data.materials.new(name)
    material.diffuse_color = linear(color)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = material.diffuse_color
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return material


def graphic(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = linear(color)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = material.diffuse_color
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs[0], out.inputs['Surface'])
    return material


def mesh(name, vertices, faces, material, parent):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = add(name, data, parent)
    data.materials.append(material)
    return obj


def lathe(name, profile, material, parent, samples=144, wave=0, teeth=False, inward=False):
    """Sweep a closed axial/radial profile. Tooth samples follow each land and flank."""
    pitch = (0, .20, .37, .63, .80)
    heights = (0, 0, 1, 1, 0)
    angles = ([(tau * (i + t) / samples, height) for i in range(samples)
               for t, height in zip(pitch, heights)] if teeth else
              [(tau * i / samples, 0) for i in range(samples)])
    count = len(angles)
    vertices = []
    amplitudes = []
    for x, radius, tooth_depth in profile:
        # The cup distorts most at the open rim and stays round at its diaphragm.
        amplitude = wave * max(0, min(1, (.36 - x) / .54))
        for angle, height in angles:
            r = radius + tooth_depth * height
            vertices.append((x, r * cos(angle), r * sin(angle)))
            amplitudes.append((angle, amplitude))
    faces = [(row * count + i, row * count + (i + 1) % count,
              ((row + 1) % len(profile)) * count + (i + 1) % count,
              ((row + 1) % len(profile)) * count + i)
             for row in range(len(profile)) for i in range(count)]
    if inward:
        faces = [face[::-1] for face in faces]
    obj = mesh(name, vertices, faces, material, parent)
    for face in obj.data.polygons:
        row = face.index // count
        face.use_smooth = profile[row][0] != profile[(row + 1) % len(profile)][0] and not teeth
    if wave:
        obj.shape_key_add(name='Round / unloaded')
        for label, lobe in (('Cosine lobe', cos), ('Sine lobe', sin)):
            shape = obj.shape_key_add(name=label)
            shape.slider_min = -1
            for point, (x, y, z), (a, strength) in zip(shape.data, vertices, amplitudes):
                radius = strength * lobe(2 * a)
                point.co = (x, y + radius * cos(a), z + radius * sin(a))
    return obj


def ring(name, section, material, parent, **kwargs):
    return lathe(name, [(x, radius, 0) for x, radius in section], material, parent, **kwargs)


def ellipsoid(obj, amount):
    for vertex in obj.data.vertices:
        _, y, z = vertex.co
        scale = 1 + amount * (y * y - z * z) / (y * y + z * z)
        vertex.co.y *= scale
        vertex.co.z *= scale


def socket(name, x, y, z, size, depth, material, parent):
    # A dark six-sided recess inside a chamfered fastener head.
    obj = ring(name, [(x, size * .53), (x, size * .87), (x + depth * .18, size),
                      (x + depth, size), (x + depth, size * .05),
                      (x + depth * .64, size * .05), (x + depth * .64, size * .53)],
               material, parent, samples=6)
    obj.location.y, obj.location.z = y, z
    obj.data.materials.append(bpy.data.materials['Socket recess'])
    for face in obj.data.polygons:
        if face.index // 6 in (4, 5, 6):
            face.material_index = 1


def arc(name, start, end, radius, thickness, x, material, parent):
    vertices = [(x, r * cos(a), r * sin(a)) for i in range(33)
                for a in [start + (end - start) * i / 32]
                for r in (radius, radius + thickness)]
    return mesh(name, vertices, [(i, i + 1, i + 3, i + 2) for i in range(0, 64, 2)], material, parent)


def text_line(parent, font, material, label, size, x, y):
    data = bpy.data.curves.new(label, 'FONT')
    data.font, data.body, data.size = font, label, size
    data.materials.append(material)
    obj = add(label, data, parent)
    obj.location = (x, y, 0)


def visibility(obj, spans):
    keys = [(1, True)]
    for first, last in spans:
        keys.extend(((first, False), (last + 1, True)))
    # Both flags make the editorial overlays editable in the viewport and deterministic in renders.
    for path in ('hide_render', 'hide_viewport'):
        animate(obj, path, sorted(dict(keys).items()), 'CONSTANT')


def main(destination, font_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    studio = add('Studio and camera', None)
    wave = add('01 | Wave generator — input', None)
    fixed = add('02 | Circular spline — stationary', None)
    flex = add('03 | Flexspline — 200 external teeth', None)
    output = add('04 | Output flange and bearing', None)
    cam = add('Input spin', None, wave)
    cup = add('Flexspline spin', None, flex)
    flange = add('Output spin', None, output)
    body = metal('Machined alloy', '80919f', .30, .62)
    edge = metal('Polished races and fasteners', 'bbc5ca', .22, .75)
    dark = metal('Phosphate steel', '404b55', .35, .58)
    metal('Socket recess', '20282e', .48, .35)
    wave_mat = metal('Highlight | elliptical cam', '778b9d')
    ring_mat = metal('Highlight | fixed circular spline', '7b8993')
    flex_mat = metal('Highlight | thin flexspline', '657d91')
    output_mat = metal('Highlight | output flange', '8295a3')

    ellipse = ring('Elliptical cam', [(-.57, .36), (-.57, .97), (-.52, 1.04),
                   (-.17, 1.04), (-.14, .99), (-.14, .36)], wave_mat, cam)
    ellipsoid(ellipse, .054)
    for name, inner, outer, material in (
        ('Inner race', 1.02, 1.089, dark), ('Flexible outer race', 1.164, 1.233, edge),
    ):
        race = ring(name, [(-.515, inner), (-.515, outer - .014), (-.498, outer),
                    (-.205, outer), (-.184, outer - .014), (-.184, inner)], material, cam)
        ellipsoid(race, .054)
    # The exposed rolling elements make the thin bearing legible in the exploded view.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=.047)
    original = bpy.context.object
    ball_mesh = original.data
    ball_mesh.materials.append(edge)
    for face in ball_mesh.polygons:
        face.use_smooth = True
    for i in range(40):
        a = tau * i / 40
        r = 1.128 * (1 + .054 * cos(2 * a))
        ball = add(f'Wave bearing ball {i + 1:02}', ball_mesh, cam)
        ball.location = (-.49, r * cos(a), r * sin(a))
    bpy.data.objects.remove(original, do_unlink=True)
    ring('Hollow input coupling', [(-.94, .215), (-.94, .343), (-.91, .382),
         (-.69, .382), (-.67, .497), (-.57, .497), (-.54, .465), (-.54, .215)], edge, cam)
    for a in (0, tau / 2):
        arc('Input phase index', a - .10, a + .10, .73, .055, -.574, dark, cam)

    ring('Circular spline body', [(-.72, 1.439), (-.72, 1.804), (-.66, 1.886),
         (-.52, 1.92), (-.28, 1.92), (-.24, 1.82), (.28, 1.82), (.40, 1.70),
         (.40, 1.48), (-.31, 1.48), (-.34, 1.432), (-.69, 1.432)], ring_mat, fixed)
    lathe('202 internal teeth', [(-.68, 1.445, -.027), (-.64, 1.437, -.058),
          (-.385, 1.437, -.058), (-.346, 1.445, -.027), (-.346, 1.466, 0),
          (-.68, 1.466, 0)], edge, fixed, RING_TEETH, teeth=True, inward=True)
    ring('Face register', [(-.727, 1.49), (-.727, 1.521), (-.72, 1.521),
         (-.72, 1.49)], dark, fixed)
    ring('Housing seam', [(-.23, 1.821), (-.23, 1.835), (-.19, 1.835),
         (-.19, 1.821)], dark, fixed)
    for i in range(12):
        a = tau * i / 12
        socket(f'Housing socket {i + 1:02}', -.77, 1.689 * cos(a), 1.689 * sin(a), .102, .08, edge, fixed)

    wall = ring('Thin cup and diaphragm', [(-.64, 1.234), (-.64, 1.291), (-.38, 1.291),
                (-.29, 1.261), (.24, 1.254), (.34, 1.216), (.43, 1.10), (.48, .87),
                (.48, .63), (.59, .63), (.61, .59), (.61, .34), (.32, .34),
                (.32, 1.04), (.28, 1.145), (.21, 1.192), (-.05, 1.203), (-.17, 1.234)],
                flex_mat, cup, wave=.067)
    teeth = lathe('200 external teeth', [(-.64, 1.284, .024), (-.606, 1.294, .052),
                  (-.413, 1.294, .052), (-.38, 1.283, .028), (-.38, 1.277, 0),
                  (-.64, 1.277, 0)], flex_mat, cup, FLEX_TEETH, wave=.067, teeth=True)

    ring('Fixed cross-roller outer race', [(.42, 1.343), (.42, 1.62), (.47, 1.68),
         (.76, 1.68), (.82, 1.61), (.82, 1.343)], dark, output)
    ring('Output flange and inner race', [(.46, .45), (.46, 1.265), (.51, 1.337),
         (.77, 1.337), (.83, 1.30), (.89, 1.223), (1.00, 1.20), (1.04, 1.16),
         (1.04, .32), (.70, .32), (.70, .45)], output_mat, flange)
    ring('Ground mounting face', [(1.038, .52), (1.038, 1.125), (1.051, 1.113),
         (1.051, .52)], edge, flange)
    ring('Output pilot face', [(.438, .63), (.438, .91), (.46, .935), (.46, .63)], edge, flange)
    for i in range(10):
        a = tau * i / 10
        socket(f'Output socket {i + 1:02}', .386, 1.10 * cos(a), 1.10 * sin(a), .102, .077, edge, flange)
    for i in range(32):
        a = tau * i / 32
        roller = ring(f'Crossed roller {i + 1:02}', [(-.06, .006), (-.06, .049),
                      (.06, .049), (.06, .006)], body, output, samples=12)
        roller.location = (.43, 1.345 * cos(a), 1.345 * sin(a))
        axis = Vector((1, (-1) ** i * cos(a), (-1) ** i * sin(a)))
        roller.rotation_euler = Vector((1, 0, 0)).rotation_difference(axis).to_euler()

    for part, offset in ((wave, -4.13), (fixed, -1.46), (flex, 1.40), (output, 3.86)):
        animate(part, 'location', [(f, (x, 0, 0)) for f, x in
                                   ((1, 0), (72, 0), (OPEN, offset), (CLOSE, offset), (235, 0), (END, 0))])

    def phase(frame):
        return tau * min(1, (frame - 1) / 66)

    def driven(frame):
        # Counter-rotate at the actual illustrative ratio while engaged. Reset the
        # tiny phase offset once the separated components are free of the fixed ring.
        reset = max(0, min(1, (frame - 109) / 24))
        reset = reset * reset * (3 - 2 * reset)
        return -phase(frame) * (RING_TEETH - FLEX_TEETH) / FLEX_TEETH * (1 - reset)

    animate(cam, 'rotation_euler', [(1, (0, 0, 0)), (67, (tau, 0, 0)), (END, (tau, 0, 0))], 'LINEAR')
    for part in (cup, flange):
        animate(part, 'rotation_euler', [(f, (driven(f), 0, 0)) for f in range(1, END + 1)], 'LINEAR')
    contact = {}
    for frame in range(1, END + 1):
        scene.frame_set(frame)
        gap = flex.location.x - wave.location.x
        load = max(0, min(1, (.55 - gap) / .34))
        contact[frame] = load * load * (3 - 2 * load)
    for obj in (wall, teeth):
        for name, lobe in (('Cosine lobe', cos), ('Sine lobe', sin)):
            animate(obj.data.shape_keys.key_blocks[name], 'value',
                    [(f, load * lobe(2 * (phase(f) - driven(f)))) for f, load in contact.items()], 'LINEAR')

    blue = graphic('Cobalt | #1f5fd6', BLUE)
    ink = graphic('Ink | #1a1a1a', '1a1a1a')
    marks = add('Opposed engagement zones', None, fixed)
    animate(marks, 'rotation_euler', [(1, (0, 0, 0)), (67, (tau, 0, 0)), (END, (tau, 0, 0))], 'LINEAR')
    for angle in (0, tau / 2):
        marker = arc('Moving mesh zone', angle - .24, angle + .24, 1.47, .055, -.74, blue, marks)
        visibility(marker, [(1, 69), (232, END)])

    for material, lo, peak, hi in ((wave_mat, 100, 111, 130), (ring_mat, 124, 137, 155),
                                   (flex_mat, 148, 160, 179), (output_mat, 173, 185, 208)):
        base = material.node_tree.nodes['Principled BSDF'].inputs['Base Color']
        original = tuple(base.default_value)
        animate(base, 'default_value', [(1, original), (lo, original), (peak, linear(BLUE)),
                                         (peak + 9, linear(BLUE)), (hi, original), (END, original)])

    camera_data = bpy.data.cameras.new('Orthographic camera')
    camera_data.type = 'ORTHO'
    camera = add('Orthographic camera', camera_data, studio)
    scene.camera = camera
    home = Vector((-11, -11, 7))
    wide = Vector((-7.4, -14, 8.6))
    wide_end = Vector((-6.6, -14, 7.4))
    shots = [(1, home, 5.98), (70, home, 5.98), (OPEN, wide, 11.45),
             (CLOSE, wide_end, 11.55), (235, home, 5.98), (END, home, 5.98)]
    poses = [(f, direction + Vector((0, 0, -.07 * zoom)),
              (-direction).to_track_quat('-Z', 'Y').to_euler(), zoom) for f, direction, zoom in shots]
    animate(camera, 'location', [(f, pos) for f, pos, _, _ in poses])
    animate(camera, 'rotation_euler', [(f, rotation) for f, _, rotation, _ in poses])
    animate(camera_data, 'ortho_scale', [(f, zoom) for f, _, _, zoom in poses])

    font = bpy.data.fonts.load(str(font_path.resolve()))
    font.pack()
    overlay = add('Camera graphics', None, camera)
    overlay.location.z = -10
    animate(overlay, 'scale', [(f, (zoom, zoom, zoom)) for f, _, zoom in shots])
    for index, title, detail, spans in (
        ('IN MOTION', 'Two moving mesh zones', 'One input turn moves the output back two teeth.', [(1, 73), (230, END)]),
        ('01  /  INPUT', 'Wave generator', 'An elliptical cam turns inside a thin bearing.', [(74, 125)]),
        ('02  /  FIXED', 'Circular spline', 'The rigid ring holds 202 internal teeth.', [(126, 149)]),
        ('03  /  FLEXIBLE', 'Flexspline', 'The thin cup flexes at its 200-tooth rim.', [(150, 174)]),
        ('04  /  OUTPUT', 'Output flange', 'The flange turns with the cup at 1/100 input speed.', [(175, 229)]),
    ):
        group = add(index, None, overlay)
        text_line(group, font, blue, index, .026, -.456, -.251)
        text_line(group, font, ink, title, .049, -.457, -.309)
        text_line(group, font, ink, detail, .028, -.456, -.353)
        for child in group.children:
            visibility(child, spans)

    world = bpy.data.worlds.new('Studio ambient')
    world.use_nodes = True
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .40
    scene.world = world
    for name, location, power, size in (
        ('Key softbox', (-4, -6, 9), 1900, 6), ('Face fill', (-8, -2, 3), 1400, 5),
        ('Back strip', (4, 5, 7), 2900, 5), ('Lower bounce', (1, -4, -5), 950, 5),
    ):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = power, size
        obj = add(name, data, studio)
        obj.location = location
        obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()

    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 3
    scene.render.use_persistent_data = True
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    tree = bpy.data.node_groups.new('Paper | #ebebeb', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    layers = tree.nodes.new('CompositorNodeRLayers')
    over = tree.nodes.new('CompositorNodeAlphaOver')
    over.inputs['Background'].default_value = linear('ebebeb')
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(layers.outputs['Image'], over.inputs['Foreground'])
    tree.links.new(over.outputs['Image'], out.inputs['Image'])
    layers.location, over.location, out.location = (-250, 0), (0, 0), (240, 0)

    scene.render.resolution_x, scene.render.resolution_y = 1280, 1024
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/reducer_'
    scene.frame_start, scene.frame_end = 1, END - 1
    for frame, label in ((1, 'One input turn'), (73, 'Separate assemblies'), (111, 'Wave generator'),
                         (137, 'Circular spline'), (160, 'Flexspline'), (185, 'Output flange'),
                         (204, 'Reassemble'), (END, 'Loop boundary')):
        scene.timeline_markers.new(label, frame=frame)
    scene.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.color_type = 'MATERIAL'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.resolve()), compress=True)


if __name__ == '__main__':
    main(*(Path(arg) for arg in sys.argv[sys.argv.index('--') + 1:]))
