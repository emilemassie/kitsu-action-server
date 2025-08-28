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
import_addon('RenderManager')