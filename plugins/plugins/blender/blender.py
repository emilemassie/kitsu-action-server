import os, sys, subprocess
#from kitsu_connect import kitsu_plugin_button

class Plugin:
    def __init__(self, parent):
        self.parent = parent
        self.kitsu_connect = parent

        # Define name of the plugin app
        self.name = 'Blender'
        self.icon = self.icon = os.path.join(parent.root_folder, 'icons', 'blender.png')
        self.extension = '.blend'
        # Takes the path for the executable file
        self.args = []
        self.item = None

        self.onPluginLoad()

    def onPluginLoad(self):
        print('LOADED PLUGIN : ' + self.name)
        #self.parent.update_log('LOADED PLUGIN : ' + self.name)
        pass
    
    def launch(self):
        env = self.setEnviron()
        subprocess.Popen(self.exec , env=env)

    def setEnviron(self):
        #nuke_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        data = {
            #"NUKE_PATH": nuke_path
        }
        for i in data:
            if data[i]:
                os.environ[i] = data[i]
        return os.environ.copy()

    def task_tree_items(self, task):
        option_list = {
            'New Blender Version': lambda: self.create_new_script(task)
        }
        return option_list

    def get_executables(self):
        env = self.setEnviron()
        return {
            'exec': {
                'Blender': [self.kitsu_connect.plugin_core.settings_dict['plugins'][self.name]['exec']] 
                },
            'env': env
        }


    def create_new_script(self, task):
        env = self.setEnviron()
        version = 1
        versions = self.kitsu_connect.path_manager.get_versions_for_task(task)
        if versions:
            # Extract version numbers as integers
            version_numbers = [int(key[1:]) for key in versions.keys()]
            # Find the maximum version number
            new_version = max(version_numbers)+1
        else:
            # Default to v001 if the dictionary is empty
            new_version = 1

        (file_name, filepath) = self.kitsu_connect.path_manager.get_task_file_name(task, version=new_version, extension='.blend')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        python_code = 'import bpy\n'+ f'bpy.ops.wm.save_as_mainfile(filepath=r"{filepath}")'
        process = subprocess.run([self.exec, '-b',"--python-expr", python_code], env=env)
        self.open_file(filepath)
        return filepath
    
    def open_file(self, file=None, args=None):
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
    
   