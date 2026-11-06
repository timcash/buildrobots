# Build Robots

Public Blender scenes and renders for Build Robots and the Building Robots in Utah slides.

- `blender/<component>/` holds editable scenes. Put external textures in a `textures/` directory alongside the scene, or pack them into the scene.
- `renders/<component>/` holds finished video masters and presentation derivatives.

Install Git LFS, then run `git lfs install` before cloning. In an existing clone, run `git lfs pull` to download the scene and render files. Git stores pointers for Blender files, videos, GIFs, HDR images, textures in the scene directories, and still images in the render directories. Blender backup files are ignored during normal staging and use LFS when deliberately included.

Open a scene in Blender 5.1 or newer. Press **Space** to preview its timeline or choose **Render → Render Animation** to render it with the saved scene settings. Set the output location in **Output Properties** before rendering. Scene folders can document any component-specific export settings.
