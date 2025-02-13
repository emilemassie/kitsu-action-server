import os, sys, subprocess
from kitsu_connect import kitsu_plugin_button

class Plugin:
    def __init__(self, parent):
        self.parent = parent

        # Define name of the plugin app
        self.name = 'DaVinci Resolve'
        self.icon = self.icon = os.path.join(parent.root_folder, 'icons', 'resolve.png')
        self.extension = '.drp'
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
            exec = r'C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe'
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
            menu.addAction(icon, 'Open DaVinci Resolve', lambda: self.open_script())
        else:
            kitsu_item = self.parent.get_kitsu_item(item)

    def get_push_buttons(self, item, file_path=None):
        buttons = []
        self.item = item
        studio_button = kitsu_plugin_button('Open Davinci Resolve')
        studio_button.set_button_icon(self.icon)
        studio_button.released.connect(lambda: self.open_script())
        # buttons.append(studio_button)
        return buttons
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

        # Run the subprocess
        process = subprocess.Popen(command, env=env)

