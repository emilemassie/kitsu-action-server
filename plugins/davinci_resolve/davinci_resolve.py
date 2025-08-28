import gazu
from flask import request, jsonify
import os, subprocess, sys


class Plugin:
    def __init__(self, kitsu_action_server):

        self.kitsu_action_server = kitsu_action_server
        self.name = 'DaVinci Resolve'
        self.extension = '.drp'
        self.icon = os.path.join(os.path.dirname(__file__),'daVinci_resolve_icon.png') 
        self.plugins_path = os.path.join(os.path.dirname(__file__),'resolve_plugins') 
        sys.path.append(self.plugins_path)
        from get_resolve import getResolve
        self.get_resolve = getResolve

    def get_url_rules(self):

        funct_list = [
            {
                'url':'/resolve_send_timeline_to_kitsu',
                'function': self.export_resolve_timeline,
                'methods': ['POST']
            }
        ]
        return funct_list

    def export_resolve_timeline(self):
        data = request.form  # Use form data instead of JSON
        if not self.get_resolve()[0]:
            return 'Cannot Find Resolve, is the program open ?'
        
        try: 
           from resolve_timeline_exporter import TimelineExporter
        except Exception as eee:
           self.kitsu_action_server.update_log('RESOLVE PLUGINS ERROR :'+str(eee))
           return str(eee)

        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            self.kitsu_action_server.update_log('Recieved Data :' + str(dict(data)))

            self.kitsu_action_server.server_worker.set_environ(data)
            
            self.kitsu_action_server.show_notification.emit("DaVinci Resolve","Exporting Timeline", self.icon, 1000)

            self.kitsu_action_server.show_plugin_dialog_signal.emit(TimelineExporter, )



            #print(sys.executable)
            #subprocess.Popen([sys.executable, os.path.join(self.plugins_path,"resolve_timeline_exporter.py")], env=os.environ)
            #self.kitsu_action_server.show_plugin_window(TimelineExporter)
            return self.kitsu_action_server.server_worker.get_plugin_page('Exporting timeline to kitsu ...')

