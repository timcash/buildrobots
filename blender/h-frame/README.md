# H-frame production loop

The Rosie 1400 loader unloads the finished part to the front stand, picks up a
blank from the rear stand, and places it in the empty fixture while the other
Rosie 1400 welds. J9 turns the H-frame 180° to exchange the loading and welding
stations. The open studio view keeps both arms, the table and deck, both
fixtures, and the stands in view. The model is illustrative and has no
engineering scale.

Open `h-frame.blend` in Blender 5.1.2 or later. The rig retains the native
slotted action from AMR's
[`war-machine.blend`](https://github.com/advanced-metal-research/gradient-cli/blob/22f39a3479dccb01b3de83f70e40b2426f5e8825/buildrobots/v1/blender/war-machine.blend).
The full timeline runs from frame 1 through 2211 at about 24 fps and includes both production
cycles, J7/J8/J9, clamps, gripper jaws, part handoffs, growing weld beads and
the arc. The studio, finishes, skid and open dual-arm composition come from
the earlier H-frame hero. The scene is self-contained.

The [video](../../renders/h-frame/h-frame-loop.mp4),
[poster](../../renders/h-frame/h-frame-poster.jpg), and
[looping GIF](../../renders/h-frame/h-frame-slides.gif) use the same view.
The 1280 × 720 H.264 master follows the source `--hero` edit. It samples frames
601–1706 at step two and plays those 553 frames at 24 fps, or about 23 seconds.
The cut lands mid-weld after the bays exchange. The camera matches its
opening pose and speed at the cut.

From the repository root, with Blender and FFmpeg on PATH and the source scene
available in a sibling `gradient-cli` checkout:

```powershell
blender -b --disable-autoexec ../gradient-cli/buildrobots/v1/blender/war-machine.blend --python-exit-code 1 --python blender/h-frame/create_scene.py -- blender/h-frame/h-frame.blend
blender -b --disable-autoexec blender/h-frame/h-frame.blend -s 601 -e 1706 -j 2 -a
$frames = 601..1706 | Where-Object { ($_ - 601) % 2 -eq 0 } | ForEach-Object { "file 'blender/h-frame/frames/h-frame_{0:0000}.png'" -f $_ }
$frames | Set-Content -Encoding ascii h-frame-frames.txt
ffmpeg -f concat -safe 0 -r 24 -i h-frame-frames.txt -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart renders/h-frame/h-frame-loop.mp4
ffmpeg -i blender/h-frame/frames/h-frame_0601.png -frames:v 1 -q:v 2 renders/h-frame/h-frame-poster.jpg
ffmpeg -i renders/h-frame/h-frame-loop.mp4 -filter_complex 'fps=12,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 renders/h-frame/h-frame-slides.gif
```
