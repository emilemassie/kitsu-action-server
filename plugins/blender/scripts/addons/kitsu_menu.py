bl_info = {"name" : "Kitsu Connect",   "category": "Menu",   "author": "Emile Massie-Vanasse"}

import bpy, os, sys

import gazu
gazu.set_host(os.getenv('KITSU_HOST')+'/api')
token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
gazu.client.set_tokens(token)


class KitsuMenu(bpy.types.Menu):
    bl_idname = "KITSUCONNECT_MT_MainMenu"
    bl_label = "Kitsu Connect"

    def draw(self, context):
        self.layout.operator("kc.publish_playblast")
        self.layout.operator('kc.update_save_file_path')

class kc_publish_playblast(bpy.types.Operator):
    bl_idname = "kc.publish_playblast"
    bl_label = "Publish Current Frame as JPEG Preview"

    def execute(self, context):
        from kitsu_export_frame import KitsuExportFrame
        KitsuExportFrame().run()
        return {'FINISHED'}
    
class update_save_file_path(bpy.types.Operator):
    bl_idname = "kc.update_save_file_path"
    bl_label = "Update Render Path"

    def execute(self, context):
        from kitsu_set_export_path import set_export_path
        return set_export_path()

def register():
    bpy.utils.register_class(KitsuMenu)
    bpy.utils.register_class(update_save_file_path)
    bpy.utils.register_class(kc_publish_playblast)
    bpy.types.TOPBAR_MT_editor_menus.append(menu_draw)

def unregister():
    bpy.utils.unregister_class(KitsuMenu)
    bpy.utils.unregister_class(update_save_file_path)
    bpy.utils.unregister_class(kc_publish_playblast)
    bpy.types.TOPBAR_MT_editor_menus.remove(menu_draw)

def menu_draw(self, context):
    self.layout.menu(KitsuMenu.bl_idname)

# default set export path and set the handler
from kitsu_set_export_path import set_export_path
set_export_path()


# Avoid adding it multiple times
import save_callbacks
save_callbacks.set_all_save_callbacks()




