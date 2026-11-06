# Machine-vision camera

An annular strobe lights a passing part. The camera opens along its optical
axis and highlights the lens elements, the global-shutter CMOS die, and the
processing and Ethernet boards in sequence. The housing then closes and the
inspection repeats.

The scene develops the C-mount, ring light, sensor and GigE Vision camera
architecture from the [Deploy Robotic tour](https://deployrobotic.com/tour/)
and the Building Robots in Utah Drive bundle. The geometry is illustrative
and uses exaggerated travel to make the internal assemblies visible.

- [Editable Blender scene](industrial-camera.blend)
- [Video master](../../renders/industrial-camera/industrial-camera-loop.mp4) at 1280 × 1024 and 24 fps
- [Slides animation](../../renders/industrial-camera/industrial-camera-slides.gif) at 800 × 640 and 12 fps, repeating indefinitely

Open the scene in Blender 5.1.2 or later. Press **Space** to play the native
keyframes or choose **Render → Render Animation**. Render frames 1–240.
Frame 241 matches frame 1 and defines the loop boundary. The scene uses
procedural materials and a packed Saira font. See the
[Saira font license](../servomotor/OFL-Saira.txt).

To rebuild the scene, download [Saira from Google Fonts](https://github.com/google/fonts/tree/main/ofl/saira).
Run these commands from the repository root with Blender, FontTools, and
FFmpeg available.

```powershell
$font = Join-Path ([IO.Path]::GetTempPath()) 'Saira-Camera.ttf'
python -m fontTools.varLib.instancer 'Saira[wdth,wght].ttf' wdth=100 wght=625 -o $font
blender -b --disable-autoexec --python-exit-code 1 --python blender/industrial-camera/create_scene.py -- blender/industrial-camera/industrial-camera.blend $font
blender -b --disable-autoexec blender/industrial-camera/industrial-camera.blend -a
$frames = 'blender/industrial-camera/frames/camera_%04d.png'
ffmpeg -framerate 24 -i $frames -frames:v 240 -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/industrial-camera/industrial-camera-loop.mp4
ffmpeg -framerate 24 -i $frames -filter_complex 'fps=12,scale=800:640:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -frames:v 120 -loop 0 renders/industrial-camera/industrial-camera-slides.gif
```

To check a commit, configure the router's `tests.buildrobots` command to run
`blender -b --disable-autoexec blender/industrial-camera/industrial-camera.blend --python-exit-code 1 --python blender/industrial-camera/verify.py`,
then run `ai-app-router submit test --cwd .`.
