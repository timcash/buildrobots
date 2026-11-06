"""Build the machine-vision camera and its native Blender animation."""

import sys
from math import cos, pi, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector

END = 241


def linear(hex_color):
    channels = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (*[v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels], 1)


def material(name, color, metal=0, roughness=.36, coat=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = linear(color)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Coat Weight'].default_value = coat
    return mat


def pulse(mat, keys, color='1f5fd6'):
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = linear(color)
    intensity = shader.inputs['Emission Strength']
    for frame, value in keys:
        intensity.default_value = value
        intensity.keyframe_insert('default_value', frame=frame)


def empty(name, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.empty_display_size = .16
    return obj


def finish(obj, name, mat, parent, bevel=0):
    obj.name = name
    obj.parent = parent
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('Machined edges', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        obj.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, xyz, dimensions, mat, parent, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    for vertex in obj.data.vertices:
        for axis, length in enumerate(dimensions):
            vertex.co[axis] *= length
    return finish(obj, name, mat, parent, bevel)


def lathe(name, profile, mat, parent, yz=(0, 0), sides=80, soften=True):
    """Revolve a closed (axial, radial) profile around +X."""
    vertices = [(x, yz[0] + r * cos(i * tau / sides), yz[1] + r * sin(i * tau / sides))
                for x, r in profile for i in range(sides)]
    faces = []
    for row in range(len(profile)):
        a, b = row * sides, ((row + 1) % len(profile)) * sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a + i, a + j, b + j, b + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if soften:
        for face in mesh.polygons:
            face.use_smooth = True
    return finish(obj, name, mat, parent)


def ring(name, center, depth, outer, inner, mat, parent, yz=(0, 0), sides=80):
    x, y = center - depth / 2, center + depth / 2
    b = min(.024, depth / 4, (outer - inner) / 3)
    profile = [(x, inner + b), (x, outer - b), (x + b, outer), (y - b, outer),
               (y, outer - b), (y, inner + b), (y - b, inner), (x + b, inner)]
    return lathe(name, profile, mat, parent, yz, sides, soften=sides > 12)


def optic(name, x, radius, front_sag, rear_sag, mat, parent):
    # Sample both polished faces. Leave a tiny center ring to avoid collapsed faces.
    radii = [.001, *[radius * i / 14 for i in range(1, 15)]]
    profile = [(x - .052 - rear_sag * (1 - (r / radius) ** 2), r) for r in radii]
    profile += [(x + .052 + front_sag * (1 - (r / radius) ** 2), r) for r in reversed(radii)]
    return lathe(name, profile, mat, parent)


def keys(obj, path, values):
    for frame, value in values:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def separate(obj, delta, start, open_frame, close_frame, seated):
    keys(obj, 'location', [(1, (0, 0, 0)), (start, (0, 0, 0)),
                           (open_frame, delta), (close_frame, delta),
                           (seated, (0, 0, 0)), (END, (0, 0, 0))])


def trace(name, points, mat, parent, width=.009):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth, curve.bevel_resolution = width, 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, parent)


def label(name, body, xyz, size, font, mat, parent):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body, curve.size, curve.font = body, size, font
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = xyz
    return finish(obj, name, mat, parent)


def body_text(name, body, xyz, size, font, mat, parent):
    obj = label(name, body, xyz, size, font, mat, parent)
    obj.rotation_euler = (pi / 2, 0, pi)
    return obj


def main(destination, font_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'Machine vision | Capture to Ethernet'
    font = bpy.data.fonts.load(str(font_path.resolve()))
    ink = material('Black anodized aluminum', '252c35', .64, .32)
    shell = material('Graphite heat sink', '3b444d', .65, .34)
    steel = material('Bead-blasted hardware', 'b6c3cd', .73, .27)
    rubber = material('Matte gasket', '191e23', 0, .68)
    gold = material('Gold contacts', 'ba9355', .66)
    solder = material('Dark teal solder mask', '204d4b', .17)
    ceramic = material('Sensor ceramic package', '9c895f', .37)
    glass = material('AR-coated lens glass', '244d69', .29, .16, .65)
    glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value = .34
    filter_mat = material('IR-cut coating', '552b60', .47, .21, .6)
    sensor_mat = material('CMOS photosites', '594474', .44, .24, .55)
    board_signal = material('PCB signal path', '608573', .42)
    led = material('Strobe emitters', 'c6d4e6', .17, .22)
    status = material('Ethernet status', '2a633f')
    white = material('Silkscreen', 'dbe3ed')
    blue = material('Highlight blue', '1f5fd6', 0, .38)
    text_ink = material('Ink', '1a1a1a')
    for mat in (blue, text_ink, white):
        pulse(mat, [(1, 1)], '1f5fd6' if mat == blue else '1a1a1a' if mat == text_ink else 'dbe3ed')
        mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0, 0, 0, 1)

    assembly = empty('Camera | optical axis +X')
    housing = empty('01 | split housing and heat sink', assembly)
    lid = empty('Heat sink cover', housing)
    box('Top cover', (-.29, 0, 1.18), (2.54, 2.56, .25), shell, lid, .055)
    box('Near side cover', (-.29, 1.16, .062), (2.54, .23, 2.28), shell, lid, .05)
    for i in range(9):
        box('Extruded cooling fin', (-.30, -.96 + .24 * i, 1.37), (2.38, .087, .24), ink, lid, .026)
    for z in (-.61, -.49, -.37):
        box('Recessed side detail', (-.31, 1.284, z), (2.21, .019, .037), ink, lid, .006)
    body_text('Housing mark', 'MV / 03', (.49, 1.282, .48), .24, font, white, lid)
    body_text('Housing specification', 'GLOBAL SHUTTER', (.48, 1.282, .25), .106, font, white, lid)
    base = empty('Lower chassis', housing)
    box('Chassis base', (-.29, 0, -1.17), (2.54, 2.56, .24), ink, base, .055)
    box('Far side wall', (-.29, -1.16, -.02), (2.54, .23, 2.20), shell, base, .04)
    for y in (-.91, .91):
        box('Board guide rail', (-.29, y, -.99), (2.29, .075, .11), steel, base)
        box('Mounting foot', (-.29, y, -1.33), (1.68, .35, .13), steel, base)
    for y in (-.91, .91):
        for x in (-1.20, .61):
            screw = ring('Foot counterbore', 0, .06, .107, .052, ink, base, sides=48)
            screw.rotation_euler.y = pi / 2
            screw.location = (x, y, -1.408)

    mount = empty('02 | C-mount flange and filter', assembly)
    for z in (-1.10, 1.10):
        box('Flange crossmember', (.99, 0, z), (.23, 2.53, .34), shell, mount, .052)
    for y in (-1.10, 1.10):
        box('Flange upright', (.99, y, 0), (.23, .34, 1.92), shell, mount, .052)
        for z in (-1.04, 1.04):
            ring('Flange fastener', 1.12, .08, .115, .043, steel, mount, (y, z), sides=12)
    ring('Flange throat', 1.04, .31, 1.077, .81, ink, mount)
    for i in range(5):
        ring('C-mount thread crest', 1.18 + .026 * i, .019, .908, .87, steel, mount)
    optic('IR-cut window', 1.11, .805, 0, 0, filter_mat, mount)

    barrel = empty('03 | focus and aperture barrel', assembly)
    profile = [(1.27, .842), (1.27, .928), (1.37, .98), (1.87, .98), (1.91, 1.06),
               (2.53, 1.06), (2.57, 1.00), (2.87, 1.00), (2.91, 1.11),
               (3.45, 1.11), (3.51, 1.04), (3.51, .891), (3.25, .88), (1.43, .83)]
    lathe('Stepped optical barrel', profile, ink, barrel)
    for start, stop, radius in ((1.96, 2.50, 1.065), (2.96, 3.39, 1.115)):
        for i in range(54):
            angle = i * tau / 54
            grip = box('Axial grip flute', ((start + stop) / 2, radius * cos(angle), radius * sin(angle)),
                       (stop - start, .067, .047), rubber, barrel, .012)
            grip.rotation_euler.x = angle
    ring('Focus index ring', 2.62, .046, 1.013, .96, steel, barrel)
    ring('Blue identification band', 2.69, .064, 1.014, .96, blue, barrel)
    for i in range(11):
        angle = (i - 5) * .15
        mark = box('Focus scale tick', (2.77, 1.001 * cos(angle), 1.001 * sin(angle)),
                   (.09 if i % 5 == 0 else .045, .012, .02), white, barrel, .003)
        mark.rotation_euler.x = angle

    optics = []
    for index, (x, radius, sag) in enumerate(((1.53, .789, -.035), (1.94, .81, .10),
                                             (2.49, .825, .145), (3.24, .854, .19)), 1):
        cell = empty(f'04.{index} | lens element', assembly)
        ring('Retaining cell', x, .113, radius + .055, radius - .016, steel, cell)
        optic('Polished optical element', x, radius, sag, .062, glass, cell)
        optics.append(cell)

    strobe = empty('05 | annular strobe', assembly)
    ring('Strobe enclosure', 3.22, .31, 1.43, 1.12, shell, strobe)
    ring('LED faceplate', 3.392, .075, 1.405, 1.136, ink, strobe)
    for i in range(16):
        angle = i * tau / 16
        yz = (1.27 * cos(angle), 1.27 * sin(angle))
        ring('LED recess', 3.435, .045, .099, .074, steel, strobe, yz, sides=24)
        optic('LED diffuser', 3.436, .073, .022, 0, led, strobe).location = (0, *yz)

    sensor = empty('06 | CMOS sensor board', assembly)
    box('Sensor PCB', (.63, 0, 0), (.11, 2.01, 2.03), solder, sensor)
    box('Ceramic package', (.76, 0, 0), (.16, 1.39, 1.16), ceramic, sensor, .046)
    box('CMOS die', (.859, 0, 0), (.05, 1.08, .81), sensor_mat, sensor, .02)
    for row in range(12):
        z = (row - 5.5) * .060
        trace('Readout row', [(.888, -.48, z), (.888, .48, z)], sensor_mat, sensor, .004)
    for y in (-.83, .83):
        for z in (-.84, .84):
            ring('Sensor mounting pad', .692, .026, .091, .042, gold, sensor, (y, z), sides=24)
    for i in range(14):
        for side in (-1, 1):
            box('Wire-bond contact', (.852, side * .63, (i - 6.5) * .071),
                (.035, .105, .026), gold, sensor, .004)

    processor = empty('07 | image processing board', assembly)
    interface = empty('08 | Ethernet and trigger board', assembly)
    for group, x in ((processor, -.38), (interface, -1.01)):
        box('Multilayer PCB', (x, 0, 0), (.123, 2.02, 2.03), solder, group)
        for y in (-.86, .86):
            for z in (-.86, .86):
                ring('Board mounting pad', x + .068, .026, .094, .044, gold, group, (y, z), sides=24)
        for i in range(8):
            z = -.30 + .088 * i
            trace('Signal trace', [(x + .064, .28, z), (x + .064, .53, z),
                                  (x + .064, .72, z + .17), (x + .064, .87, z + .17)],
                  board_signal, group)
        for i in range(7):
            z = -.62 + .196 * i
            box('Surface-mount package', (x + .085, -.69, z), (.062, .18, .093), rubber, group, .011)
            for y in (-.782, -.598):
                box('Solder fillet', (x + .069, y, z), (.047, .045, .071), steel, group, .007)
    box('Image processor', (-.24, -.05, .09), (.17, .83, .82), ink, processor, .035)
    box('Processor heat spreader', (-.14, -.05, .09), (.055, .65, .64), steel, processor)
    for i in range(10):
        z = -.27 + .081 * i
        for y in (-.49, .39):
            box('Processor bond pad', (-.298, y, z), (.028, .115, .027), gold, processor, .005)
    box('PHY and PoE controller', (-.885, .28, -.06), (.125, .68, .61), ink, interface)
    for i in range(4):
        box('PoE magnetics', (-.887, -.32 + .22 * i, .63), (.13, .15, .20), steel, interface)

    rear = empty('09 | rear plate and ports', assembly)
    box('Rear endplate', (-1.61, 0, 0), (.20, 2.55, 2.51), shell, rear, .067)
    box('Endplate gasket', (-1.49, 0, 0), (.055, 2.47, 2.42), rubber, rear)
    for y in (-1.02, 1.02):
        for z in (-1.01, 1.01):
            ring('Rear fastener', -1.724, .07, .099, .039, steel, rear, (y, z), sides=12)
    for y in (.02, .91):
        box('Shielded RJ45 side', (-1.83, y, .29), (.33, .084, .68), steel, rear)
    for z in (.0, .58):
        box('Shielded RJ45 flange', (-1.83, .465, z), (.33, .89, .086), steel, rear)
    box('Recessed jack insert', (-1.74, .465, .29), (.14, .79, .52), rubber, rear)
    for i in range(8):
        box('Ethernet spring contact', (-1.87, .20 + .074 * i, .43), (.15, .025, .035), gold, rear, .005)
    ring('Trigger connector shell', -1.87, .38, .328, .236, steel, rear, (-.61, .19))
    optic('Trigger connector insert', -1.82, .227, 0, 0, rubber, rear).location = (0, -.61, .19)
    for i in range(6):
        angle = i * tau / 6
        box('Trigger contact', (-1.941, -.61 + .14 * cos(angle), .19 + .14 * sin(angle)),
            (.17, .038, .038), gold, rear, .008)
    box('Link indicator', (-1.725, .71, -.28), (.036, .19, .071), status, rear)

    target = empty('Inspection target | machined part')
    ring('Inspection coupon', 0, .24, .57, .27, steel, target)
    for i in range(6):
        angle = i * tau / 6
        ring('Inspection feature', -.138, .031, .063, .029, ink, target,
             (.41 * cos(angle), .41 * sin(angle)), sides=24)
    keys(target, 'location', [(1, (5.34, -.93, -.30)), (11, (5.34, -.62, -.08)),
                              (25, (5.34, .04, .0)), (39, (5.34, .86, -.02)),
                              (55, (5.34, 1.95, -1.95)), (226, (5.34, -.93, -.30)),
                              (END, (5.34, -.93, -.30))])
    keys(target, 'scale', [(1, (1, 1, 1)), (42, (1, 1, 1)), (56, (.001,) * 3),
                           (225, (.001,) * 3), (END, (1, 1, 1))])
    bpy.ops.object.light_add(type='POINT', location=(4.04, 0, 0))
    flash = bpy.context.object
    flash.name = 'Inspection flash on target'
    flash.data.color, flash.data.shadow_soft_size = (.25, .55, 1), .57
    for frame, value in ((1, 0), (19, 0), (24, 340), (28, 160), (34, 0), (END, 0)):
        flash.data.energy = value
        flash.data.keyframe_insert('energy', frame=frame)

    keys(strobe, 'location', [(1, (0, 0, 0)), (39, (0, 0, 0)),
                              (79, (3.62, 0, 0)), (101, (3.62, 0, -.49)),
                              (177, (3.62, 0, -.49)), (191, (3.62, 0, 0)),
                              (228, (0, 0, 0)), (END, (0, 0, 0))])
    keys(barrel, 'location', [(1, (0, 0, 0)), (44, (0, 0, 0)),
                              (81, (2.48, 0, 0)), (106, (2.48, 0, 2.17)),
                              (181, (2.48, 0, 2.17)), (200, (2.48, 0, 0)),
                              (229, (0, 0, 0)), (END, (0, 0, 0))])
    for cell, offset in zip(optics, (.91, 1.37, 1.82, 2.45)):
        separate(cell, (offset, 0, 0), 96, 120, 168, 190)
    separate(lid, (-.40, -.21, 2.06), 51, 104, 179, 226)
    separate(base, (-.32, -.13, -.82), 51, 104, 179, 226)
    separate(mount, (.45, 0, 0), 57, 105, 176, 219)
    separate(sensor, (-.52, .11, .07), 65, 108, 176, 216)
    separate(processor, (-1.70, .20, .10), 69, 114, 181, 216)
    separate(interface, (-2.82, .31, .10), 63, 111, 183, 222)
    separate(rear, (-4.12, .42, .10), 56, 107, 188, 227)

    pulse(led, [(1, 0), (19, 0), (24, 3.4), (28, 1.6), (36, 0), (END, 0)])
    pulse(glass, [(1, .025), (89, .025), (110, .76), (124, .76), (139, .025), (END, .025)])
    pulse(sensor_mat, [(1, 0), (122, 0), (136, 1.4), (148, 1.4), (159, 0), (END, 0)])
    pulse(board_signal, [(1, 0), (148, 0), (162, 1.8), (174, 1.8), (191, 0), (END, 0)])
    pulse(status, [(1, .02), (27, .02), (34, 1.1), (42, .02),
                   (160, .02), (171, 1.6), (183, .02), (END, .02)])

    camera_data = bpy.data.cameras.new('Product orthographic')
    camera = bpy.data.objects.new('Product camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    for frame, azimuth, height, center, scale in (
        (1, .66, .29, 1.49, 8.7), (35, .61, .25, 1.60, 8.8),
        (85, .47, .23, .61, 13.6), (118, .49, .23, .44, 14.1),
        (180, .55, .25, .45, 14.1), (225, .65, .29, 1.44, 8.7), (END, .66, .29, 1.49, 8.7),
    ):
        aim = Vector((center, 0, .36))
        direction = Vector((sin(azimuth), cos(azimuth), height)).normalized()
        camera.location = aim + 26 * direction
        camera.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        camera.keyframe_insert('location', frame=frame)
        camera.keyframe_insert('rotation_euler', frame=frame)
        camera_data.ortho_scale = scale
        camera_data.keyframe_insert('ortho_scale', frame=frame)

    overlay = empty('Camera-space phase captions', camera)
    # Ortho scale is frame width. Drive the overlay at the same scale as the framing.
    for axis in (0, 1):
        driver = overlay.driver_add('scale', axis).driver
        driver.type = 'AVERAGE'
        variable = driver.variables.new()
        variable.targets[0].id_type = 'CAMERA'
        variable.targets[0].id = camera_data
        variable.targets[0].data_path = 'ortho_scale'
    for kicker, title, detail, spans in (
        ('IN MOTION', 'Strobe and capture', 'A short flash lights the passing part.', [(1, 53), (230, END)]),
        ('01 / OPTICS', 'Lens elements', 'Curved glass brings the image into focus.', [(54, 126)]),
        ('02 / CAPTURE', 'Global-shutter CMOS', 'The sensor exposes every pixel together.', [(127, 152)]),
        ('03 / READOUT', 'Processing and Ethernet', 'The boards process and stream the image.', [(153, 183)]),
        ('ASSEMBLY', 'On the optical axis', 'The lens and sensor return to alignment.', [(184, 229)]),
    ):
        for value, y, size, mat in ((kicker, -.224, .022, blue),
                                    (title, -.275, .041, text_ink),
                                    (detail, -.318, .025, text_ink)):
            obj = label(value, value, (-.45, y, -4), size, font, mat, overlay)
            for path in ('hide_render', 'hide_viewport'):
                visible = set()
                for start, stop in spans:
                    visible.update(range(start, stop + 1))
                boundaries = {1, END, *[f for start, stop in spans for f in (start, stop + 1)]}
                keys(obj, path, [(f, f not in visible) for f in sorted(boundaries) if f <= END])

    world = bpy.data.worlds.new('Soft studio ambient')
    world.use_nodes = True
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .35
    scene.world = world
    for name, location, power, size in (
        ('Long key', (4, 2, 9), 1800, 6), ('Front diffuser', (8, 7, 3), 1450, 5),
        ('Rim strip', (-5, -5, 6), 2100, 4), ('Low fill', (-3, 8, -4), 900, 6),
    ):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()

    scene.render.engine = 'CYCLES'
    scene.cycles.samples, scene.cycles.max_bounces = 12, 3
    scene.cycles.use_denoising = True
    scene.render.use_persistent_data = True
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    tree = bpy.data.node_groups.new('Ground | #ebebeb', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    layers = tree.nodes.new('CompositorNodeRLayers')
    over = tree.nodes.new('CompositorNodeAlphaOver')
    over.inputs['Background'].default_value = linear('ebebeb')
    output = tree.nodes.new('NodeGroupOutput')
    tree.links.new(layers.outputs['Image'], over.inputs['Foreground'])
    tree.links.new(over.outputs['Image'], output.inputs['Image'])
    layers.location, over.location, output.location = (-230, 0), (0, 0), (220, 0)

    scene.render.resolution_x, scene.render.resolution_y = 1280, 1024
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/camera_'
    scene.frame_start, scene.frame_end = 1, END - 1
    for frame, name in ((1, 'Inspection target enters'), (24, 'Strobe'), (54, 'Optical stack opens'),
                        (136, 'Global exposure'), (162, 'Process and transmit'),
                        (184, 'Reassemble'), (END, 'Loop boundary')):
        scene.timeline_markers.new(name, frame=frame)
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.color_type = 'MATERIAL'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.resolve()), compress=True)


if __name__ == '__main__':
    main(*(Path(arg) for arg in sys.argv[sys.argv.index('--') + 1:]))
