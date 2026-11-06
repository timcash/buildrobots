# Strain-wave gear reducer

One turn of the elliptical wave generator carries two opposing mesh zones
around the fixed circular spline. The 200-tooth flexspline and its output
flange turn backward by two teeth relative to the fixed 202-tooth ring.
The camera pulls back as the four assemblies separate. Blue identifies the
cam, fixed ring, flexible cup, and output flange in sequence. The loop then
reseats the components. The scene exaggerates the cam lift and tooth geometry
for readability and uses illustrative dimensions.

The scene develops the assembly shown in the [Deploy Robotic tour](https://deployrobotic.com/tour/#gears)
and the reducer from the Building Robots in Utah Drive bundle. Its gear teeth,
thin cup, races, fasteners, and cam are editable geometry. Two shape keys
animate the cup deformation in phase with the input angle. The scene uses procedural
materials and a packed Saira font, with no external textures or playback scripts.
See the [Saira font license](../servomotor/OFL-Saira.txt).

- [Editable Blender scene](reducer.blend)
- [Video master](../../renders/reducer/reducer-loop.mp4) at 1280 × 1024 and 24 fps
- [Slides animation](../../renders/reducer/reducer-slides.gif) at 800 × 640 and 12 fps, repeating indefinitely

Open the scene in Blender 5.1.2 or later and press **Space** to preview. Render
frames 1–240. Frame 241 defines the loop boundary. To rebuild the scene, use the
same Saira font instance described in the [servomotor notes](../servomotor/README.md).
Run these commands from the repository root with Blender and FFmpeg on PATH.

```powershell
blender -b --disable-autoexec --python-exit-code 1 --python blender/reducer/create_scene.py -- blender/reducer/reducer.blend $font
blender -b --disable-autoexec blender/reducer/reducer.blend -a
ffmpeg -framerate 24 -i blender/reducer/frames/reducer_%04d.png -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/reducer/reducer-loop.mp4
ffmpeg -framerate 24 -i blender/reducer/frames/reducer_%04d.png -filter_complex 'fps=12,scale=800:640:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 renders/reducer/reducer-slides.gif
```

To check a commit, configure the router's `tests.buildrobots` command to run
`blender -b --disable-autoexec blender/reducer/reducer.blend --python-exit-code 1 --python blender/reducer/verify.py`,
then run `ai-app-router submit test --cwd .`.
