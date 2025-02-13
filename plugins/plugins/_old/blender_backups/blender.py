import os, sys, subprocess
#from kitsu_connect import kitsu_plugin_button

class Plugin:
    def __init__(self, parent):
        self.parent = parent

        # Define name of the plugin app
        self.name = 'Blender'
        self.icon = self.icon = os.path.join(parent.root_folder, 'icons', 'blender.png')
        self.extension = '.blend'
        # Takes the path for the executable file
        self.exec = self.getExec()
        self.args = []
        self.item = None

        self.onPluginLoad()

    def onPluginLoad(self):
        print('LOADED PLUGIN : ' + self.name)
        pass
    
    def launch(self):
        env = self.setEnviron()
        subprocess.Popen(self.exec , env=env)

    def setEnviron(self):

        if self.item:
            kitsu_item = self.item.kitsu_item

            host = self.parent.kitsu_host.text()
            username = self.parent.kitsu_username.text()

            data = {
                "KITSU_HOST": host,
                "KITSU_USER": username,
                "KITSU_ACCESS_TOKEN": self.parent.access_token,
                "KITSU_CONTEXT_ID": self.parent.context_id,
                "KITSU_PROJECT_ROOT": self.parent.project_root_label.text(),
                "KITSU_PROJECT": self.parent.project['name'],
                "KITSU_SEQUENCE": kitsu_item['sequence_name'],
                "KITSU_SHOT": kitsu_item['entity_name'],
                "KITSU_TASK": kitsu_item['task_type_name'],
            }
            for i in data:
                try:
                    os.environ[i] = data[i]
                except Exception as eee:
                    print(i, str(eee))
        return os.environ.copy()

    def getExec(self):
        if os.name == 'nt':
            # Do something specific for Windows
            exec = r'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
        elif os.name == 'posix':
            if sys.platform == 'darwin':
                # Do something specific for macOS
                exec = '/Applications/Nuke15.0v4/Nuke15.0v4.app/Contents/MacOS/Nuke15.0'
            else:
                # Do something specific for Linux
                exec = ''
        else:
            raise NameError("Unknown operating system.")
        return exec
    
    def tree_right_click_action(self, menu, item=None, icon=None):
        if not item:
            menu.addAction(icon, 'Open Blender', lambda: self.open_script())
        else:
            kitsu_item = self.parent.get_kitsu_item(item)

    def get_push_buttons(self, item, file_path=None):
        buttons = []

        self.item = item
        nv_button = kitsu_plugin_button('New Blender File')
        nv_button.set_button_icon(self.icon)
        nv_button.released.connect(lambda: self.create_new_script(item))
        buttons.append(nv_button)

        if file_path and file_path.endswith(self.extension):
            nuke_button = kitsu_plugin_button('Open in Blender')
            nuke_button.set_button_icon(self.icon)
            nuke_button.released.connect(lambda: self.open_script(file_path))
            buttons.append(nuke_button)

        buttons.reverse()

        return buttons
    
    def open_script(self, file=None, args=None):

        env = self.setEnviron()
        # Define the command-line arguments
        arguments = []#self.args
        on_launch_script = os.path.join(os.path.dirname(__file__), 'scripts','on_launch.py')
        if args:
            arguments.append(args)
        if file:  
            arguments.append(file)


        # Combine the executable and arguments
        command = [self.exec, file, '--python', on_launch_script] + arguments

        # Run the subprocess
        process = subprocess.Popen(command, env=env)
    
    def create_new_script(self, item):
        env = self.setEnviron()
        version = 1

        folder_path = item.get_path()
        kitsu_item = item.kitsu_item
        project = self.parent.project

        if project['code'] is not None:
            pname = project['code']
        else:
            pname = project['name']
        filename = pname+'_asset_'+kitsu_item['entity_name']+'_'+kitsu_item['task_type_name']

        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                    version = version +1
            version = 'v'+str(version).zfill(4)
            filename = filename+'_'+version+'.blend'
            filepath = os.path.join(folder_path, version)
            os.makedirs(filepath, exist_ok=True)
            complete_path = os.path.join(filepath,  filename)

            python_code = 'import bpy\n'+ f'bpy.ops.wm.save_as_mainfile(filepath=r"{complete_path}")'


            process = subprocess.run([self.exec, '-b',"--python-expr", python_code], env=env)

            self.open_script(complete_path)
            self.parent.set_asset_tab(item)


            return complete_path
        else:
            return False

