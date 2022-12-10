import bpy
import bmesh
from bpy_extras.object_utils import AddObjectHelper

from . import utils

def get_possible_overrite_list(object):
    if not object.is_instancer:
        print("Object {} is not an instancer".format(object))
        return
    
    linked_collection = object.instance_collection
    library = linked_collection.library
    if library is None:
        print("Object {} has no library".format(object))
        return
    
    cluster_root = utils.get_cluster_collection(object.instance_collection)
    if cluster_root is None:
        print("Object {} is not a cluster".format(object))
        return

    modifiers_src_object_names = []
    modifiers_src_modifers_names = []
    
    collisions_collection = utils.find_collection(cluster_root, "Collision")
    if collisions_collection is not None:
        print ("cc obj", collisions_collection.objects)
        for src in collisions_collection.objects:
            
            print("obj {} modifiers {}".format(src, src.modifiers))
            for mod_src in src.modifiers:
                if mod_src.type != 'NODES':
                    continue
                if mod_src.node_group.name == "CollisionCircle" or mod_src.node_group.name == "CollisionPolygon":                
                    modifiers_src_object_names.append(src.name)
                    modifiers_src_modifers_names.append(mod_src.name)
           
    beams_collection = utils.find_collection(cluster_root, "Beams")    
    if beams_collection is not None:
        for src in beams_collection.objects:
            for mod_src in src.modifiers:
                if mod_src.type != 'NODES':
                    continue
                if mod_src.node_group.name == "Beam":
                    modifiers_src_object_names.append(src.name)
                    modifiers_src_modifers_names.append(mod_src.name)       
      
    return modifiers_src_object_names, modifiers_src_modifers_names                

class RISING_OT_CreateOverride(bpy.types.Operator, AddObjectHelper):
    
    bl_idname = "overrites.create_override"
    bl_label = "Create override"
    
    target_object_name: bpy.props.StringProperty(name = 'target_object_name', default = '')
    source_element_name: bpy.props.StringProperty(name = 'source_element_name', default = '')
    modifier_name: bpy.props.StringProperty(name = 'modifier_name', default = '')
    
#    @classmethod
#    def poll(cls, context):
#        object = context.object
#        return object.is_instancer and (object.library is not None)

    def create_overrides_object(self, context):
        
        root = utils.get_cluster_from_active_object(context)
        
        mesh = bpy.data.meshes.new("overrides")
        
        bm = bmesh.new()
        bm.verts.new((0, 0, 0))
        
        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)
        
        from bpy_extras import object_utils
        new_override = object_utils.object_data_add(context, mesh, operator=self)
        
        overrites_collection = utils.find_collection(root, "Overrites")
        print("overrites_collection", overrites_collection)
        if overrites_collection is None:
            overrites_collection = bpy.data.collections.new("Overrites")
            root.children.link(overrites_collection)
        
        for coll in new_override.users_collection:
            coll.objects.unlink(new_override)
        overrites_collection.objects.link(new_override)
        
        return new_override

    def execute(self, context):
        target_object = bpy.data.objects[self.target_object_name]
        
        overrides_object = utils.find_object(target_object, "overrides")
        if overrides_object is None:
            overrides_object = self.create_overrides_object(context)
            overrides_object.parent = target_object
            
        source_element = target_object.instance_collection.all_objects[self.source_element_name]
        mod_src = source_element.modifiers[self.modifier_name]
        
        mod_target = overrides_object.get(mod_src.name, None)
        if mod_target is None:
            mod_target = overrides_object.modifiers.new(mod_src.name, mod_src.type)
        print("ch", mod_src, mod_target)
            
        properties = [p.identifier for p in mod_src.bl_rna.properties
                    if not p.is_readonly]

        for prop in properties:
            setattr(mod_target, prop, getattr(mod_src, prop))
            
        for param in mod_src.node_group.inputs:
            input_name = param.identifier
            if input_name == "Input_0" or input_name == "Input_1":
                continue
            mod_target[input_name] = mod_src[input_name]
        mod_target.name = self.source_element_name
            
        print("creating overrite of {} from element {} for object {}".format(self.modifier_name, self.source_element_name, self.target_object_name))
        #self.report({"INFO"}, "Scene export complete")
        return {'FINISHED'}

_classes = (
    RISING_OT_CreateOverride,
)
    
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)