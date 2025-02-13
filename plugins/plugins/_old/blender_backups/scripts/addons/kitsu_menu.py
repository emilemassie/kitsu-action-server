import bpy, os, sys

bl_info = {"name" : "Kitsu Connect",   "category": "Menu",   "author": "Emile Massie-Vanasse"}

#sys.path.append(os.environ['KITSU_CONNECT_PACKAGES'])
import gazu



gazu.set_host(os.getenv('KITSU_HOST')+'/api')
token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
gazu.client.set_tokens(token)



from kitsu_export_frame import KitsuExportFrame


class KitsuMenu(bpy.types.Menu):
    bl_idname = "KITSUCONNECT_MT_MainMenu"
    bl_label = "Kitsu Connect"

    def draw(self, context):
        self.layout.operator("kc.publish_playblast")
        self.layout.operator('kc.update_save_file_path')

class kc_publish_playblast(bpy.types.Operator):
    bl_idname = "kc.publish_playblast"
    bl_label = "Publish Current Frame As Jpeg"

    def execute(self, context):
        KitsuExportFrame().run()
        return {'FINISHED'}
    
class update_save_file_path(bpy.types.Operator):
    bl_idname = "kc.update_save_file_path"
    bl_label = "Update Render Path"

    def execute(self, context):
        version = 'v'+bpy.path.basename(bpy.data.filepath).split(".")[0].split('_v')[-1]
        export_file_path = os.path.join(os.environ['KITSU_PROJECT_ROOT'], 'assets', os.environ['KITSU_SHOT'], os.environ['KITSU_TASK'], 'renders', version, bpy.path.basename(bpy.data.filepath).split(".")[0]+'.####.exr')
        bpy.context.scene.render.filepath = export_file_path

        return {'FINISHED'}

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
