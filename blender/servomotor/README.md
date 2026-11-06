# Servomotor

The nine-second loop opens a brushless permanent-magnet servomotor to show
the wound stator, rotor magnets, stepped shaft and absolute encoder. The
housing lifts clear of the stator as the front and rear bells separate. Blue
highlights follow torque from the stator to the shaft, then show the encoder
that reads shaft position. The rotor, shaft and encoder target share an axis
and spin in sync. The scene is illustrative and has no engineering scale.

The original geometry follows the visual language of the
[Deploy Robotic tour](https://deployrobotic.com/tour/#supply-servo-motor).
The Blender file contains editable part assemblies, native animation keys,
procedural materials and the packed Saira label font. See the [font license](OFL-Saira.txt).

Open `servomotor.blend` in Blender 5.1.2 or later and press **Space** to preview
the timeline. Render frames 1–216. Frame 217 defines the loop boundary and is
excluded from both exports. The Blender check in `verify.py` covers camera
framing, clearance during shaft withdrawal, highlights and loop closure.

- [Video master](../../renders/servomotor/servomotor-loop.mp4) is silent H.264 at 1280 × 1024, 24 fps.
- [Slides animation](../../renders/servomotor/servomotor-slides.gif) loops continuously at 12 fps.

To rebuild the scene, use [Saira from Google Fonts](https://github.com/google/fonts/tree/main/ofl/saira)
and instantiate it at width 100 and weight 625 with FontTools. From the
repository root, with Blender and FFmpeg on PATH:

```powershell
$font = Join-Path ([IO.Path]::GetTempPath()) 'Saira-Labels.ttf'
python -m fontTools.varLib.instancer 'Saira[wdth,wght].ttf' wdth=100 wght=625 -o $font
blender -b --disable-autoexec --python-exit-code 1 --python blender/servomotor/create_scene.py -- blender/servomotor/servomotor.blend $font
blender -b --disable-autoexec blender/servomotor/servomotor.blend -a
ffmpeg -framerate 24 -i blender/servomotor/frames/servo_%04d.png -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/servomotor/servomotor-loop.mp4
ffmpeg -framerate 24 -i blender/servomotor/frames/servo_%04d.png -filter_complex 'fps=12,scale=800:640:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 renders/servomotor/servomotor-slides.gif
```

To verify a commit, configure the router's `tests.buildrobots` command to
invoke `blender -b --disable-autoexec blender/servomotor/servomotor.blend --python-exit-code 1 --python blender/servomotor/verify.py`,
then run `ai-app-router submit test --cwd .` from the repository root.
