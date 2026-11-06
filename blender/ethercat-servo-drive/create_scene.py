"""Build the illustrative EtherCAT drive and its native Blender animation."""

import sys
from math import pi
from pathlib import Path

import bpy
from mathutils import Vector


END = 241
BLUE = '1f5fd6'


def linear(hex_color):
    rgb = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (*[v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb], 1)


def material(name, color, metal=0, roughness=.37, flat=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = linear(color)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    if flat:
        nodes.clear()
        shader = nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = mat.diffuse_color
        mat.node_tree.links.new(shader.outputs[0], nodes.new('ShaderNodeOutputMaterial').inputs[0])
    else:
        shader = nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = mat.diffuse_color
        shader.inputs['Metallic'].default_value = metal
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Emission Color'].default_value = linear(BLUE)
    return mat


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
        obj.modifiers.new('Weighted face normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, location, dimensions, mat, parent, bevel=.018):
    x, y, z = (length / 2 for length in dimensions)
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return finish(obj, name, mat, parent, bevel)


def cylinder(name, xyz, radius, depth, mat, parent, axis='X', sides=40):
    rotation = (0, pi / 2, 0) if axis == 'X' else (pi / 2, 0, 0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=depth,
                                        location=xyz, rotation=rotation)
    obj = bpy.context.object
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return finish(obj, name, mat, parent, min(.014, depth / 5))


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


def label(value, xyz, size, font, mat, parent, rotation=(0, 0, 0)):
    data = bpy.data.curves.new(value, 'FONT')
    data.body, data.size, data.font = value, size, font
    obj = bpy.data.objects.new(value, data)
    bpy.context.collection.objects.link(obj)
    obj.location, obj.rotation_euler = xyz, rotation
    return finish(obj, value, mat, parent)


def keys(target, property_name, values):
    for frame, value in values:
        setattr(target, property_name, value)
        target.keyframe_insert(data_path=property_name, frame=frame)


def move(obj, offset, start, opened, close, seated, twist=0):
    rest = (0, 0, 0)
    keys(obj, 'location', [(1, rest), (start, rest), (opened, offset),
                           (close, offset), (seated, rest), (END, rest)])
    if twist:
        keys(obj, 'rotation_euler', [(1, rest), (start, rest), (opened, (0, 0, twist)),
                                      (close, (0, 0, twist)), (seated, rest), (END, rest)])


def glow(mat, values):
    intensity = mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    keys(intensity, 'default_value', [(1, 0), *values, (END, 0)])


def visible(obj, spans):
    boundaries = {1, END, *[f for start, stop in spans for f in (start, stop + 1)]}
    values = [(f, not any(a <= f <= b for a, b in spans)) for f in sorted(boundaries) if f <= END]
    for path in ('hide_render', 'hide_viewport'):
        keys(obj, path, values)


def sweep(obj, start, stop):
    visible(obj, [(start, stop)])
    keys(obj.data, 'bevel_factor_end', [(start, .06), (stop - 3, 1.0)])
    keys(obj.data, 'bevel_factor_start', [(start, 0.0), (start + 4, 0.0), (stop, .92)])


def enclosure(font, graphite, charcoal, steel, cover_mat, white, blue):
    chassis = empty('01A | Enclosure carrier')
    cover = empty('01B | Vented side cover')
    box('Die-cast carrier', (-.85, .00, 0), (.19, 4.29, 5.39), graphite, chassis, .075)
    for z in (-2.61, 2.61):
        box('Chassis end cap', (-.04, .01, z), (1.67, 4.27, .17), graphite, chassis, .047)
        for i in range(7):
            box('End-cap rib', (-.56 + .173 * i, .49, z * 1.033), (.067, 2.6, .048), charcoal, chassis, .012)
    for y in (-2.01, 2.02):
        box('Board support rail', (-.66, y, 0), (.28, .15, 5.1), steel, chassis, .023)
    for z in (-2.87, 2.87):
        box('Rear cabinet mounting tab', (-.04, 2.24, z), (1.22, .29, .43), steel, chassis, .048)
        cylinder('Mounting insert', (-.04, 2.073, z), .095, .05, charcoal, chassis, axis='Y')

    box('Beveled fascia of side cover', (.848, -.56, 0), (.15, 3.12, 5.22), cover_mat, cover, .055)
    for z in (-2.48, 2.48):
        box('Side cover return', (.81, 1.54, z), (.21, 1.12, .26), cover_mat, cover)
    box('Side cover rear stile', (.848, 2.045, 0), (.15, .11, 5.04), cover_mat, cover)
    for i in range(21):
        box('Louver blade', (.83, 1.51, -2.31 + .231 * i), (.15, .99, .108), cover_mat, cover, .025)
    for y in (-1.88, .75):
        for z in (-2.33, 2.33):
            cylinder('Captive screw head', (.931, y, z), .073, .032, steel, cover)
            box('Screw slot', (.950, y, z), (.007, .080, .014), charcoal, cover, .004)
    box('Anodized identity stripe', (.937, -1.72, .91), (.032, .065, 2.35), blue, cover, .012)
    side = (pi / 2, 0, pi / 2)
    label('EC / 01', (.935, -1.49, 1.48), .38, font, white, cover, side)
    label('SERVO DRIVE', (.935, -1.47, 1.17), .177, font, white, cover, side)
    label('DIGITAL MOTION CONTROL', (.935, -1.47, -.05), .105, font, white, cover, side)
    return chassis, cover


def connectors(font, steel, charcoal, white, gold, port_mat, led, signal):
    ports = empty('02 | EtherCAT IN / OUT and I/O fascia')
    front = (pi / 2, 0, 0)
    box('Connector fascia', (0, -2.17, 0), (1.60, .17, 5.17), charcoal, ports, .053)
    box('Machined upper escutcheon', (0, -2.26, 1.50), (1.35, .055, 1.81), steel, ports, .042)
    for z, name in ((1.89, 'IN'), (1.08, 'OUT')):
        box('RJ45 receptacle recess', (0, -2.30, z), (.80, .034, .46), charcoal, ports, .038)
        for x in (-.43, .43):
            box('RJ45 shield side', (x, -2.35, z), (.091, .15, .57), port_mat, ports)
        for edge in (-1, 1):
            box('RJ45 shield lip', (0, -2.35, z + edge * .263), (.83, .15, .066), port_mat, ports)
        box('Latch recess', (0, -2.327, z - .165), (.24, .027, .123), charcoal, ports, .012)
        for i in range(8):
            box('Gold spring contact', (-.272 + i * .078, -2.353, z + .127), (.037, .086, .034), gold, ports, .007)
        label(name, (-.34, -2.296, z - .36), .096, font, charcoal, ports, front)
        box('EtherCAT link indicator', (.53, -2.303, z + .12), (.073, .045, .087), led, ports, .013)

    for z, count, legends in ((.13, 4, ('FB',)), (-.61, 3, ('STO',)),
                              (-1.45, 3, ('U', 'V', 'W')), (-2.16, 2, ('+', '−'))):
        box('Pluggable terminal housing', (0, -2.29, z), (1.04, .20, .35), port_mat, ports, .040)
        for i in range(count):
            x = (i - (count - 1) / 2) * .24
            cylinder('Terminal wire entry', (x, -2.403, z), .065, .034, charcoal, ports, axis='Y')
            if len(legends) == count:
                label(legends[i], (x - .039, -2.363, z - .264), .119, font, white, ports, front)
        if len(legends) == 1:
            label(legends[0], (-.49, -2.29, z - .287), .105, font, white, ports, front)

    for i, z in enumerate((1.89, 1.08)):
        lane = .10 + i * .13
        for name, length, start in (('Assembled data pulse', .92, 11), ('Exploded data pulse', .75, 76)):
            path = [(lane, -2.45 - length, z), (lane, -2.45, z)]
            if i:
                path.reverse()
            wave = trace(name + (' / OUT' if i else ' / IN'), path, signal, ports, .025)
            sweep(wave, start + i * 6, start + 14 + i * 6)
    return ports


def control_board(font, pcb, steel, charcoal, white, gold, solder, chip, signal):
    control = empty('03 | Control and network PCB')
    box('Control PCB laminate', (-.58, .02, 1.26), (.095, 3.75, 2.29), pcb, control, .038)
    box('Interboard connector housing', (-.45, 1.37, .21), (.17, .72, .16), charcoal, control)
    side = (pi / 2, 0, pi / 2)
    label('MOTION CONTROL', (-.517, -.62, 2.19), .133, font, white, control, side)
    for name, y, z, size in (('ESC', -1.10, 1.49, .59), ('DSP', .12, 1.22, .80),
                              ('PHY', -1.13, .63, .37), ('I/O', 1.21, 1.21, .45)):
        box(name + ' package', (-.438, y, z), (.173, size, size), chip, control, .025)
        label(name, (-.345, y - size * .30, z - .044), size * .25, font, white, control, side)
        for i in range(7):
            pin = (i - 3) * size / 8.5
            for edge in (-1, 1):
                box('Gull-wing package lead', (-.522, y + pin, z + edge * size * .53),
                    (.052, .025, .107), solder, control, .005)
                box('Gull-wing package lead', (-.522, y + edge * size * .53, z + pin),
                    (.052, .107, .025), solder, control, .005)
    for i in range(10):
        y = -.76 + i * .037
        z = 1.78 + i * .028
        path = [(-.527, -1.37, z), (-.527, y - .10, z),
                (-.527, y + .26, z - .30), (-.527, .05, z - .30)]
        trace('Copper routing / network to motion controller', path, gold, control, .005)
        if i in (2, 6, 9):
            sweep(trace('Motion setpoint on PCB', path, signal, control, .011), 106 + i, 123 + i)
    for z in (.36, 2.12):
        for i in range(16):
            y = -1.63 + i * .208
            box('Surface-mounted passive', (-.495, y, z), (.064, .100, .065),
                solder if i % 4 else steel, control, .009)
    for y in (-1.67, 1.70):
        for z in (.29, 2.22):
            cylinder('PCB captive fastener', (-.502, y, z), .075, .045, steel, control)
    return control


def power_stage(pcb, charcoal, steel, caps, copper, ceramic, signal):
    power = empty('04 | Three-phase inverter and DC link')
    box('Power PCB laminate', (-.60, .01, -1.13), (.11, 3.74, 2.56), pcb, power, .042)
    for y in (-1.26, -.57):
        for z in (-1.88, -1.16, -.44):
            cylinder('DC-link electrolytic capacitor', (-.226, y, z), .267, .62, caps, power)
            cylinder('Scored capacitor lid', (.091, y, z), .238, .042, steel, power)
            for angle in (0, pi / 3, -pi / 3):
                obj = box('Pressure relief score', (.117, y, z), (.011, .301, .018), charcoal, power, .004)
                obj.rotation_euler.x = angle

    box('Inverter heat spreader', (-.45, 1.26, -1.24), (.16, 1.39, 1.98), steel, power, .035)
    box('Insulated inverter base', (-.33, .99, -1.24), (.40, 1.41, 1.98), ceramic, power, .055)
    for i, z in enumerate((-.62, -1.20, -1.78)):
        box('Half-bridge switch package', (-.031, .93, z), (.31, 1.04, .40), charcoal, power, .045)
        for y in (.60, 1.20):
            box('Switch metallized terminal', (.145, y, z), (.075, .195, .26), copper, power)
        route = [(.159, 1.24, z), (.159, 1.57, z), (.159, 1.73, z - .17), (.159, 1.73, z - .29)]
        trace('Copper phase busbar', route, copper, power, .037)
        sweep(trace('Motor phase switching pulse', route, signal, power, .044), 139 + i * 7, 153 + i * 7)
        box('Isolated gate driver', (-.47, .47, z + .26), (.12, .37, .102), steel, power)
    for y in (-1.70, 1.71):
        for z in (-2.23, -.04):
            cylinder('Power board standoff head', (-.50, y, z), .072, .05, steel, power)
    return power


def heat_sink(aluminum, ceramic, graphite):
    sink = empty('05 | Finned aluminum heat sink')
    box('Extruded aluminum heat-sink base', (-.02, 2.11, 0), (1.79, .29, 5.34), aluminum, sink, .058)
    for i in range(11):
        x = -.803 + .157 * i
        box('Extruded convection fin', (x, 2.56, 0), (.083, .72, 5.15), aluminum, sink, .034)
    box('Thermal interface pad', (-.03, 1.942, -1.15), (1.40, .064, 2.22), ceramic, sink, .034)
    for z in (-2.46, 2.46):
        box('Heat-sink mounting boss', (0, 2.91, z), (1.36, .13, .145), aluminum, sink, .020)
        cylinder('Heat-sink fastener', (0, 3.001, z), .082, .06, graphite, sink, axis='Y')
    return sink


def camera_and_titles(scene, font, ink, blue):
    data = bpy.data.cameras.new('Orthographic product lens')
    camera = bpy.data.objects.new('Product camera', data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    data.type = 'ORTHO'
    for frame, direction, center, width in (
        (1, (.78, -.63, .35), (0, .03, -.76), 11.2),
        (29, (.76, -.65, .32), (.02, -.11, -.74), 11.2),
        (64, (.83, -.56, .27), (.32, .14, -.73), 11.7),
        (107, (.86, -.51, .25), (.35, .85, -.68), 13.3),
        (163, (.87, -.50, .24), (.35, .93, -.70), 13.3),
        (193, (.85, -.53, .27), (.35, .90, -.68), 13.3),
        (226, (.78, -.63, .35), (0, .03, -.76), 11.2),
        (END, (.78, -.63, .35), (0, .03, -.76), 11.2),
    ):
        direction = Vector(direction).normalized()
        keys(camera, 'location', [(frame, Vector(center) + 30 * direction)])
        keys(camera, 'rotation_euler', [(frame, direction.to_track_quat('Z', 'Y').to_euler())])
        keys(data, 'ortho_scale', [(frame, width)])

    overlay = empty('Camera-space captions', camera)
    # With this driver each overlay unit is one visible frame width.
    for axis in (0, 1):
        driver = overlay.driver_add('scale', axis).driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.targets[0].id_type = 'CAMERA'
        var.targets[0].id = data
        var.targets[0].data_path = 'ortho_scale'
    rule = material('Inactive progress rail', 'b5bcc6', flat=True)
    label('FUNCTIONAL CUTAWAY', (-.442, .346, -5), .024, font, ink, overlay)
    label('DRIVE / 05', (.324, .346, -5), .024, font, blue, overlay)
    phases = (
        ('IN MOTION', 'Synchronized motion', 'EtherCAT carries motion commands and drive status.', [(1, 31), (226, END)]),
        ('01 / PACKAGING', 'Vented enclosure', 'The side cover lifts to expose the electronics.', [(32, 65)]),
        ('02 / NETWORK', 'EtherCAT ports', 'IN and OUT link the drive to its neighbors.', [(66, 100)]),
        ('03 / CONTROL', 'Control board', 'The controller uses feedback to correct motion.', [(101, 133)]),
        ('04 / POWER', 'Three-phase inverter', 'The switches meter current into U, V and W.', [(134, 168)]),
        ('05 / THERMAL', 'Finned heat sink', 'Aluminum fins transfer heat to the surrounding air.', [(169, 202)]),
        ('ASSEMBLY', 'Drive closes', 'The ports, boards and cover return to their seats.', [(203, 225)]),
    )
    for i in range(5):
        location = (-.428 + i * .038, -.215, -5)
        box('Inactive phase marker', location, (.028, .005, .012), rule, overlay, 0)
        active = box('Active phase marker', (location[0], location[1], -4.96),
                     (.028, .005, .012), blue, overlay, 0)
        visible(active, phases[i + 1][3])
    for kicker, title, description, spans in phases:
        scene.timeline_markers.new(kicker + ' | ' + title, frame=spans[0][0])
        for value, y, size, mat in ((kicker, -.254, .021, blue), (title, -.306, .046, ink),
                                     (description, -.351, .024, ink)):
            visible(label(value, (-.442, y, -5), size, font, mat, overlay), spans)


def studio(scene):
    world = bpy.data.worlds.new('Studio ambient')
    world.use_nodes = True
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .35
    scene.world = world
    for name, position, power, size in (
        ('Soft key', (4, -5, 8), 1700, 7), ('Front strip', (1, -7, 1), 780, 5),
        ('Rear edge light', (-4, 5, 7), 1450, 5), ('Side fill', (7, 5, 2), 880, 5),
    ):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = position
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


def main(destination, font_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'EtherCAT servo drive | functional cutaway'
    scene['Scale note'] = 'Illustrative low-voltage DC-fed drive. Geometry and timing are not to scale.'
    font = bpy.data.fonts.load(str(font_path.resolve()))
    ink = material('Ink | #1a1a1a', '1a1a1a', flat=True)
    blue = material('Accent | #1f5fd6', BLUE, flat=True)
    signal = material('Data and power tracers', BLUE, flat=True)
    white = material('Ivory silkscreen', 'f4f6f8', flat=True)
    graphite = material('Powder-coated graphite', '343b44', .24)
    charcoal = material('Molded connector resin', '191e25', 0, .44)
    steel = material('Bead-blasted nickel', 'a3acb8', .54, .34)
    gold = material('Gold contacts', 'b89b62', .53, .30)
    copper = material('Copper busbars', 'ba8053', .55, .29)
    solder = material('Tin and ceramic passives', 'b4b5a9', .43, .40)
    ceramic = material('Thermal interface ceramic', 'adb6bc', .13, .37)
    cover_mat = material('Enclosure highlight', '3a434f', .25, .35)
    port_mat = material('Port highlight', '6c7989', .39, .32)
    led = material('EtherCAT link status', '233548', .12, .29)
    pcb = material('Control highlight', '173b43', .17, .45)
    chip = material('Black IC molding', '272c34', .14, .35)
    power_pcb = material('Power highlight', '203541', .20, .39)
    caps = material('Capacitor sleeves', '203647', .13, .40)
    aluminum = material('Thermal highlight', '8d99a6', .58, .38)

    chassis, cover = enclosure(font, graphite, charcoal, steel, cover_mat, white, blue)
    ports = connectors(font, steel, charcoal, white, gold, port_mat, led, signal)
    control = control_board(font, pcb, steel, charcoal, white, gold, solder, chip, signal)
    power = power_stage(power_pcb, charcoal, steel, caps, copper, ceramic, signal)
    sink = heat_sink(aluminum, ceramic, graphite)

    move(cover, (4.35, .40, .75), 31, 66, 204, 224, .74)
    move(chassis, (-.65, .16, -.08), 42, 79, 204, 225)
    move(ports, (-.15, -1.61, .08), 56, 78, 204, 222)
    move(control, (.74, -.14, .63), 80, 105, 203, 223)
    move(power, (.84, -.13, -.55), 92, 120, 203, 222)
    move(sink, (-1.35, 4.02, -.22), 72, 114, 203, 224, -1.05)

    for mat, start, stop in ((cover_mat, 32, 65), (port_mat, 66, 100), (pcb, 101, 133),
                              (power_pcb, 134, 168), (aluminum, 169, 202)):
        glow(mat, [(start, 0), (start + 6, .52), (stop - 6, .52), (stop, 0)])
    glow(led, [(8, 0), (14, 2.4), (19, .2), (23, 1.9), (31, 0),
               (73, 0), (79, 2.4), (85, .2), (93, 1.9), (100, 0)])

    camera_and_titles(scene, font, ink, blue)
    studio(scene)
    scene.render.resolution_x, scene.render.resolution_y = 1280, 1024
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/drive_'
    scene.frame_start, scene.frame_end = 1, END - 1
    scene.timeline_markers.new('Loop boundary', frame=END)
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
