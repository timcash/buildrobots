"""Build an illustrative fiber-laser source, optical path, and welding station."""

import random
import sys
from math import cos, pi, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.geometry import interpolate_bezier

END = 241


def color(hex_value):
    rgb = [int(hex_value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*[v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb], 1)


def material(name, hex_value, metal=0, roughness=.38):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color(hex_value)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = roughness
    return mat


def luminous(name, hex_value):
    mat = material(name, hex_value)
    nodes = mat.node_tree.nodes
    emitter = nodes.new('ShaderNodeEmission')
    emitter.inputs['Color'].default_value = mat.diffuse_color
    mat.node_tree.links.new(emitter.outputs[0], nodes.get('Material Output').inputs['Surface'])
    return mat


def highlight(mat, start, peak, stop, strength):
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = color('1f5fd6')
    animate(shader.inputs['Emission Strength'], 'default_value',
            [(1, 0), (start, 0), (peak, strength), (stop - 5, strength), (stop, 0), (END, 0)])


def animate(obj, path, values):
    for frame, value in values:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def show(obj, start, stop):
    for path in ('hide_render', 'hide_viewport'):
        animate(obj, path, [(f, not start <= (1 if f == END else f) < stop)
                            for f in sorted({1, start, stop, END})])


def lift(obj, delta, start, opened, closing, closed):
    home = obj.location.copy()
    away = home + Vector(delta)
    animate(obj, 'location', [(1, home), (start, home), (opened, away),
                              (closing, away), (closed, home), (END, home)])


def empty(name, parent=None, xyz=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = parent, xyz
    obj.empty_display_size = .12
    return obj


def finish(obj, name, mat, parent, bevel=0):
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    if bevel:
        edge = obj.modifiers.new('Machined edges', 'BEVEL')
        edge.width, edge.segments = bevel, 3
        obj.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, xyz, size, mat, parent, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    for vert in obj.data.vertices:
        for axis, length in enumerate(size):
            vert.co[axis] *= length
    return finish(obj, name, mat, parent, bevel)


def turned(name, xyz, radius, depth, mat, parent, tip=None, axis='Z', sides=48):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=radius, radius2=radius if tip is None else tip,
                                   depth=depth, location=xyz)
    obj = bpy.context.object
    if axis == 'X':
        obj.rotation_euler.y = pi / 2
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return finish(obj, name, mat, parent, .012)


def tube(name, points, width, mat, parent):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions, curve.bevel_depth, curve.bevel_resolution = '3D', width, 2
    curve.use_fill_caps = True
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, parent)


def bend(start, control1, control2, stop, samples=40):
    return interpolate_bezier(*map(Vector, (start, control1, control2, stop)), samples)


def sweep(obj, start, stop, width):
    # A moving band on a curve follows arc length, including around the coil.
    curve = obj.data
    curve.bevel_factor_mapping_start = curve.bevel_factor_mapping_end = 'SPLINE'
    animate(curve, 'bevel_factor_end', [(1, 0), (start, 0), (stop - 4, 1), (stop, 1), (END, 0)])
    animate(curve, 'bevel_factor_start', [(1, 0), (start + width, 0), (stop, 1), (END, 0)])
    for channel in curve.animation_data.action.layers[0].strips[0].channelbag(curve.animation_data.action_slot).fcurves:
        for key in channel.keyframe_points:
            key.interpolation = 'LINEAR'
    show(obj, start, stop)


def label(name, content, xyz, size, font, mat, parent, rotation=(0, 0, 0)):
    data = bpy.data.curves.new(name, 'FONT')
    data.body, data.size, data.font = content, size, font
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location, obj.rotation_euler = xyz, rotation
    return finish(obj, name, mat, parent)


def cabinet(font, mats):
    ink, alloy, black, blue, paper = (mats[k] for k in ('ink', 'alloy', 'black', 'blue', 'paper'))
    base = empty('01 | Fiber laser source')
    lid = empty('Source lid', base)
    fascia = empty('Service fascia', base)
    box('Cast base', (-2.2, .1, .23), (5.9, 3.48, .31), ink, base, .085)
    box('Rear wall', (-2.2, 1.77, .70), (5.84, .12, .84), ink, base)
    for x in (-5.04, .65):
        box('Side rail', (x, .13, .67), (.17, 3.18, .77), ink, base)
        for y in (-1.26, 1.42):
            box('Isolation foot', (x, y, .08), (.43, .5, .16), black, base, .05)
    box('Cover', (-2.2, .09, 1.19), (5.88, 3.49, .20), alloy, lid, .07)
    box('Cover inset', (-2.2, .1, 1.296), (5.61, 3.21, .018), ink, lid, .007)
    box('Cobalt registration stripe', (-4.80, .10, 1.309), (.065, 3.16, .015), blue, lid, .003)
    label('Source badge', 'Yb / FIBER SOURCE', (-4.53, -.02, 1.31), .22, font, paper, lid)
    label('Source badge index', 'OPTICAL ENGINE   /   04', (-4.51, -.30, 1.31), .11, font, paper, lid)
    box('Front panel', (-2.2, -1.59, .69), (5.88, .21, .83), ink, fascia, .055)
    box('Display recess', (-3.99, -1.709, .72), (1.18, .047, .32), black, fascia)
    label('Status display', 'SOURCE  /  READY', (-4.47, -1.738, .69), .105, font, paper, fascia, (pi / 2, 0, 0))
    for i in range(19):
        box('Intake slot', (-2.90 + i * .152, -1.702, .69), (.062, .03, .41), black, fascia, .015)
    for x in (-4.94, .55):
        for y in (-1.46, 1.58):
            turned('Cover screw', (x, y, 1.30), .062, .022, alloy, lid, sides=12)
    for y in (.84, 1.30):
        turned('Coolant port', (.77, y, .70), .125, .22, alloy, base, axis='X', sides=12)
        turned('Coolant cap', (.90, y, .70), .09, .09, black, base, axis='X')
    box('DC power shield', (-3.52, 1.12, .64), (2.49, .87, .48), mats['steel'], base)
    for i in range(15):
        box('Power shield rib', (-4.65 + i * .157, 1.11, .91), (.062, .77, .065), alloy, base, .008)
    box('Driver control board', (-.97, 1.12, .45), (1.71, .81, .10), mats['pcb'], base)
    for i in range(6):
        box('Diode driver IC', (-1.57 + i * .239, 1.13, .535), (.14, .29, .07), black, base, .008)
    lift(lid, (-.54, .72, 2.32), 17, 65, 196, 230)
    lift(fascia, (0, -.47, -.15), 30, 66, 198, 225)
    return base


def optical_engine(base, mats):
    alloy, ink, blue, light = (mats[k] for k in ('alloy', 'ink', 'blue', 'light'))
    pump = empty('02 | Pump diode cold plate', base)
    gain = empty('03 | Ytterbium gain cassette', base)
    # Both trays lift together so the pump pigtails stay physically connected.
    for tray in (pump, gain):
        lift(tray, (0, 0, .55), 34, 67, 195, 219)
    box('Liquid-cooled pump plate', (-3.56, -.41, .46), (2.58, 1.97, .16), alloy, pump, .06)
    for y in (-1.06, -.40, .26):
        for x in (-4.34, -3.48):
            box('Pump diode package', (x, y, .63), (.68, .47, .22), mats['pump'], pump, .045)
            box('Diode copper heat spreader', (x, y, .752), (.49, .34, .032), mats['copper'], pump, .009)
            for offset in (-.092, .092):
                box('Diode terminal', (x - .35, y + offset, .70), (.14, .043, .044), alloy, pump, .006)
        route = bend((-3.12, y, .68), (-2.65, y, .68), (-2.56, -.40, .69), (-2.20, -.40, .69))
        elbow = (-3.27, y + .275, .65)
        branch = [*bend((-4.00, y, .68), (-3.88, y, .68), (-3.91, y + .275, .65), elbow)[:-1],
                  *bend(elbow, (-2.66, y + .275, .65), (-2.61, -.34, .69), (-2.20, -.37, .69))]
        for path in (route, branch):
            tube('Pump pigtail', path, .028, ink, pump)
            sweep(tube('Pump light in pigtail', path, .039, light, pump), 70, 101, 10)
    turned('Pump signal combiner', (-1.97, -.40, .69), .15, .51, alloy, pump, .083, 'X')
    box('Fiber cassette plate', (-.72, -.34, .45), (2.04, 1.91, .16), alloy, gain, .055)
    turned('Fiber mandrel', (-.68, -.36, .58), .69, .13, ink, gain)
    for i in range(8):
        angle = tau * i / 8
        turned('Cassette retainer', (-.68 + .80 * cos(angle), -.36 + .80 * sin(angle), .57),
               .082, .086, alloy, gain, sides=12)
    turns = 4.5
    coil = [(-.68 + .70 * cos(pi + tau * turns * t / 360),
             -.36 + .70 * sin(pi + tau * turns * t / 360), .61 + .23 * t / 360) for t in range(361)]
    entry = bend((-1.72, -.40, .69), (-1.51, -.40, .69), (-1.42, -.22, .62), coil[0])
    exit_path = bend(coil[-1], (.03, -.88, .84), (.29, -.95, .72), (.65, -.95, .70))
    route = [*entry[:-1], *coil, *exit_path[1:]]
    tube('Ytterbium-doped gain fiber', route, .027, mats['gain'], gain)
    sweep(tube('Signal through gain fiber', route, .043, light, gain), 95, 135, 17)
    turned('Input fiber Bragg grating sleeve', (-1.58, -.37, .68), .067, .18, blue, gain, axis='X')
    turned('Output fiber Bragg grating sleeve', (.39, -.95, .72), .075, .22, blue, gain, axis='X')
    # The feedthrough and head stay fixed. This pigtail bends as the cassette rises.
    link = tube('Flexible output pigtail', ((.65, -.95, .70), (.86, -.95, .70),
                                           (1.09, -.99, .68), (1.30, -.99, .68)), .039, ink, base)
    for i, point in enumerate(link.data.splines[0].points[:2]):
        home = point.co.copy()
        up = home.copy()
        up.z += .55 if i == 0 else .33
        for frame, co in ((1, home), (34, home), (67, up), (195, up), (219, home), (END, home)):
            point.co = co
            point.keyframe_insert('co', frame=frame)
    flex_light = tube('Light through output pigtail', ((.65, -.95, 1.25), (.86, -.95, 1.03),
                                                      (1.09, -.99, .68), (1.30, -.99, .68)), .052, light, base)
    sweep(flex_light, 129, 145, 4)


def processing_station(base, font, mats):
    ink, alloy, black, blue, light = (mats[k] for k in ('ink', 'alloy', 'black', 'blue', 'light'))
    head_x, head_y = 4.10, -.22
    head = empty('05 | Processing head', xyz=(head_x, head_y, 0))
    # Two cubic bends carry the armor out of the cabinet and into the QBH connector.
    collar = (head_x, head_y, 3.54)
    arc = (2.62, -1.24, 2.68)
    cable = [*bend((.72, -.99, .68), (2.12, -.99, .68), (2.16, -1.45, 1.56), arc, 55)[:-1],
             *bend(arc, (3.12, -.99, 3.89), (head_x, head_y, 4.15), collar, 55)]
    turned('Chassis fiber gland', (.77, -.99, .68), .16, .30, alloy, base, axis='X', sides=12)
    tube('04 | Armored delivery fiber', cable, .104, mats['cable'], None)
    # A blue tracer runs just above the jacket to show the enclosed optical path.
    tracer = [(x, y - .055, z + .098) for x, y, z in cable]
    sweep(tube('Signal in delivery fiber', tracer, .049, light, None), 137, 166, 12)
    for i in range(1, 8):
        turned('Cabinet strain relief', (.86 + i * .062, -.99, .68), .14 - i * .003, .035, black, base, axis='X')
        turned('Head strain relief', (0, 0, 3.52 + i * .045), .129 - i * .003, .026, black, head)
    turned('QBH connector', (0, 0, 3.43), .185, .29, alloy, head, sides=12)
    turned('Collimator barrel', (0, 0, 3.13), .29, .47, ink, head)
    turned('Collimator lock ring', (0, 0, 3.27), .32, .077, alloy, head)
    cowl = empty('Removable head cowl', head)
    box('Head body', (0, 0, 2.59), (.85, .83, .82), mats['head'], cowl, .11)
    box('Head face plate', (0, -.426, 2.59), (.68, .08, .59), alloy, cowl, .052)
    box('Head serial plate', (0, -.472, 2.64), (.49, .019, .23), ink, cowl, .016)
    label('Head badge', 'WELD', (-.19, -.486, 2.59), .13, font, mats['paper'], cowl, (pi / 2, 0, 0))
    for x in (-.28, .28):
        for z in (2.37, 2.81):
            screw = turned('Face plate fastener', (x, -.471, z), .037, .022, ink, cowl, sides=12)
            screw.rotation_euler.x = pi / 2
    lift(cowl, (.86, .16, .12), 137, 157, 187, 206)
    for z, radius in ((2.81, .215), (2.37, .266)):
        turned('Optics mount', (0, 0, z), radius + .054, .081, alloy, head)
        turned('AR-coated optic', (0, 0, z + .052), radius, .068, mats['optic'], head, radius * .91)
    beam_path = ((0, 0, 3.36), (0, 0, 2.81), (0, 0, 2.34), (0, 0, 1.45))
    sweep(tube('Signal inside head', beam_path, .047, light, head), 160, 178, 8)
    turned('Focus barrel', (0, 0, 2.10), .29, .45, ink, head)
    turned('Protective window collar', (0, 0, 1.84), .34, .095, blue, head)
    turned('Copper shielding nozzle', (0, 0, 1.55), .085, .47, mats['copper'], head, .26)
    turned('Shielding gas inlet', (.39, 0, 1.94), .10, .29, alloy, head, axis='X', sides=12)

    box('Station bed', (head_x, head_y, .15), (2.86, 1.83, .27), ink, None, .072)
    for y in (-.82, .38):
        box('Linear stage rail', (head_x, y, .34), (2.75, .13, .14), alloy, None)
    stage = empty('06 | Coupon linear stage', xyz=(head_x, head_y, 0))
    box('Moving fixture', (0, 0, .47), (1.98, 1.15, .22), black, stage, .05)
    for y in (-.238, .238):
        box('Steel weld coupon', (0, y, .625), (1.76, .465, .096), mats['steel'], stage, .015)
    for x in (-.82, .82):
        for y in (-.48, .48):
            turned('Coupon clamp', (x, y, .68), .087, .105, alloy, stage, sides=12)
    animate(stage, 'location', [(1, stage.location.copy()), (152, (head_x, head_y, 0)),
                               (166, (head_x + .65, head_y, 0)), (192, (head_x - .65, head_y, 0)),
                               (227, (head_x, head_y, 0)), (END, (head_x, head_y, 0))])
    weld = tube('Growing weld bead', ((-.65, 0, .678), (.65, 0, .678)), .024, mats['copper'], stage)
    animate(weld.data, 'bevel_factor_end', [(1, 0), (166, 0), (192, 1), (END, 1)])
    animate(weld.data, 'bevel_depth', [(1, .024), (213, .024), (226, 0), (END, .024)])
    show(weld, 167, 226)
    beam = tube('Illustrative focused beam', ((0, 0, 1.32), (0, 0, .68)), .032, light, head)
    show(beam, 166, 193)
    spot = turned('Weld pool', (0, 0, .688), .084, .018, mats['spark'], head)
    show(spot, 166, 193)
    rng = random.Random(74)
    for i in range(24):
        start = 167 + i % 22
        angle, reach = rng.uniform(0, tau), rng.uniform(.14, .41)
        x, y, z = reach * cos(angle), reach * sin(angle), rng.uniform(.08, .36)
        spark = tube('Weld spatter', ((.66 * x, .66 * y, .70 + .65 * z), (x, y, .70 + z)),
                     .012, mats['spark'], head)
        show(spark, start, start + 4)


def shot(scene, font, mats):
    data = bpy.data.cameras.new('Orthographic product camera')
    camera = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(camera)
    scene.camera, data.type = camera, 'ORTHO'
    for frame, aim, direction, width in (
        (1, (-.24, 0, 1.05), (.40, -.83, .61), 11.50),
        (23, (-.25, 0, 1.12), (.36, -.85, .64), 11.65),
        (69, (-.42, .15, 1.56), (.28, -.82, .85), 12.45),
        (118, (-.42, .12, 1.52), (.21, -.86, .84), 12.30),
        (179, (-.12, .03, 1.52), (.28, -.89, .69), 12.45),
        (226, (-.22, 0, 1.10), (.39, -.84, .62), 11.55),
        (END, (-.24, 0, 1.05), (.40, -.83, .61), 11.50),
    ):
        view = Vector(direction).normalized()
        camera.location = Vector(aim) + 24 * view
        camera.rotation_euler = view.to_track_quat('Z', 'Y').to_euler()
        camera.keyframe_insert('location', frame=frame)
        camera.keyframe_insert('rotation_euler', frame=frame)
        data.ortho_scale = width
        data.keyframe_insert('ortho_scale', frame=frame)

    overlay = empty('Screen-aligned phase labels', camera)
    for axis in (0, 1):
        driver = overlay.driver_add('scale', axis).driver
        driver.type = 'AVERAGE'
        target = driver.variables.new().targets[0]
        target.id_type, target.id, target.data_path = 'CAMERA', data, 'ortho_scale'
    for index, (name, verb, start, stop) in enumerate((
        ('PUMP DIODES', 'Combine pump light', 36, 97),
        ('GAIN FIBER', 'Amplify in the Yb coil', 97, 136),
        ('DELIVERY FIBER', 'Guide light to the head', 136, 162),
        ('PROCESSING HEAD', 'Focus light on the seam', 162, 209),
    )):
        x = -.45 + .235 * index
        box('Phase rail', (x + .087, -.305, -4.05), (.174, .003, .003), mats['quiet'], overlay, 0)
        label('Optical path step', f'0{index + 1}  {name}', (x, -.333, -4), .019, font, mats['type'], overlay)
        active = box('Active phase rail', (x + .087, -.305, -4), (.174, .005, .003), mats['type_blue'], overlay, 0)
        show(active, start, stop)
        obj = label(verb, verb, (-.45, -.268, -4), .032, font, mats['type'], overlay)
        show(obj, start, stop)
    for content, start, stop in (('Fiber laser source', 1, 36), ('Close the optical engine', 209, END)):
        obj = label(content, content, (-.45, -.268, -4), .032, font, mats['type'], overlay)
        show(obj, start, stop)
    for child in overlay.children:
        child.visible_shadow = False


def contact_shadow(name, x, y, width, depth, opacity):
    """Fade a soft footprint into the exact background color."""
    bpy.ops.mesh.primitive_plane_add(size=2, location=(x, y, -.003))
    plane = bpy.context.object
    plane.name = name
    plane.scale = (width / 2, depth / 2, 1)
    for ray in ('diffuse', 'glossy', 'transmission', 'volume_scatter', 'shadow'):
        setattr(plane, 'visible_' + ray, False)
    mat = luminous(name, '4d4d4d')
    plane.data.materials.append(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    uv = nodes.new('ShaderNodeTexCoord')
    centered = nodes.new('ShaderNodeVectorMath')
    centered.operation = 'SUBTRACT'
    centered.inputs[1].default_value = (.5, .5, 0)
    links.new(uv.outputs['UV'], centered.inputs[0])
    absolute = nodes.new('ShaderNodeVectorMath')
    absolute.operation = 'ABSOLUTE'
    links.new(centered.outputs['Vector'], absolute.inputs[0])
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(absolute.outputs['Vector'], separate.inputs[0])
    distance = nodes.new('ShaderNodeMath')
    distance.operation = 'ADD'
    # Fourth powers round the footprint's corners without making it elliptical.
    for i, axis in enumerate(('X', 'Y')):
        power = nodes.new('ShaderNodeMath')
        power.operation = 'POWER'
        power.inputs[1].default_value = 4
        links.new(separate.outputs[axis], power.inputs[0])
        links.new(power.outputs[0], distance.inputs[i])
    fade = nodes.new('ShaderNodeMapRange')
    fade.interpolation_type = 'SMOOTHERSTEP'
    for key, value in (('From Min', .009), ('From Max', .061), ('To Min', opacity), ('To Max', 0)):
        fade.inputs[key].default_value = value
    links.new(distance.outputs[0], fade.inputs['Value'])
    mix = nodes.new('ShaderNodeMixShader')
    links.new(fade.outputs['Result'], mix.inputs[0])
    links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0], mix.inputs[1])
    links.new(nodes.get('Emission').outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])


def studio(scene):
    contact_shadow('Source contact shadow', -2.14, .25, 7.15, 4.65, .42)
    contact_shadow('Station contact shadow', 4.13, -.08, 3.8, 2.82, .35)
    world = bpy.data.worlds.new('Soft studio ambient')
    world.use_nodes = True
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .38
    scene.world = world
    for name, position, power, size in (
        ('Key softbox', (-2, -6, 9), 1700, 7), ('Rim softbox', (-1, 5, 7), 1750, 6),
        ('Head fill', (7, -1, 5), 880, 4), ('Cabinet fill', (-7, -1, 4), 560, 4),
    ):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.engine = 'CYCLES'
    scene.cycles.samples, scene.cycles.max_bounces = 8, 3
    scene.cycles.use_denoising = True
    scene.cycles.denoising_prefilter = 'FAST'
    scene.render.use_persistent_data = True
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    tree = bpy.data.node_groups.new('Studio ground | #ebebeb', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    layers = tree.nodes.new('CompositorNodeRLayers')
    over = tree.nodes.new('CompositorNodeAlphaOver')
    over.inputs['Background'].default_value = color('ebebeb')
    output = tree.nodes.new('NodeGroupOutput')
    tree.links.new(layers.outputs['Image'], over.inputs['Foreground'])
    tree.links.new(over.outputs['Image'], output.inputs['Image'])
    layers.location, over.location, output.location = (-230, 0), (0, 0), (220, 0)


def main(destination, font_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'Industrial fiber laser | Pump to weld'
    font = bpy.data.fonts.load(str(font_path.resolve()))
    mats = {key: material(name, rgb, metal, rough) for key, name, rgb, metal, rough in (
        ('ink', 'Graphite anodized aluminum', '28313d', .63, .34),
        ('alloy', 'Bead-blasted aluminum', 'adbaca', .70, .33),
        ('steel', 'Brushed steel', '818c99', .66, .32),
        ('black', 'Rubber and seals', '1a1a1a', .04, .67),
        ('copper', 'Copper heat spreader and nozzle', 'be7749', .64, .30),
        ('pcb', 'Driver board solder mask', '31514a', .14, .40),
        ('blue', 'Cobalt identification', '1f5fd6', .21, .34),
        ('pump', 'Pump diode package', '3d526a', .50, .35),
        ('gain', 'Gain fiber jacket', '365882', .17, .30),
        ('cable', 'Braided delivery jacket', '273747', .20, .42),
        ('head', 'Head anodizing', '2f435b', .57, .28),
        ('optic', 'Blue AR-coated optics', '327eab', .35, .16),
    )}
    mats.update({k: luminous(k, value) for k, value in (
        ('paper', 'e7eff9'), ('type', '1a1a1a'), ('type_blue', '1f5fd6'), ('quiet', 'a9b3c0'),
        ('light', '52acff'), ('spark', 'ffbb65'),
    )})
    mats['light'].node_tree.nodes.get('Emission').inputs['Strength'].default_value = 1.65
    mats['spark'].node_tree.nodes.get('Emission').inputs['Strength'].default_value = 2.4
    for name, start, peak, stop, power in (
        ('pump', 59, 76, 100, .68), ('gain', 90, 109, 139, .85),
        ('cable', 132, 145, 166, .42), ('head', 151, 171, 193, .40), ('optic', 148, 168, 194, .9),
    ):
        highlight(mats[name], start, peak, stop, power)
    base = cabinet(font, mats)
    optical_engine(base, mats)
    processing_station(base, font, mats)
    shot(scene, font, mats)
    studio(scene)
    scene.render.resolution_x, scene.render.resolution_y = 1280, 1024
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/laser_'
    scene.frame_start, scene.frame_end = 1, END - 1
    for frame, name in ((1, 'Source closed'), (18, 'Lift cabinet lid'), (70, 'Pump diodes'),
                        (97, 'Ytterbium gain fiber'), (137, 'Delivery fiber'), (158, 'Head optics'),
                        (166, 'Weld the seam'), (209, 'Reassemble'), (END, 'Loop boundary')):
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
