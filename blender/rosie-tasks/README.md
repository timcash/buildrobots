# Rosie 1400 at work

Three Rosie 1400 arms paint, plasma-cut, and MIG-weld in a six-second loop
for slide 2 of *Building Robots in Utah*. The paint fan lays down a cobalt
stripe, the cutter traces an oval kerf, and the weld torch follows a fillet
joint. The finish fades during the reset so the next pass is visible.

The scene reuses the seven AMR CAD meshes and six joint frames from the
[original Rosie scene](../rosie/README.md). Each arm has its own editable
joint keys and tool. The workpieces, tools, and effects are illustrative
and have no engineering scale. The [CAD license](../rosie/AMR-LICENSE.txt)
and [Saira license](../servomotor/OFL-Saira.txt) apply to the reused assets.

Open `rosie-tasks.blend` in Blender 5.1.2 or later and press **Space** to
preview. The scene packs its font and shares the CAD meshes between arms.
Frame 145 is the closure reference. Render frames 1–144 for playback.

- [Video master](../../renders/rosie-tasks/rosie-tasks-loop.mp4) is silent H.264 at 1440 × 512 and 24 fps.
- [Poster](../../renders/rosie-tasks/rosie-tasks-poster.png) shows all three tools working.
- [Slides GIF](../../renders/rosie-tasks/rosie-tasks-slides.gif) repeats at 12 fps.
- [Full-bleed Slides GIF](../../renders/rosie-tasks/rosie-tasks-full-bleed.gif) repeats at 1088 × 612 and 12 fps behind the editable slide text.

To rebuild from the original scene, supply a static bold Saira TTF.
Run from the repository root with Blender and FFmpeg on PATH.

```powershell
blender -b --disable-autoexec blender/rosie/rosie.blend --python-exit-code 1 --python blender/rosie-tasks/create_task_scene.py -- blender/rosie-tasks/rosie-tasks.blend path/to/Saira-Bold.ttf
blender -b --disable-autoexec blender/rosie-tasks/rosie-tasks.blend -a
$frames = 'blender/rosie-tasks/frames/rosie-tasks_%04d.png'
$output = 'renders/rosie-tasks'
ffmpeg -framerate 24 -i $frames -an -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart "$output/rosie-tasks-loop.mp4"
Copy-Item blender/rosie-tasks/frames/rosie-tasks_0029.png "$output/rosie-tasks-poster.png"
ffmpeg -framerate 24 -i $frames -filter_complex 'fps=12,scale=1080:384:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle' -loop 0 "$output/rosie-tasks-slides.gif"
```

For the 16:9 export, take the three workstations from the existing MP4,
blend the joins across the floor, and extend the top edge behind the title.
Run from the repository root.

```powershell
$filter = @'
[0:v]fps=12,format=yuv444p,split=7[a][b][c][d][e][f][g];
[a]crop=360:512:48:0[left];
[b]crop=32:512:408:0[leftEdge];
[c]crop=32:512:536:0[midLeft];
[d]crop=336:512:568:0[mid];
[e]crop=32:512:904:0[midRight];
[f]crop=32:512:1032:0[rightEdge];
[g]crop=328:512:1064:0[right];
[leftEdge][midLeft]blend=all_expr='A*(31-X)/31+B*X/31'[seam1];
[midRight][rightEdge]blend=all_expr='A*(31-X)/31+B*X/31'[seam2];
[left][seam1][mid][seam2][right]hstack=inputs=5,pad=1088:612:0:100,fillborders=top=100:mode=smear,split[x][y];
[x]palettegen=max_colors=128[p];
[y][p]paletteuse=dither=bayer:bayer_scale=4
'@
ffmpeg -i renders/rosie-tasks/rosie-tasks-loop.mp4 -filter_complex $filter -loop 0 renders/rosie-tasks/rosie-tasks-full-bleed.gif
```
