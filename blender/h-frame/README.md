# H-frame positioner

The War Machine H-frame carries two illustrative T-joint blanks between
a Rosie 1400 welder and a Rosie 1400 loader. The arms hold their parked
poses while J9 indexes 180°, dwells, and completes a second 180° index.
The open composition shows the table, deck, and staged parts on the
loader stands. The model is illustrative and has no engineering scale.

Open `h-frame.blend` in Blender 5.1.2 or later. The collections separate the
positioner CAD, fixtures, workpieces, stationary foundation, two six-axis
arm hierarchies, and studio. The timeline holds the native J9 and camera
keyframes. The blend contains all its materials.

The positioner, weld fixtures, arms, tooling, table, deck and stands come from
AMR's
`gradient-cli/buildrobots/v1/blender/war-machine.blend` at
`22f39a3479dccb01b3de83f70e40b2426f5e8825`. The skid, central bearing housing,
workpiece blanks in the fixture, bay marks, materials, and studio are
authored in `create_scene.py`. The arm poses come from frame 1 of the source
scene. The loader stand blanks reuse the source workpiece on both stands.

The [eight-second master](../../renders/h-frame/h-frame-loop.mp4) is a
1280 × 720, 24 fps, silent H.264 video. The site uses the master and its
first-frame poster. The Utah deck embeds the same video from Drive.
An animated GIF of the loop is also available for presentations. Render frames
1–192. Frame 193 repeats the first pose to define the loop boundary. Camera
keys outside the rendered range preserve its speed through the seam.

From the repository root, with Blender and FFmpeg on PATH:

```powershell
blender -b --disable-autoexec ../gradient-cli/buildrobots/v1/blender/war-machine.blend --python-exit-code 1 --python blender/h-frame/create_scene.py -- blender/h-frame/h-frame.blend
blender -b --disable-autoexec blender/h-frame/h-frame.blend -a
ffmpeg -framerate 24 -i blender/h-frame/frames/h-frame_%04d.png -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/h-frame/h-frame-loop.mp4
ffmpeg -i renders/h-frame/h-frame-loop.mp4 -frames:v 1 -q:v 2 renders/h-frame/h-frame-poster.jpg
ffmpeg -i renders/h-frame/h-frame-loop.mp4 -filter_complex 'fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4' -loop 0 renders/h-frame/h-frame-slides.gif
```
