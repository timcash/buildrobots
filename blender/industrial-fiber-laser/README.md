# Industrial fiber laser

A diode-pumped ytterbium fiber source opens to reveal the pump bank and gain
coil. A blue tracer follows the optical path into the delivery fiber and
through the head optics. The head welds a seam as the steel coupons move
beneath it, then the assembly closes to repeat the cycle.

The cabinet, delivery cable, and welding head develop the layout of the
[Deploy Robotic tour model](https://deployrobotic.com/tour/#supply-fiber-laser)
and the Building Robots in Utah Drive bundle. Geometry, travel, and light
colors are illustrative and not to scale. The [IPG fiber-laser
primer](https://www.ipgphotonics.com/en-us/technology/fiber-lasers-101)
describes the optical architecture.

- [Editable Blender scene](industrial-fiber-laser.blend)
- [Video master](../../renders/industrial-fiber-laser/industrial-fiber-laser-loop.mp4)
- [Looping Slides animation](../../renders/industrial-fiber-laser/industrial-fiber-laser-slides.gif)

Open the scene in Blender 5.1.2 or later. Press **Space** to preview the
keyframes or choose **Render → Render Animation**. The scene uses procedural
materials and packs [Saira](../servomotor/OFL-Saira.txt). Frames 1–240 make a
ten-second loop at 24 fps. Frame 241 matches the opening pose and marks the
loop boundary.

To rebuild from the repository root, download the variable [Saira
font](https://github.com/google/fonts/tree/main/ofl/saira). Use FontTools to
create the label weight, Blender to render the frames, and FFmpeg to encode
the two deliverables.

```powershell
$font = Join-Path ([IO.Path]::GetTempPath()) 'Saira-Laser.ttf'
python -m fontTools.varLib.instancer 'Saira[wdth,wght].ttf' wdth=100 wght=625 -o $font
$scene = 'blender/industrial-fiber-laser/industrial-fiber-laser.blend'
blender -b --disable-autoexec --python-exit-code 1 --python blender/industrial-fiber-laser/create_scene.py -- $scene $font
blender -b --disable-autoexec $scene -a
$frames = 'blender/industrial-fiber-laser/frames/laser_%04d.png'
$renders = 'renders/industrial-fiber-laser'
ffmpeg -framerate 24 -i $frames -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart "$renders/industrial-fiber-laser-loop.mp4"
ffmpeg -framerate 24 -i $frames -filter_complex 'fps=12,scale=800:640:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 "$renders/industrial-fiber-laser-slides.gif"
```

For verification, configure the router's `tests.buildrobots` command to
load the saved scene in background Blender with `--python-exit-code 1` and
`--python blender/industrial-fiber-laser/verify.py`, then run
`ai-app-router submit test --cwd .` on the commit.
