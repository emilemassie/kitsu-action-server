import os, sys, subprocess
from kitsu_connect import kitsu_plugin_button

class Plugin:
    def __init__(self, parent):
        self.parent = parent

        # Define name of the plugin app
        self.name = 'Nuke 14.0v3'
        self.icon = os.path.join(parent.root_folder, 'icons', 'nuke.png')
        self.extension = '.nk'
        # Takes the path for the executable file
        self.exec = self.getExec()
        self.args = []
        self.item = None

        self.onPluginLoad()

    def onPluginLoad(self):
        print('LOADED PLUGIN : ' + self.name)

    def launch(self):
        env = self.setEnviron()
        subprocess.Popen(self.exec , env=env)

    def setEnviron(self):

        host = self.parent.kitsu_host.text()
        username = self.parent.kitsu_username.text()
        nuke_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')

        if self.item:
            kitsu_item = self.item.kitsu_item
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
                "NUKE_PATH": nuke_path
            }
        else:
            data = {
                "KITSU_HOST": host,
                "KITSU_USER": username,
                "KITSU_ACCESS_TOKEN": self.parent.access_token,
                "KITSU_CONTEXT_ID": self.parent.context_id,
                "KITSU_PROJECT_ROOT": self.parent.project_root_label.text(),
                "KITSU_PROJECT": self.parent.project['name'],
                "NUKE_PATH": nuke_path
            }

        for i in data:
            if data[i]:
                os.environ[i] = data[i]
        return os.environ.copy()

    def getExec(self):
        if os.name == 'nt':
            # Do something specific for Windows
            exec = r'c:\Program Files\Nuke14.0v4\Nuke14.0.exe'
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

        if item:
            kitsu_item = self.parent.get_kitsu_item(item)
            if kitsu_item is not None:
                item_type = kitsu_item['type'] 
                self.context_id = kitsu_item['id']
                if item_type == 'Sequence':
                    return
                if item_type == 'Shot':
                    return
                if item_type =='Task':
                    filepath = self.parent.get_item_file_path(item)
                    project = kitsu_item['project']
                    if project['code'] is not None:
                        pname = project['code']
                    else:
                        pname = project['name']
                    filename = pname+'_'+kitsu_item['sequence']['name']+'_'+kitsu_item['entity']['name']+'_'+kitsu_item['task_type']['name']
                    menu.addAction(icon, 'Create New Nuke Script', lambda: self.create_new_script(filepath, filename))
            if item.whatsThis().startswith('FILE:'):
                file = item.whatsThis().split(':',1)[1]
                self.context_id = item.parent().whatsThis().split(':',1)[1]
                menu.addAction(icon, 'Open in Nuke', lambda: self.open_script(file))
        else:
            menu.addAction(icon, 'Open Nuke Studio', lambda: self.open_script(None,'-studio'))

    def get_push_buttons(self, item=None, file_path=None):
        buttons = []

        self.item = item

        if item.kitsu_item['task_type_name'] not in ['Compositing', 'Paint & Roto']:
            return buttons
        
        
        nv_button = kitsu_plugin_button('New Nuke Version')
        nv_button.set_button_icon(self.icon)
        nv_button.released.connect(lambda: self.create_new_script(item))
        buttons.append(nv_button)

        #studio_button = kitsu_plugin_button('Open Nuke Studio')
        #studio_button.set_button_icon(self.icon)
        #studio_button.released.connect(lambda: self.open_script(None,'-studio'))
        #buttons.append(studio_button)

        if file_path:
            nuke_button = kitsu_plugin_button('Open in Nuke')
            nuke_button.set_button_icon(self.icon)
            nuke_button.released.connect(lambda: self.open_script(file_path))
            buttons.append(nuke_button)
            
            nukex_button = kitsu_plugin_button('Open in NukeX')
            nukex_button.set_button_icon(self.icon)
            nukex_button.released.connect(lambda: self.open_script(file_path,'-nukex'))
            buttons.append(nukex_button)

        buttons.reverse()

        return buttons
        
    def create_new_script(self, item):
        version = 1

        folder_path = item.get_path()
        kitsu_item = item.kitsu_item
        project = self.parent.project

        if project['code'] is not None:
            pname = project['code']
        else:
            pname = project['name']
        filename = pname+'_'+kitsu_item['sequence_name']+'_'+kitsu_item['entity_name']+'_'+kitsu_item['task_type_name']

        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                    version = version +1
            version = 'v'+str(version).zfill(4)
            filename = filename+'_'+version+'.nk'
            filepath = os.path.join(folder_path, version)
            os.makedirs(filepath, exist_ok=True)
            complete_path = os.path.join(filepath,  filename)
            with open(complete_path, 'w') as fp:
                pass
            self.open_script(complete_path)
            self.parent.set_shot_tab(item)

            return complete_path
        else:
            return False
    
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
        print(command)

        # Run the subprocess
        process = subprocess.Popen(command, env=env)

