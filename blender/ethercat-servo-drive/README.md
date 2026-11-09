# EtherCAT servo drive

A book-style, DC-fed servo drive exchanges motion data over EtherCAT. Its
vented enclosure opens to reveal the IN and OUT ports, a populated control
board, the DC link and three-phase inverter, and the aluminum heat sink. Blue
highlights identify each assembly in turn. Tracers show data at the network
ports and on the control board, then mark switching on the three phase
busbars before the drive closes.

The new geometry develops the proportions and architecture of the
[Deploy Robotic drive](https://github.com/timcash/deployrobotic/blob/31356cd93fe25b1c8ef124ac2c4297a61eaf17be/cad/components/servo_drive.py)
and the original Building Robots in Utah Drive animation. Geometry and timing
are illustrative and not to scale. The [EtherCAT Technology Group](https://www.ethercat.org/technology/)
describes the network and its distributed clocks.

- [Editable Blender scene](ethercat-servo-drive.blend)
- [Video master](../../renders/ethercat-servo-drive/ethercat-servo-drive-loop.mp4) at 1280 × 1024 and 24 fps
- [Slides animation](../../renders/ethercat-servo-drive/ethercat-servo-drive-slides.gif) at 800 × 640 and 12 fps, repeating indefinitely

Open the scene in Blender 5.1.2 or later. Press **Space** to preview the
animation or choose **Render → Render Animation**. Render frames 1–240 for the
ten-second loop. Frame 241 matches frame 1 and marks the loop boundary. The
scene uses procedural materials and a packed [Saira font](../servomotor/OFL-Saira.txt).

To rebuild from the repository root, download the variable [Saira font](https://github.com/google/fonts/tree/main/ofl/saira)
and run the following with FontTools, Blender, and FFmpeg available.

```powershell
$font = Join-Path ([IO.Path]::GetTempPath()) 'Saira-Drive.ttf'
python -m fontTools.varLib.instancer 'Saira[wdth,wght].ttf' wdth=100 wght=625 -o $font
$scene = 'blender/ethercat-servo-drive/ethercat-servo-drive.blend'
$renders = 'renders/ethercat-servo-drive'
blender -b --disable-autoexec --python-exit-code 1 --python blender/ethercat-servo-drive/create_scene.py -- $scene $font
blender -b --disable-autoexec $scene -a
$frames = 'blender/ethercat-servo-drive/frames/drive_%04d.png'
ffmpeg -framerate 24 -i $frames -frames:v 240 -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart "$renders/ethercat-servo-drive-loop.mp4"
ffmpeg -framerate 24 -i $frames -filter_complex 'fps=12,scale=800:640:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -frames:v 120 -loop 0 "$renders/ethercat-servo-drive-slides.gif"
```

To verify a commit, configure the router's `tests.buildrobots` command to
run Blender with `-b --disable-autoexec`, the scene path, and
`--python-exit-code 1 --python blender/ethercat-servo-drive/verify.py`.
Then run `ai-app-router submit test --cwd .`.
