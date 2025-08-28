import bpy
from bpy.app.handlers import persistent

@persistent
def save_post_callback(dummy):
    # default set export path 
    from kitsu_set_export_path import set_export_path
    set_export_path()
    return


def save_pre_callback(dummy):
    return

def set_all_save_callbacks():
    # set all save callbacks
    if save_post_callback not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(save_post_callback)
    if save_pre_callback not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_pre_callback)



