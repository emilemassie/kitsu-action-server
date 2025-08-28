import gazu
from flask import request, jsonify
import os, subprocess

class Plugin:
    
    def __init__(self, kitsu_action_server):
        self.kitsu_action_server = kitsu_action_server
        self.name = 'Blender'
        self.extension = '.blend'
        self.icon = os.path.join(os.path.dirname(__file__),'blender.png') 


    def get_url_rules(self):

        funct_list = [
            {
                'url':'/start-blender',
                'function': self.start_blender,
                'methods': ['POST']
            }
        ]
        return funct_list

    def open_file(self,file=None,args=[]):
        try:
            exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
            command = [exec]
        except:
            return 'Cannot find Blender exec'
        if args: 
            command += args
        if file:
            self.kitsu_action_server.update_log('Opening File :' + file)
            command += [file]


        on_launch_script = os.path.join(os.path.dirname(__file__), 'scripts','on_launch.py')

        # Combine the executable and arguments
        command = [exec, file, '--python', on_launch_script] + args

        # Run the subprocess
        subprocess.Popen(command, env=os.environ.copy())
        print(command)
        self.kitsu_action_server.show_notification.emit("Blender Plugin","Launching Blender", self.icon, 1000)
        return

    def create_new_version(self,version, version_folder, args=[], extension='.blend'):
        
        task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
        project = task['project']
        project_root = os.environ['KITSU_PROJECT_ROOT']
        exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
       
        if project['code'] is not None:
            pname = project['code']
        else:
            pname = project['name']

        filename = f"{os.environ['KITSU_SHOT']}_{task['task_type']['name'].lower().replace(' ', '_')}"
        filename = filename.lower()
        file_path= version_folder
        if version:
            version_string = 'v'+str(int(version)).zfill(4)
            filename = filename+'_'+ version_string
            file_path = os.path.join(file_path,version_string)
        
        filename = filename+extension
        file_path = os.path.join(file_path,filename)
        
        self.kitsu_action_server.update_log('Creating : ' + str(file_path))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as fp:
            pass

        
        python_code = 'import bpy; '+ f'bpy.ops.wm.save_as_mainfile(filepath=r"{file_path}" ); bpy.ops.wm.quit_blender()'
        process = subprocess.run([exec, '-b',"--python-expr", python_code], env=os.environ.copy())
        #subprocess.Popen([exec, file_path], env=os.environ.copy())
        self.open_file(file_path)
        return file_path





    def start_blender(self):
        data = request.form  # Use form data instead of JSON
        
        try:
            exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
        except:
            return 'Cannot find blender exec'

        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            self.kitsu_action_server.update_log('Recieved Data :' + str(dict(data)))
            self.kitsu_action_server.server_worker.set_environ(data)

            version = self.kitsu_action_server.server_worker.get_version(self)

            return self.kitsu_action_server.server_worker.get_plugin_page('Lauching Blender ...')
            #jsonify({'message': 'First request received', 'data': data.to_dict()})
