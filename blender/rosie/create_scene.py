"""Build the Rosie slide scene from AMR's public Rosie 1400 simulation kit."""

import json
import sys
from math import cos, radians, sin, tau
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


def linear(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels) + (1,)


def finish(name, color, metal=0, roughness=0.4):
    material = bpy.data.materials.new(name)
    material.diffuse_color = linear(color)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = material.diffuse_color
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = roughness
    return material


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def object_in(group, name, data):
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    return obj


def line(group, name, points, thickness, material):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = thickness
    curve.bevel_resolution = 3
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (*coords, 1)
    curve.materials.append(material)
    return object_in(group, name, curve)


def arc(group, name, radius, start, end, thickness, material):
    points = [(radius * cos(tau * t), radius * sin(tau * t), 0)
              for t in (start + (end - start) * i / 64 for i in range(65))]
    return line(group, name, points, thickness, material)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def main(source, destination):
    model = json.loads((source / 'robot.json').read_text(encoding='utf-8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=str(source / 'rosie_1400.glb'))
    root = bpy.data.objects['rosie_1400']
    root.name = 'Rosie 1400 | AMR simulation CAD'
    root['source'] = 'https://advancedmetalresearch.com/assets/sim/1400/glb/rosie_1400.glb'
    root['source_version'] = model['version']
    rig = collection('01 | AMR CAD and joint hierarchy')
    for obj in list(scene.objects):
        for previous in obj.users_collection:
            previous.objects.unlink(obj)
        rig.objects.link(obj)
    studio = collection('02 | Camera and lighting')
    guides = collection('03 | Illustrative joint and floor marks')

    ink = finish('Graphite | #1a1a1a', '1a1a1a', 0.36)
    alloy = finish('Satin alloy', 'a5afb9', 0.55, 0.30)
    shell = finish('Pale alloy', 'd3d9df', 0.44, 0.29)
    blue = finish('Cobalt | #1f5fd6', '1f5fd6', 0.28, 0.30)
    guide = finish('Floor marks', '929eae', 0, 0.85)
    highlight = finish('Joint highlight | #1f5fd6', '1f5fd6')
    shader = highlight.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = highlight.diffuse_color
    shader.inputs['Emission Strength'].default_value = 0.65

    links = [bpy.data.objects['base_link'], *(bpy.data.objects[j['child']] for j in model['joints'])]
    # Blender imports the glTF Y-up basis into the mesh-local coordinates.
    # Restore the kit's Z-up link frames so the documented joint axes apply.
    root.rotation_mode = 'XYZ'
    root.rotation_euler = (0, 0, 0)
    links[0].rotation_mode = 'XYZ'
    links[0].rotation_euler = (0, 0, 0)
    links[0].location = model['frames']['base_link']['xyz']
    for link, joint in zip(links[1:], model['joints']):
        link.location = joint['origin_xyz']
    tool = bpy.data.objects['tool0']
    tool.location = model['frames']['tool0']['xyz']
    tool.rotation_mode = 'XYZ'
    tool.rotation_euler = Euler(model['frames']['tool0']['rpy'])
    kit_basis = Matrix.Rotation(-tau / 4, 4, 'X')
    for link, material in zip(links, (ink, alloy, blue, ink, shell, ink, alloy)):
        link.data.transform(kit_basis)
        link.data.materials.clear()
        link.data.materials.append(material)
        link.data.set_sharp_from_angle(angle=radians(35))
        link.data.polygons.foreach_set('use_smooth', [True] * len(link.data.polygons))

    # Home, lift, reach, wrist sweep and return. Angles are illustrative.
    poses = (
        (1, (-11, 12, -23, -12, 22, -12)),
        (27, (-11, 12, -23, -12, 22, -12)),
        (65, (-6, -9, 5, 10, 27, 4)),
        (112, (15, 32, -34, -21, -17, 37)),
        (145, (10, 23, -29, 14, 19, -29)),
        (184, (-11, 12, -23, -12, 22, -12)),
        (193, (-11, 12, -23, -12, 22, -12)),
    )
    for index, (link, joint) in enumerate(zip(links[1:], model['joints'])):
        link['joint'] = joint['name']
        link['role'] = joint['role']
        link.rotation_mode = 'XYZ'
        for frame, angles in poses:
            link.rotation_euler = Vector(joint['axis']) * radians(angles[index])
            link.keyframe_insert('rotation_euler', frame=frame, group=joint['name'])

    # These arcs identify the axes in the sequence. They are studio graphics.
    for name, link, offset, tilt, radius, pulse in (
        ('Shoulder', links[2], (0, -0.082, 0), (tau / 4, 0, 0), 0.083, (30, 44, 64, 80)),
        ('Elbow', links[3], (0, -0.083, 0), (tau / 4, 0, 0), 0.084, (64, 82, 106, 122)),
        ('Wrist', links[6], (0, 0, 0.015), (0, 0, 0), 0.052, (107, 122, 146, 162)),
    ):
        mark = arc(guides, f'{name} | axis highlight', radius, 0.07, 0.86, 0.0028, highlight)
        mark.parent = link
        mark.location, mark.rotation_euler = offset, tilt
        for frame, factor in zip(pulse, (0, 1, 1, 0)):
            mark.data.bevel_factor_end = factor
            mark.data.keyframe_insert('bevel_factor_end', frame=frame)

    for quadrant in range(4):
        start = quadrant / 4 + 0.011
        mark = arc(guides, f'Floor | quadrant {quadrant + 1}', 0.315, start,
                   start + 0.228, 0.0011, guide)
        mark.location.z = 0.001
    for tick in range(24):
        angle = tau * tick / 24
        inner = 0.333
        outer = 0.355 if tick % 6 == 0 else 0.343
        points = [(r * cos(angle), r * sin(angle), 0.001) for r in (inner, outer)]
        line(guides, f'Floor | tick {tick + 1:02}', points, 0.001, guide)

    ground_mesh = bpy.data.meshes.new('Shadow receiver')
    ground_mesh.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    ground = object_in(studio, 'Studio | shadow receiver', ground_mesh)
    ground.location.z = -0.001
    ground.is_shadow_catcher = True
    ground.data.materials.append(finish('Studio paper | #ebebeb', 'ebebeb', roughness=0.75))

    scene.world = bpy.data.worlds.new('Neutral fill')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value = (0.82, 0.89, 1, 1)
    background.inputs['Strength'].default_value = 0.23
    for name, position, energy, width, height in (
        ('Key', (-2.1, -3.2, 4.2), 190, 3.4, 2.6),
        ('Fill', (3.5, -0.6, 2.2), 95, 2.7, 3.2),
        ('Rim', (0.1, 2.2, 3.4), 170, 2.2, 1.8),
    ):
        light = bpy.data.lights.new(f'Softbox | {name}', 'AREA')
        light.energy, light.shape, light.size, light.size_y = energy, 'RECTANGLE', width, height
        lamp = object_in(studio, light.name, light)
        lamp.location = position
        aim(lamp, (0.25, 0, 0.45))

    camera_data = bpy.data.cameras.new('Hero camera')
    camera_data.type, camera_data.ortho_scale = 'ORTHO', 1.96
    camera = object_in(studio, 'Hero camera', camera_data)
    scene.camera = camera
    for frame in range(-3, 198, 4):
        phase = tau * (frame - 1) / 192
        camera.location = (2.02 + 0.40 * sin(phase), -4.65, 2.05 + 0.19 * cos(phase))
        aim(camera, (0.38, 0.01, 0.55))
        camera.keyframe_insert('location', frame=frame)
        camera.keyframe_insert('rotation_euler', frame=frame)

    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.use_persistent_data = True
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    tree = bpy.data.node_groups.new('Paper and contact shadows', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    render = tree.nodes.new('CompositorNodeRLayers')
    overlay = tree.nodes.new('CompositorNodeAlphaOver')
    overlay.inputs['Background'].default_value = linear('ebebeb')
    output = tree.nodes.new('NodeGroupOutput')
    tree.links.new(render.outputs['Image'], overlay.inputs['Foreground'])
    tree.links.new(overlay.outputs['Image'], output.inputs['Image'])
    render.location, overlay.location, output.location = (-260, 0), (0, 0), (240, 0)

    scene.render.resolution_x, scene.render.resolution_y = 1280, 960
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 192
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = '//frames/rosie_'
    for frame, name in ((1, 'Rosie at rest'), (30, 'Shoulder lift'), (65, 'Elbow reach'),
                        (112, 'Wrist sweep'), (146, 'Return'), (193, 'Loop closure')):
        scene.timeline_markers.new(name, frame=frame)
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
