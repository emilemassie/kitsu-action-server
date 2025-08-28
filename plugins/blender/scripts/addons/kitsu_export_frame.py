import bpy
import gazu
import tempfile
import os

class KitsuExportFrame:
    def __init__(self):
        self.saved_settings = self.save_render_settings()
            
    # Function to save the current render settings
    def save_render_settings(self):
        render = bpy.context.scene.render
        saved_settings = {
            'filepath': render.filepath,
            'image_settings.file_format': render.image_settings.file_format,
            'image_settings.color_mode': render.image_settings.color_mode,
            'image_settings.color_depth': render.image_settings.color_depth,
            'resolution_x': render.resolution_x,
            'resolution_y': render.resolution_y,
            'resolution_percentage': render.resolution_percentage
        }
        return saved_settings

    # Function to restore saved render settings
    def restore_render_settings(self, saved_settings):
        render = bpy.context.scene.render
        render.filepath = saved_settings['filepath']
        render.image_settings.file_format = saved_settings['image_settings.file_format']
        render.image_settings.color_mode = saved_settings['image_settings.color_mode']
        render.image_settings.color_depth = saved_settings['image_settings.color_depth']
        render.resolution_x = saved_settings['resolution_x']
        render.resolution_y = saved_settings['resolution_y']
        render.resolution_percentage = saved_settings['resolution_percentage']

    def run(self):
        # Save current render settings
        saved_settings = self.save_render_settings()

        # Get project name and current frame
        project_name = bpy.path.basename(bpy.data.filepath).split(".")[0]  # Get the project name from the file
        current_frame = bpy.context.scene.frame_current  # Get the current frame number

         # Create a clean temporary file path
        temp_dir = tempfile.gettempdir()  # Get the system's temp directory
        temp_filepath = os.path.join(temp_dir, f"{project_name}_preview_{current_frame}.jpg")

        # Set render settings for exporting current frame as JPEG
        bpy.context.scene.render.filepath = temp_filepath
        bpy.context.scene.render.image_settings.file_format = 'JPEG'
        bpy.context.scene.render.image_settings.color_mode = 'RGB'
        bpy.context.scene.render.image_settings.color_depth = '8'  # JPEG is 8-bit

        # Render the current frame and save as JPEG
        bpy.ops.render.render(write_still=True)

        # Restore the original render settings
        self.restore_render_settings(self.saved_settings)

        # Publish preview to Kitsu

        status = gazu.task.get_task_status_by_short_name("wip")
        task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
        comment = gazu.task.add_comment(task, status, f'{os.path.basename(temp_filepath)}<br><br><u><b>Source file :</b></u><br>{bpy.data.filepath}\n<u><b>Scene Render Path :</u></b><br>{bpy.context.scene.render.filepath}')

        self.preview_file = gazu.task.add_preview(
                task,
                comment,
                temp_filepath
            )

        # Delete the temporary file after use
        os.remove(temp_filepath)

         # Show the Blender message box
        self.show_message_box("Export Complete", f"Preview {project_name}_frame_{current_frame}.jpg was successfully exported.")

    def show_message_box(self, title="Message Box", message=""):
        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title=title, icon='FILE_TICK')
