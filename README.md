# Kitsu Action Server

<p align="center">
  <img src="https://github.com/user-attachments/assets/e74980ee-7e8f-411f-b046-da5269affd11" alt="Kitsu Action Server" width="600">
</p>

Kitsu Action Server is a local listener for the [Kitsu](https://kitsu.io) shot-tracking platform.  
It runs in the system tray and allows users to launch **Nuke**, **Blender**, or any other DCC with a plugin, ensuring the correct context environment and publishing features.

---

## 🚀 Setting Up Your Kitsu Website

To set up the application, add the following custom actions to your Kitsu settings:

<p align="center">
  <img src="https://github.com/user-attachments/assets/e74980ee-7e8f-411f-b046-da5269affd11" alt="Kitsu Custom Actions Setup" width="600">
</p>

The actions above show how the functions are linked to the listener server running locally.

---

## 🔌 How to Make a Plugin

Creating a plugin is straightforward! All plugins are stored in the **`plugins/`** folder.  
To create a new plugin, follow these minimum requirements:

1. Create a **folder** with the plugin name inside the `plugins/` directory.
2. Add a **`.py` file** with the same name as the plugin folder.
3. Inside this `.py` file, implement the following structure:

```python
import os
import subprocess
from flask import request, jsonify
import gazu

class Plugin:
    def __init__(self, kitsu_action_server):
        self.kitsu_action_server = kitsu_action_server
        self.name = 'nuke'
        self.extension = '.nk'
        self.icon = os.path.join(os.path.dirname(__file__), 'nuke.png')

    def get_url_rules(self):
        return [
            {'url': '/start-nuke', 'function': self.start_nuke, 'methods': ['POST']},
            {'url': '/start-nukex', 'function': lambda args=['--nukex']: self.start_nuke(args), 'methods': ['POST']}
        ]

    def open_file(self, file=None, args=[]):
        exec_path = self.kitsu_action_server.settings_dict['plugins'].get(self.name, {}).get('exec')
        if not exec_path:
            return 'Cannot find Nuke executable'

        command = [exec_path] + args + ([file] if file else [])
        os.environ['NUKE_PATH'] = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        subprocess.Popen(command, env=os.environ.copy())

        self.kitsu_action_server.show_notification.emit("Nuke Plugin", "Launching Nuke", self.icon, 1000)

    def create_new_version(self, version, version_folder, args=[], extension='.nk'):
        task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
        project_name = task['project'].get('code') or task['project']['name']
        filename = f"{os.environ['KITSU_SHOT']}_{task['task_type']['name']}".lower()

        if version:
            version_str = f"v{int(version):04d}"
            filename = f"{filename}_{version_str}"
            version_folder = os.path.join(version_folder, version_str)

        file_path = os.path.join(version_folder, f"{filename}{extension}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w'):
            pass  # Create an empty file

        self.open_file(file_path, args)

    def start_nuke(self, args=[]):
        data = request.form
        if not data:
            return jsonify({'error': 'No form data received'}), 400

        self.kitsu_action_server.update_log(f"Received Data:\n{dict(data)}")
        self.kitsu_action_server.server_worker.set_environ(data)

        os.environ['NUKE_PATH'] = os.path.join(os.path.dirname(__file__), 'nuke_plugins')
        version = self.kitsu_action_server.server_worker.get_version(self, args)

        return self.kitsu_action_server.server_worker.get_plugin_page('Launching Nuke...')
