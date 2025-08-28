import gazu
from flask import request, jsonify
import os, subprocess, sys


class Plugin:
    def __init__(self, kitsu_action_server):

        self.kitsu_action_server = kitsu_action_server
        self.name = 'OpenRV'
        self.extension = '.rv'
        self.icon = os.path.join(os.path.dirname(__file__),'OpenRVIcon.png')
        os.environ['RV_SUPPORT_PATH'] = os.path.join(os.path.dirname(__file__),'OpenRV_contents')
        self.plugins_path = os.path.join(os.path.dirname(__file__),'OpenRV_plugins') 
        sys.path.append(self.plugins_path)

    def get_url_rules(self):

        funct_list = [
            {
                'url':'/OpenRV',
                'function': self.open_ORV,
                'methods': ['POST']
            }
        ]
        return funct_list

    def open_ORV(self, file=None, args=[]):
        data = request.form  # Use form data instead of JSON
        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            self.kitsu_action_server.server_worker.set_environ(data)
            try:
                exec = self.kitsu_action_server.settings_dict['plugins'][self.name]['exec']
                command = [exec]
            except:
                return 'Cannot find OpenRV exec'
            if args: 
                command += args
            if file:
                self.kitsu_action_server.update_log('Opening File :' + file)
                command += [file]

        
            print(command)
            subprocess.Popen(command, env=os.environ.copy())
            self.kitsu_action_server.show_notification.emit("OpenRV","Launching OpenRV", self.icon, 1000)
            return self.kitsu_action_server.server_worker.get_plugin_page('Launching OpenRV ...')


            #print(sys.executable)
            #subprocess.Popen([sys.executable, os.path.join(self.plugins_path,"resolve_timeline_exporter.py")], env=os.environ)
            #self.kitsu_action_server.show_plugin_window(TimelineExporter)
            return self.kitsu_action_server.server_worker.get_plugin_page('Exporting timeline to kitsu ...')

