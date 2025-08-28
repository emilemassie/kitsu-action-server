import bpy
import gazu
import os, sys

def set_export_path():
    kitsu_task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
    version = 'v'+bpy.path.basename(bpy.data.filepath).split(".")[0].split('_v')[-1]
    folder_stepback = os.path.dirname(os.path.dirname(os.path.dirname(bpy.data.filepath)))
    base_name = os.path.basename(bpy.data.filepath).split(".")[0]

    task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
    if task['task_type']['for_entity'].lower() == 'shot':
        export_file_path = os.path.abspath(os.path.join(os.path.dirname(folder_stepback), 'media', kitsu_task['task_type']['name'].lower().replace(' ', '_'),version,  base_name))
    else:
        export_file_path = os.path.abspath(os.path.join(folder_stepback, 'media', version,  base_name))
        
    print(export_file_path)
    bpy.context.scene.render.filepath = export_file_path
    return {'FINISHED'}