import gazu
from flask import request, jsonify
import os, subprocess


class Plugin:
    
    def __init__(self, kitsu_action_server):
        self.kitsu_action_server = kitsu_action_server
        self.name = 'nuke'
        self.extension = '.nk'
        self.icon = os.path.join(os.path.dirname(__file__),'nuke_icon.png') 


    def get_url_rules(self):

        funct_list = [
            {
                'url':'/start-nuke',
                'function': self.start_nuke,
                'methods': ['POST']
            },
            {
                'url':'/start-nukex',
                'function': lambda args=['--nukex']: self.start_nuke(args),
                'methods': ['POST']
            },
            {
                'url':'/start-nuke-studio',
                'function': self.start_nuke_studio,
                'methods': ['POST']
            }
        ]
        return funct_list

    def open_file(self,file=None,args=[]):
        try:
            exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
            command = [exec]
        except:
            return 'Cannot find nuke exec'
        if args: 
            command += args
        if file:
            self.kitsu_action_server.update_log('Opening File :' + file)
            command += [file]

        #self.kitsu_action_server.server_worker.set_environ(data)

        nuke_plugin_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        os.environ['NUKE_PATH'] = nuke_plugin_path

        print(command)

        subprocess.Popen(command, env=os.environ.copy())
        self.kitsu_action_server.show_notification.emit("Nuke Plugin","Launching Nuke", self.icon, 1000)


    def create_new_version(self,version, version_folder, args=[], extension='.nk'):
        
        task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
        project = task['project']
        project_root = os.environ['KITSU_PROJECT_ROOT']
       
        if project['code'] is not None:
            pname = project['code']
        else:
            pname = project['name']

        filename = f"{os.environ['KITSU_SHOT']}_{task['task_type']['name']}"
        filename = filename.lower()
        file_path= version_folder
        if version:
            version_string = 'v'+str(int(version)).zfill(4)
            filename = filename+'_'+ version_string
            file_path = os.path.join(file_path,version_string)
        if extension:
            print(filename, extension)
            filename = filename+extension
        file_path = os.path.join(file_path,filename)
        
        self.kitsu_action_server.update_log('Creating : ' + str(file_path))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as fp:
            pass

        self.open_file(file_path, args)

    def start_nuke_studio(self):
        data = request.form  # Use form data instead of JSON
    
        try:
            exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
        except:
            return 'Cannot find nuke exec'

        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            self.kitsu_action_server.update_log('Recieved Data :' + str(dict(data)))

            self.kitsu_action_server.server_worker.set_environ(data)

            nuke_plugin_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
            os.environ['NUKE_PATH'] = nuke_plugin_path

            command = [exec, '--studio']
            subprocess.Popen(command, env=os.environ.copy())
            
            self.kitsu_action_server.show_notification.emit("Nuke Plugin","Launching Nuke Studio", self.icon, 1000)
            return self.kitsu_action_server.server_worker.get_plugin_page('Lauching Nuke Studio ...')

    def start_nuke(self, args=[]):
        data = request.form  # Use form data instead of JSON
        try:
            exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
        except:
            return 'Cannot find nuke exec'

        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            self.kitsu_action_server.update_log('Recieved Data :\n' + str(dict(data)))
            self.kitsu_action_server.server_worker.set_environ(data)

            nuke_plugin_path = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
            os.environ['NUKE_PATH'] = nuke_plugin_path

            version = self.kitsu_action_server.server_worker.get_version(self, args)
            return self.kitsu_action_server.server_worker.get_plugin_page('Lauching Nuke ...')
            #jsonify({'message': 'First request received', 'data': data.to_dict()})
