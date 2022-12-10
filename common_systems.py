import bpy

from . import utils

class Initiate(bpy.types.Operator):
    bl_idname = "scene.initiate"
    bl_label = "Initiate scene"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.scene.render.fps = 60
        context.scene.render.fps_base = 1
        context.scene.frame_end = 10000
        bpy.ops.view3d.view_axis(type = 'FRONT')
        return {'FINISHED'}


class ReloadScene(bpy.types.Operator):
    
    bl_idname = "object.reload_scene"
    bl_label = "Reload scene operator"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.scene.process_libraries()
        bpy.ops.wm.objects_cleanup()
        path = bpy.data.filepath
        if not path:
            bpy.ops.wm.save_as_mainfile("INVOKE_AREA")
            return
        bpy.ops.wm.save_mainfile()
        self.report({"INFO"}, "Saved & Reloaded")
        bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath=path)
        return {'FINISHED'}
    
class ExportScene(bpy.types.Operator):
    
    bl_idname = "object.export_scene"
    bl_label = "Export scene operator"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.screen.frame_jump(1)
        bpy.ops.object.reload_scene()
        bpy.ops.scene.export_scene()
        self.report({"INFO"}, "Scene export complete")
        return {'FINISHED'}

class ProcessLibraries(bpy.types.Operator):
    
    bl_idname = "scene.process_libraries"
    bl_label = "Process libraries"
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        for lib in bpy.data.libraries:
            if not bpy.path.is_subdir(lib.filepath, utils.get_data_path()):
                continue
            lib.filepath = bpy.path.relpath(lib.filepath)
        return {'FINISHED'}

class ObjectCleanup(bpy.types.Operator):
    """delete objects and their derivatives"""
    bl_idname = "wm.objects_cleanup"
    bl_label = "Cleanup objects"
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):        
        for obj in context.scene.objects:
            if not obj.is_instancer:
                continue
            lib = obj.instance_collection.library
            if lib is None:
                continue
            collection = bpy.data.collections[obj.instance_collection.name]
            if not utils.get_cluster_collection(collection):
                continue
            
            root = utils.get_cluster_from_collection_rec(obj.users_collection[0])
            if root is None:
                continue
            object_target = utils.find_collection(root, "Objects")
            if object_target is None:
                continue
            
            for c_obj in obj.users_collection:
                c_obj.objects.unlink(obj)
            object_target.objects.link(obj)
        
        return {'FINISHED'}

_classes = (
    Initiate,
    ReloadScene,
    ExportScene,
    ProcessLibraries,
    ObjectCleanup,
)
    
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)