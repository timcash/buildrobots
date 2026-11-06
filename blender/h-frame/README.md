# H-frame positioner

The isolated War Machine H-frame carries two illustrative T-joint blanks.
The fixed bearing and skid stay put while the J9 assembly indexes 180°,
dwells, and returns through a second 180° index. The model is illustrative
and has no engineering scale.

Open `h-frame.blend` in Blender 5.1.2 or later. The collections separate the
positioner CAD, fixtures, workpieces, bearing, and studio. The timeline holds
the native J9 and camera keyframes. The blend contains all its materials.

The positioner and weld-fixture meshes come from AMR's
`gradient-cli/buildrobots/v1/blender/war-machine.blend` at
`22f39a3479dccb01b3de83f70e40b2426f5e8825`. The skid, central bearing housing,
workpieces, bay marks, materials, and studio are authored in `create_scene.py`.

The [eight-second master](../../renders/h-frame/h-frame-loop.mp4) is a
1280 × 720, 24 fps, silent H.264 video. The site uses the master and its
first-frame poster. The Utah deck uses the same sequence as an animated GIF
so the slide can repeat it continuously. Render frames 1–192. Frame 193
repeats the first pose to define the loop boundary. Camera keys outside the
rendered range preserve its speed through the seam.

From the repository root, with Blender and FFmpeg on PATH:

```powershell
blender -b --disable-autoexec blender/h-frame/h-frame.blend -a
ffmpeg -framerate 24 -i blender/h-frame/frames/h-frame_%04d.png -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/h-frame/h-frame-loop.mp4
ffmpeg -i renders/h-frame/h-frame-loop.mp4 -frames:v 1 -q:v 2 renders/h-frame/h-frame-poster.jpg
ffmpeg -i renders/h-frame/h-frame-loop.mp4 -filter_complex 'fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4' -loop 0 renders/h-frame/h-frame-slides.gif
```
