# Rosie 1400

An eight-second studio loop for slide 2 of *Building Robots in Utah*. Rosie
lifts at the shoulder, reaches through the elbow, rolls its wrist and returns
to its opening pose. Blue arcs mark the joints during the sequence. The shot
illustrates motion and omits a measurement scale.

The seven editable exterior meshes and their link hierarchy come from the
[AMR Rosie 1400 simulation kit](https://github.com/advanced-metal-research/rosie-sim-kits/tree/2cd53d559151785f9ca8f548472ee3e0af576685/sim/1400).
AMR's Rosie 1430 design study served as the starting reference.
The public kit supplies the CAD surfaces and joint frames for the
[Rosie 1400 shown on AMR's site](https://advancedmetalresearch.com/rosie).
See [the geometry license](AMR-LICENSE.txt).

Open `rosie.blend` in Blender 5.1.2 or later. The scene includes native joint
and camera keyframes, editable guide curves, procedural materials, lighting
and the paper background composite. Press **Space** to preview the timeline.
Frame 193 is the closure reference. Render frames 1–192 for the loop.
`verify.py` checks the joint frames, camera framing and loop closure.

- [Video master](../../renders/rosie/rosie-loop.mp4) is silent H.264 at 1280 × 960, 24 fps.
- [Slides animation](../../renders/rosie/rosie-slides.gif) loops continuously at 12 fps.
- [Poster](../../renders/rosie/rosie-poster.png) is the opening frame.

To rebuild the scene, place `rosie_1400.glb` from `sim/1400/glb/` and
`robot.json` from `sim/1400/` in a local directory. The GLB used here has
SHA-256 `fd3ecd2c1bbd507ea5a392302a187b6c8ae9ce5c754350ff7d2d3d74e3525087`.
From the repository root, with Blender and FFmpeg on PATH:

```powershell
blender -b --disable-autoexec --python-exit-code 1 --python blender/rosie/create_scene.py -- <kit-files-directory> blender/rosie/rosie.blend
blender -b --disable-autoexec blender/rosie/rosie.blend -a
ffmpeg -framerate 24 -i blender/rosie/frames/rosie_%04d.png -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/rosie/rosie-loop.mp4
Copy-Item blender/rosie/frames/rosie_0001.png renders/rosie/rosie-poster.png
ffmpeg -framerate 24 -i blender/rosie/frames/rosie_%04d.png -filter_complex 'fps=12,scale=720:540:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 renders/rosie/rosie-slides.gif
```
