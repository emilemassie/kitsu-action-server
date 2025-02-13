import nuke, os, sys
import importlib.util

print('IMPORTING : Kitsu-connect-toolsets')

class colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\x1B[3m'

print(colors.BOLD, colors.UNDERLINE)
print(' KITSU_CONNECT ')
print(colors.RESET)

# Get the path to the plugins directory where menu.py is located
plugins_directory = os.path.dirname(os.path.dirname(__file__))
kitsu_connect_icons = os.path.join(plugins_directory, 'icons')

# Path to the tools directory relative to the plugins directory
tools_directory = os.path.join(plugins_directory, 'tools')

nuke.pluginAddPath('./tools')
nuke.pluginAddPath('./icons')

# Create parent menu under 'Nodes' menu
kitsu_menu = nuke.menu('Nodes').addMenu('Kitsu', icon = os.path.join(kitsu_connect_icons, 'kitsu.png'))


def import_module_from_path(module_path, module_name):
    '''
        The proper way to execute python scripts.
        This will only execute the <main> function inside of a .py file
    '''
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main() # Execute the main function
    return module

def add_tools_to_menu(menu, directory):
    '''
        Scans all the given folder and makes a menu out of it
    '''
    for dir_name in os.listdir(directory):
        
        dir_path = os.path.join(directory, dir_name)

        if dir_name != '__pycache__': # to avoid having __pycache__ files and folders.

            if os.path.isdir(dir_path): # if the folder exists, scan it

                submenu = menu.addMenu(dir_name, icon = dir_name+'.png')  # Assign submenu if it's a directory
                print(f'{colors.BLUE}{colors.BOLD}  Submenu found: {dir_name}{colors.RESET}')
                add_tools_to_menu(submenu, dir_path) # run the funciton recursivly for the new folders that might be found
            else:

                icon = dir_name[:-3]+'.png' # Define default icon

                if dir_name.endswith('.nk'):# if its a .nk file, then its a tool, so have it ready for import
                   
                    if os.path.exists(os.path.join(kitsu_connect_icons,icon)) == False: # if the icon doesnt exist, replace it with desired image
                        icon = 'nuke_script.png'

                    menu.addCommand(dir_name[:-3], lambda file_path=dir_path: nuke.nodePaste(file_path), icon = icon)
                
                elif dir_name.endswith('.py'): # if its a pure python script

                    if os.path.exists(os.path.join(kitsu_connect_icons,icon)) == False: # if the icon doesnt exist, replace it with desired image
                        icon = 'python_script.png'
                        
                    menu.addCommand(dir_name, lambda file_path=[dir_path, dir_name]: import_module_from_path(file_path[0], file_path[1]), icon = icon)
                print(f'{colors.GREEN}{colors.ITALIC}                 ADDED: {dir_path.replace(tools_directory+os.sep,"")+colors.WHITE}\n                        Icon: {icon}{colors.RESET}')

# Add tools to the menu recursively
add_tools_to_menu(kitsu_menu, tools_directory)
print(colors.BOLD)
print('---> Setup Successful !')
print(colors.RESET)