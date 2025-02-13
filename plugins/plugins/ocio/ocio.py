import os, sys, subprocess
import json

class Plugin:
    def __init__(self, kitsu_connect):
        self.kitsu_connect = kitsu_connect

        # Define name of the plugin app
        self.name = 'OCIO'
        self.icon = os.path.join(kitsu_connect.root_folder, 'icons', 'ocio.png')
        self.extension = '.ocio'
        # Takes the path for the executable file
        self.args = []
        self.item = None

        self.onPluginLoad()

    def onPluginLoad(self):
        with open(self.kitsu_connect.plugin_core.settings_file, 'r') as f:
            settings_dict = json.load(f)
        try:
            file_path = settings_dict['plugins'][self.name]['exec']
        except:
            file_path = None
        print(file_path)
        if file_path:
            os.environ['OCIO'] = file_path
            self.kitsu_connect.update_log('ocio set to : ' + os.environ['OCIO'])
        print('LOADED PLUGIN : ' + self.name)


    def setEnviron(self):
        nuke_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        data = {
            "NUKE_PATH": nuke_path
        }
        for i in data:
            if data[i]:
                os.environ[i] = data[i]
        return os.environ.copy()
    