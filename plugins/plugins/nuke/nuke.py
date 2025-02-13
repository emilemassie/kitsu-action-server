import os, sys, subprocess

class Plugin:
    def __init__(self, kitsu_connect):
        self.kitsu_connect = kitsu_connect

        # Define name of the plugin app
        self.name = 'Nuke 14.0v3'
        self.icon = os.path.join(kitsu_connect.root_folder, 'icons', 'nuke.png')
        self.extension = '.nk'
        # Takes the path for the executable file
        self.args = []
        self.item = None

        self.onPluginLoad()

    def context_menu_items(self, item=None):
        self.setEnviron()
        return {
                'Nuke Studio': self.launch_studio
            }

    def launch_studio(self):
        command = [self.kitsu_connect.plugin_core.settings_dict['plugins'][self.name]['exec'], '-studio']
        env = self.setEnviron()
        process = subprocess.Popen(command, env=env)

    def onPluginLoad(self):
        print('LOADED PLUGIN : ' + self.name)

    def get_executables(self):
        env = self.setEnviron()
        return {
            'exec': {
                'Nuke': [self.kitsu_connect.plugin_core.settings_dict['plugins'][self.name]['exec']], 
                'NukeX': [self.kitsu_connect.plugin_core.settings_dict['plugins'][self.name]['exec'],'-nukex']
                },
            'env': env
        }
    
    def launch(self, file=None):
        command = [exec_path, file]
        return command

    def setEnviron(self):
        nuke_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        data = {
            "NUKE_PATH": nuke_path
        }
        for i in data:
            if data[i]:
                os.environ[i] = data[i]
        return os.environ.copy()

    def task_tree_items(self, task):
        option_list = {
            'New Nuke Version': lambda: self.create_new_script(task)
        }
        return option_list
    
    def tree_right_click_action(self, menu, item=None, icon=None):
        if item:
            kitsu_item = self.kitsu_connect.get_kitsu_item(item)
            if kitsu_item is not None:
                item_type = kitsu_item['type'] 
                self.context_id = kitsu_item['id']
                if item_type == 'Sequence':
                    return
                if item_type == 'Shot':
                    return
                if item_type =='Task':
                    filepath = self.kitsu_connect.get_item_file_path(item)
                    project = kitsu_item['project']
                    if project['code'] is not None:
                        pname = project['code']
                    else:
                        pname = project['name']
                    filename = pname+'_'+kitsu_item['sequence']['name']+'_'+kitsu_item['entity']['name']+'_'+kitsu_item['task_type']['name']
                    menu.addAction(icon, 'Create New Nuke Script', lambda: self.create_new_script(filepath, filename))
            if item.whatsThis().startswith('FILE:'):
                file = item.whatsThis().split(':',1)[1]
                self.context_id = item.kitsu_connect().whatsThis().split(':',1)[1]
                menu.addAction(icon, 'Open in Nuke', lambda: self.open_script(file))
        else:
            menu.addAction(icon, 'Open Nuke Studio', lambda: self.open_script(None,'-studio'))
        
    def create_new_script(self, task):
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

        (file_name, filepath) = self.kitsu_connect.path_manager.get_task_file_name(task, version=new_version, extension='.nk')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as fp:
            pass
        self.open_script(filepath)
        return filepath
    
    def open_script(self, file=None, args=None):

        env = self.setEnviron()

        # Define the command-line arguments
        arguments = []#self.args
        if args:
            arguments.append(args)
        if file:  
            arguments.append(file)

        # Combine the executable and arguments
        command = [self.exec] + arguments
        self.kitsu_connect.update_log('Launching Nuke !', 'orange')
        if file:
            self.kitsu_connect.update_log(str(file))

        # Run the subprocess
        process = subprocess.Popen(command, env=env)

