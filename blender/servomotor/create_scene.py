"""Build an editable, self-contained illustrative brushless servo in Blender 5.1."""

import sys
from math import cos, pi, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector


FIRST, CLOSURE = 1, 217


def linear(hex_color):
    channels = bytes.fromhex(hex_color)
    return tuple((v / 255 / 12.92 if v <= 10 else ((v / 255 + .055) / 1.055) ** 2.4)
                 for v in channels) + (1,)


def metal(name, color, metallic=.45, roughness=.31):
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
    nodes = material.node_tree.nodes
    nodes.clear()
    flat = nodes.new('ShaderNodeEmission')
    flat.inputs['Color'].default_value = material.diffuse_color
    material.node_tree.links.new(flat.outputs[0], nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    return material


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def add(name, data, target, parent=None):
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.parent = parent
    return obj


def ease(obj, field, keys, linear_keys=False):
    for frame, value in keys:
        setattr(obj, field, value)
        obj.keyframe_insert(field, frame=frame)
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    for curve in action.layers[0].strips[0].channelbag(slot).fcurves:
        if curve.data_path == field:
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR' if linear_keys else 'BEZIER'
                key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'


def assembly(name, path):
    target = collection(name)
    root = add(name.split(' | ')[1], None, target)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = .22
    ease(root, 'location', [(FIRST, (0, 0, 0)), *path, (CLOSURE, (0, 0, 0))])
    return target, root


def mesh(name, vertices, faces, material, group, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = add(name, data, *group)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('Machined edges', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        mod.harden_normals = True
        normal = obj.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
        normal.keep_sharp = True
    return obj


def block(name, center, dims, material, group, bevel=.04, twist=0):
    x, y, z = center
    a, b, c = (d / 2 for d in dims)
    vertices = [(-a, -b, -c), (-a, b, -c), (-a, b, c), (-a, -b, c),
                (a, -b, -c), (a, b, -c), (a, b, c), (a, -b, c)]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = mesh(name, vertices, faces, material, group, bevel)
    obj.location = x, y, z
    obj.rotation_euler.x = twist
    return obj


def section(name, profile, material, group, *, count=96, arc=(0, tau), bevel=.014):
    """Revolve a closed axial/radial profile. Radius functions form slots or rounded squares."""
    closed = abs(arc[1] - arc[0] - tau) < 1e-6
    steps = count if closed else count + 1
    vertices = []
    for x, radius in profile:
        for i in range(steps):
            a = arc[0] + (arc[1] - arc[0]) * i / count
            r = radius(a) if callable(radius) else radius
            vertices.append((x, r * cos(a), r * sin(a)))
    faces = []
    for j in range(len(profile)):
        k = (j + 1) % len(profile)
        for i in range(count):
            n = (i + 1) % steps
            faces.append((j * steps + i, k * steps + i, k * steps + n, j * steps + n))
    if not closed:
        faces.extend([tuple(i * steps for i in range(len(profile))),
                      tuple(i * steps + count for i in reversed(range(len(profile))))])
    obj = mesh(name, vertices, faces, material, group, bevel)
    obj.data.set_sharp_from_angle(angle=.63)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def ring(name, x0, x1, outer, inner, material, group, **kwargs):
    return section(name, [(x0, inner), (x1, inner), (x1, outer), (x0, outer)],
                   material, group, **kwargs)


def cylinder(name, center, length, radius, material, group, *, sides=64, axis='X', bevel=.015):
    x, y, z = center
    vertices = [(end * length / 2, radius * cos(tau * i / sides), radius * sin(tau * i / sides))
                for end in (-1, 1) for i in range(sides)]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))]
    faces.extend((i, (i + 1) % sides, sides + (i + 1) % sides, sides + i) for i in range(sides))
    obj = mesh(name, vertices, faces, material, group, bevel)
    obj.location = x, y, z
    if axis == 'Z':
        obj.rotation_euler.y = -pi / 2
    for face in list(obj.data.polygons)[2:]:
        face.use_smooth = True
    return obj


def bore_square(half_width):
    return lambda angle: half_width / (abs(cos(angle)) ** 6 + abs(sin(angle)) ** 6) ** (1 / 6)


def pipe(name, coords, radius, material, group, cyclic=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth, curve.bevel_resolution = radius, 2
    path = curve.splines.new('POLY')
    path.points.add(len(coords) - 1)
    for point, co in zip(path.points, coords):
        point.co = (*co, 1)
    path.use_cyclic_u = cyclic
    curve.materials.append(material)
    return add(name, curve, *group)


def blue_pulse(material, timing):
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = linear('1f5fd6')
    base = tuple(material.diffuse_color)
    for frame, amount in zip(timing, (0, 1, .46, .46, 0)):
        color = shader.inputs['Base Color']
        color.default_value = tuple(a * (1 - amount) + b * amount for a, b in zip(base, linear('1f5fd6')))
        color.keyframe_insert('default_value', frame=frame)
        strength = shader.inputs['Emission Strength']
        strength.default_value = .19 * amount
        strength.keyframe_insert('default_value', frame=frame)


def callout(name, label, anchor, font, camera, graphics, colors, appear):
    ink, blue = colors
    root = add(name + ' callout', None, graphics, camera)
    root.location = *label, -4
    ease(root, 'scale', [(1, (.001,) * 3), (appear, (.001,) * 3), (appear + 8, (1,) * 3),
                         (161, (1,) * 3), (168, (.001,) * 3), (CLOSURE, (.001,) * 3)])
    text = bpy.data.curves.new(name + ' label', 'FONT')
    text.body, text.font, text.size = name.upper(), font, .40
    text.space_character = 1.03
    text.materials.append(ink)
    obj = add(name + ' label', text, graphics, root)
    dx, dy = anchor.x - label[0], anchor.y - label[1]
    obj.location = .20, (-.30 if dy > 0 else .10), .02
    elbow = .28 if dx >= 0 else -.28
    pipe(name + ' leader', [(0, 0, 0), (elbow, 0, 0), (dx, dy, 0)],
         .012, blue, (graphics, root))
    for u, v in [(0, 0), (dx, dy)]:
        points = [(u + .044 * cos(tau * i / 24), v + .044 * sin(tau * i / 24), .005)
                  for i in range(24)]
        pipe(name + ' leader endpoint', points, .012, blue, (graphics, root), cyclic=True)


def main(destination, font_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'Servomotor | torque and feedback'
    studio = collection('00 | Studio')
    # Slide the stator clear of the extrusion before lifting the housing.
    # Reverse the same path on the return so the shell never crosses the windings.
    housing = assembly('01 | Finned housing', [
        (32, (0, 0, 0)), (55, (-1.04, 0, 0)), (73, (-1.04, .92, 2.82)),
        (85, (-.15, .92, 2.82)), (172, (-.15, .92, 2.82)),
        (178, (-1.04, .92, 2.82)), (188, (-1.04, 0, 0)), (198, (0, 0, 0)),
    ])
    stator = assembly('02 | Wound stator', [
        (35, (0, 0, 0)), (54, (1.60, 0, 0)), (73, (1.60, 0, 0)),
        (85, (-.58, 0, 0)), (172, (-.58, 0, 0)), (178, (1.60, 0, 0)),
        (188, (1.60, 0, 0)), (198, (0, 0, 0)),
    ])
    rotor = assembly('03 | Permanent magnet rotor', [
        (56, (0, 0, 0)), (82, (2.19, 0, 0)), (93, (2.19, -.17, .02)),
        (164, (2.19, -.17, .02)), (172, (2.19, 0, 0)), (186, (2.19, 0, 0)), (198, (0, 0, 0)),
    ])
    # Withdraw along the bore before dropping the shaft into its callout position.
    shaft = assembly('04 | Output shaft', [
        (52, (0, 0, 0)), (68, (5.24, 0, 0)), (79, (5.24, -1.48, -1.30)),
        (100, (1.42, -1.48, -1.30)), (168, (1.42, -1.48, -1.30)),
        (177, (5.24, -1.48, -1.30)), (186, (5.24, 0, 0)), (198, (0, 0, 0)),
    ])
    front = assembly('05 | Front bell and bearing', [
        (26, (0, 0, 0)), (42, (2.43, 0, 0)), (55, (2.43, 1.95, 1.05)),
        (82, (2.43, 1.95, 1.05)), (92, (2.43, .34, .06)),
        (168, (2.43, .34, .06)), (177, (2.43, 1.95, 1.05)), (195, (2.43, 1.95, 1.05)),
        (200, (2.43, 0, 0)), (205, (0, 0, 0)),
    ])
    rear = assembly('06 | Rear bell and bearing', [
        (29, (0, 0, 0)), (42, (-.58, 0, 0)), (53, (-1.15, .20, .04)),
        (190, (-1.15, .20, .04)), (194, (-.58, 0, 0)), (198, (0, 0, 0)),
    ])
    encoder = assembly('07 | Absolute encoder', [
        (28, (0, 0, 0)), (35, (-.35, 0, 0)), (56, (-1.57, -.31, .16)),
        (192, (-1.57, -.31, .16)), (196, (-.35, 0, 0)), (201, (0, 0, 0)),
    ])
    cover = assembly('08 | Feedback cover and sockets', [
        (26, (0, 0, 0)), (56, (-3.47, .46, .30)), (190, (-3.47, .46, .30)), (200, (0, 0, 0)),
    ])
    guides = collection('09 | Explanatory callouts')

    graphite = metal('Graphite anodizing | #1a1a1a', '272c32', .42, .34)
    alloy = metal('Bead-blasted aluminum', 'aeb9c4', .57, .33)
    edge = metal('Machined aluminum', 'c9d4de', .65, .25)
    dark = metal('Seals and connector inserts', '171a1f', .10, .55)
    stack = metal('Electrical steel', '666e7b', .63, .34)
    lam = metal('Lamination edges', '3e4753', .57, .38)
    back_iron = metal('Rotor back iron', '535d6b', .62, .33)
    copper = metal('Enameled copper windings', 'b46836', .48, .32)
    copper_light = metal('Copper wire | satin enamel', 'ca824d', .41, .30)
    magnet = metal('NdFeB magnet segments', '64768d', .40, .30)
    magnet_alt = metal('NdFeB magnet segments | alternate pole', 'a0adbf', .48, .28)
    shaft_steel = metal('Ground steel | shaft', 'a7b6c6', .70, .24)
    cobalt = metal('Cobalt anodizing | #1f5fd6', '1f5fd6', .35, .28)
    pcb = metal('Encoder solder mask', '273b50', .24, .39)
    gold = metal('Gold connector contacts', 'c9a362', .57, .27)
    blue_pulse(stack, (70, 86, 101, 170, 182))
    blue_pulse(magnet, (89, 105, 118, 170, 182))
    blue_pulse(magnet_alt, (89, 105, 118, 170, 182))
    blue_pulse(shaft_steel, (110, 126, 137, 170, 183))
    blue_pulse(pcb, (132, 146, 157, 170, 183))

    # Open-ended extrusion and continuous heat sink fins.
    ring('Anodized housing extrusion', -1.38, 1.20, bore_square(1.24), 1.111, graphite, housing, bevel=.031)
    for x0, x1 in [(-1.42, -1.29), (1.10, 1.25)]:
        ring('Housing machined land', x0, x1, bore_square(1.25), 1.115, alloy, housing)
    for side in (-1, 1):
        for h in (-.83, -.55, -.27, .01, .29, .57, .85):
            block('Extruded cooling fin', (-.08, side * 1.275, h), (2.31, .205, .09), graphite, housing, .026)
        for y in (-.83, -.55, -.27, .27, .55, .83):
            block('Extruded cooling fin', (-.08, y, side * 1.27), (2.31, .09, .19), graphite, housing, .024)
    block('Identification plate', (-.08, -.02, 1.304), (1.39, .46, .029), dark, housing, .042)
    for i in range(5):
        block('Identification plate | stripe', (-.50 + i * .22, -.015, 1.321),
              (.115, .18, .012), edge if i else cobalt, housing, .008)

    # A toothed core with 12 slots and individual enamelled coil turns.
    def tooth(angle):
        offset = abs(((angle * 12 / tau + .5) % 1) - .5)
        return .715 + .235 * min(1, max(0, (offset - .19) / .11))

    ring('Slotted stator core', -.97, .82, 1.105, tooth, stack, stator, count=192, bevel=.008)
    for i in range(17):
        x = -.94 + .105 * i
        ring('Electrical steel lamination edge', x, x + .016, 1.109, 1.085,
             lam, stator, count=72, bevel=0)
    for i in range(12):
        center = tau * i / 12
        for turn in range(5):
            radius = .826 + .044 * turn
            width = .205 + .009 * turn
            points = []
            for x, direction in ((.78, 1), (-.93, -1)):
                for j in range(17):
                    a = pi * j / 16
                    angle = center + direction * width * cos(a)
                    points.append((x + direction * (.17 + .032 * turn) * sin(a),
                                   radius * cos(angle), radius * sin(angle)))
            pipe(f'Tooth {i + 1:02d} | coil turn {turn + 1}', points, .020,
                 copper_light if turn % 2 else copper, stator, cyclic=True)

    # Rotor, keyed shaft and encoder disk turn around their common X axis.
    for target, motion in ((rotor, 'Rotor spin'), (shaft, 'Shaft spin')):
        spin = add(motion, None, *target)
        ease(spin, 'rotation_euler', [(1, (0, 0, 0)), (CLOSURE, (tau * 3, 0, 0))], True)
        if target is rotor:
            rotor_spin = (target[0], spin)
        else:
            shaft_spin = (target[0], spin)
    ring('Rotor back iron', -.91, .79, .535, .245, back_iron, rotor_spin)
    for i in range(8):
        a = tau * i / 8
        ring('Curved permanent magnet', -.875, .755, .661, .533,
             magnet if i % 2 else magnet_alt, rotor_spin, count=14,
             arc=(a + .024, a + tau / 8 - .024), bevel=.017)
    for x in (-.99, .79):
        ring('Rotor end band', x, x + .10, .668, .25, edge, rotor_spin)
    ring('Balance ring | witness stripe', .895, .913, .600, .558, cobalt, rotor_spin)
    section('Stepped output shaft', [(-1.91, .022), (2.60, .022), (2.60, .204), (2.56, .248),
                                   (1.16, .248), (1.16, .285), (.91, .285), (.91, .240),
                                   (-1.66, .240), (-1.66, .170), (-1.91, .170)],
            shaft_steel, shaft_spin, bevel=.012)
    cylinder('Output shaft end face', (2.597, 0, 0), .012, .207, shaft_steel, shaft_spin, bevel=.004)
    block('Shaft key', (2.067, 0, .239), (.60, .104, .088), cobalt, shaft_spin, .022)
    block('Shaft end witness mark', (2.605, .080, 0), (.009, .131, .023), cobalt, shaft_spin, .003)

    ring('Front flange | mounting face', 1.22, 1.48, bore_square(1.36), .535, alloy, front, bevel=.040)
    ring('Front flange | locating register', 1.48, 1.585, .795, .382, edge, front, bevel=.025)
    ring('Output shaft seal', 1.56, 1.615, .394, .251, dark, front, bevel=.016)
    ring('Rear end bell', -1.56, -1.40, bore_square(1.218), .492, alloy, rear, bevel=.025)
    for target, x in ((front, 1.34), (rear, -1.52)):
        ring('Bearing outer race', x - .125, x + .125, .525 if target is front else .501, .433, edge, target)
        ring('Bearing inner race', x - .123, x + .123, .325, .249 if target is front else .242, edge, target)
        ring('Bearing cage', x - .09, x + .09, .431, .330, dark, target, bevel=.009)
        for i in range(10):
            a = tau * i / 10
            cylinder('Bearing cage pocket', (x + .101, .378 * cos(a), .378 * sin(a)),
                     .024, .037, alloy, target, sides=20, bevel=.006)
    for y in (-1.035, 1.035):
        for z in (-1.035, 1.035):
            for x, target in ((1.481, front), (-1.564, rear)):
                # Recessed drive faces and collars make the four mounting points legible.
                cylinder('Mounting collar', (x, y, z), .035, .139, edge, target, bevel=.008)
                cylinder('Recessed hex drive', (x + (.022 if x > 0 else -.022), y, z),
                         .010, .073, dark, target, sides=6, bevel=.004)

    spin = add('Encoder target spin', None, *encoder)
    ease(spin, 'rotation_euler', [(1, (0, 0, 0)), (CLOSURE, (tau * 3, 0, 0))], True)
    disc = encoder[0], spin
    ring('Encoder target disk', -1.87, -1.81, .645, .171, edge, disc, bevel=.010)
    for x, side in ((-1.873, -1), (-1.807, 1)):
        ring('Encoder optical track', x - .004, x + .004, .615, .482, dark, disc, bevel=0)
        for i in range(44):
            a = tau * i / 44
            radius = .542
            block('Encoder track division', (x + side * .006, radius * cos(a), radius * sin(a)),
                  (.007, .111 if i % 11 == 0 else .067, .027), cobalt if i % 11 == 0 else edge,
                  disc, .002, a)
    ring('Absolute encoder PCB', -2.025, -1.960, .767, .267, pcb, encoder, bevel=.012)
    for i in range(8):
        a = tau * i / 8
        y, z = .659 * cos(a), .659 * sin(a)
        block('PCB solder pad', (-2.032, y, z), (.016, .088, .053), gold, encoder, .004, a)
    block('Encoder readhead ASIC', (-1.934, -.423, .372), (.055, .225, .180), dark, encoder, .015, -.6)
    block('Feedback processor', (-2.062, -.384, .331), (.068, .246, .204), dark, encoder, .018, -.6)
    for i in range(6):
        block('Feedback processor pin', (-2.065, -.64 + i * .053, .305 + i * .035),
              (.026, .031, .070), gold, encoder, .005, -.6)

    ring('Encoder cover wall', -2.282, -1.55, bore_square(1.217), .975, graphite, cover, bevel=.039)
    ring('Encoder cover gasket', -1.564, -1.528, bore_square(1.225), 1.07, cobalt, cover, bevel=.005)
    block('Encoder cover end panel', (-2.282, 0, 0), (.166, 2.41, 2.41), graphite, cover, .17)
    for y in (-.52, .46):
        block('Connector pedestal', (-1.95, y, 1.219), (.454, .449, .13), alloy, cover, .046)
        cylinder('Mating connector shell', (-1.95, y, 1.435), .36, .207, alloy, cover, axis='Z')
        cylinder('Connector coupling nut', (-1.95, y, 1.55), .13, .245, graphite, cover, axis='Z', sides=12)
        cylinder('Connector insulator', (-1.95, y, 1.618), .044, .154, dark, cover, axis='Z')
        for i in range(5):
            a = tau * i / 5
            cylinder('Connector pin', (-1.95 + .090 * cos(a), y + .090 * sin(a), 1.652),
                     .047, .020, gold, cover, axis='Z', sides=12, bevel=.005)

    camera_data = bpy.data.cameras.new('Orthographic product camera')
    camera_data.type = 'ORTHO'
    camera = add('Orthographic product camera', camera_data, studio)
    scene.camera = camera
    angle = Vector((4.7, -12, 6.6))
    camera.rotation_euler = (-angle).to_track_quat('-Z', 'Y').to_euler()
    home = angle + Vector((.18, 0, .12))
    wide = angle + Vector((-.08, 0, .34))
    withdrawal = wide + Vector((.72, 0, 0))
    shots = [(1, home, 7.2), (24, home, 7.2), (54, wide, 13.4), (58, wide, 13.4),
             (69, withdrawal, 15.9), (82, withdrawal, 15.9), (93, wide, 13.4),
             (169, wide, 13.4), (177, withdrawal, 15.9), (192, withdrawal, 15.9),
             (201, wide, 13.4), (213, home, 7.2), (CLOSURE, home, 7.2)]
    ease(camera, 'location', [(frame, position) for frame, position, _ in shots])
    ease(camera_data, 'ortho_scale', [(frame, zoom) for frame, _, zoom in shots])

    scene.world = bpy.data.worlds.new('Neutral studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .35
    for name, position, power, size, color in (
        ('Key', (2, -5, 7), 1950, 6, (1, .94, .86)),
        ('Front fill', (7, -3, 2), 1100, 5, (.81, .89, 1)),
        ('Rim', (-2, 5, 6), 2400, 5, (.85, .91, 1)),
        ('Bounce', (-7, -2, -.1), 790, 4, (1, .93, .85)),
    ):
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.size, light.color = power, size, color
        obj = add(name, light, studio)
        obj.location = position
        obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()

    scene.frame_set(153)
    bpy.context.view_layer.update()
    inverse = camera.matrix_world.inverted()
    font = bpy.data.fonts.load(str(font_path.resolve()))
    font.pack()
    callout_ink, callout_blue = graphic('Ink | #1a1a1a', '1a1a1a'), graphic('Blue | #1f5fd6', '1f5fd6')
    for name, label, anchor, start in (
        ('01  Stator', (-3.43, -2.32), (-.87, -.94, -.42), 93),
        ('02  Rotor', (3.27, 1.78), (2.13, -.45, .53), 96),
        ('03  Shaft', (1.64, -3.68), (3.64, -1.49, -1.08), 116),
        ('04  Encoder', (-4.26, 3.11), (-3.46, -.55, .57), 139),
    ):
        callout(name, label, inverse @ Vector(anchor), font, camera, guides,
                (callout_ink, callout_blue), start)

    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 2
    scene.render.use_persistent_data = True
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    tree = bpy.data.node_groups.new('Studio paper | #ebebeb', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    layer = tree.nodes.new('CompositorNodeRLayers')
    over = tree.nodes.new('CompositorNodeAlphaOver')
    over.inputs['Background'].default_value = linear('ebebeb')
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(layer.outputs['Image'], over.inputs['Foreground'])
    tree.links.new(over.outputs['Image'], out.inputs['Image'])
    layer.location, over.location, out.location = (-260, 0), (0, 0), (240, 0)

    scene.render.resolution_x, scene.render.resolution_y = 1280, 1024
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/servo_'
    scene.frame_start, scene.frame_end = FIRST, CLOSURE - 1
    for frame, name in ((1, 'Torque at the shaft'), (30, 'Open housing'), (86, 'Energize stator'),
                        (105, 'Rotor follows field'), (126, 'Shaft transmits torque'),
                        (146, 'Encoder reads position'), (173, 'Reassemble'), (CLOSURE, 'Loop closure')):
        scene.timeline_markers.new(name, frame=frame)
    scene.frame_set(FIRST)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.color_type = 'MATERIAL'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.resolve()), compress=True)


if __name__ == '__main__':
    main(*(Path(arg) for arg in sys.argv[sys.argv.index('--') + 1:]))
