bl_info = {
    "name": "connector",
    "blender": (2, 80, 0),
    "category": "Rising",
}

from ctypes import util
import bpy

import os
import sys
#root_dir = os.path.dirname(bpy.data.filepath)
#print(root_dir)
#tools_root = root_dir.split("hopper")[0]
#print(tools_root)
#tools_plugin_folder = tools_root + "tools"
#print(tools_plugin_folder)
#sys.path.append(tools_plugin_folder)

from . import mapParser, objectsFabric, gui, rjoints, collisions, overrites, common_systems, utils

print("reloaded")

_modules = (
    utils,
    common_systems,
    mapParser,
    objectsFabric,
    rjoints,
    collisions,
    overrites,
    gui,
)

def register():
    
    import importlib
    for mdl in _modules:
        importlib.reload(mdl)
        
    for mdl in _modules:
        if "register" in dir(mdl):
            mdl.register()
        
def unregister():
    for mdl in reversed(_modules):
        if "unregister" in dir(mdl):
            mdl.unregister()
        
if __name__ == '__main__':
    register()