import bpy, sys, os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'site-packages'))




def import_addon(addon_module_name):
    addon_module = __import__(addon_module_name)
    # Register the addon
    if hasattr(addon_module, "register"):
        addon_module.register()

# Path to the directory containing the addon
addon_directory = os.path.join(os.path.dirname(__file__), 'addons')
# Add the directory to sys.path
if addon_directory not in sys.path:
    sys.path.append(addon_directory)

import_addon('kitsu_menu')

from bpy.app.handlers import persistent

@persistent
def load_handler(scene):
    version = 'v'+bpy.path.basename(bpy.data.filepath).split(".")[0].split('_v')[-1]
    export_file_path = os.path.join(os.environ['KITSU_PROJECT_ROOT'], 'assets', os.environ['KITSU_SHOT'], os.environ['KITSU_TASK'], 'renders', version, bpy.path.basename(bpy.data.filepath).split(".")[0]+'.####.exr')
    bpy.context.scene.render.filepath = export_file_path

    # Access the render settings
    render = bpy.context.scene.render

    # Set the file format to EXR
    render.image_settings.file_format = 'OPEN_EXR'

    # Configure the EXR compression settings
    render.image_settings.exr_codec = 'DWAA'  # Set the EXR compression to DWAA (Discrete Wavelet Approximation)
    render.image_settings.color_depth = '16'
    os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
    print("Load Handler:", bpy.data.filepath)

bpy.app.handlers.load_post.append(load_handler)
bpy.app.handlers.save_post.append(load_handler)

