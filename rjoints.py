import bpy

import bmesh
import mathutils
from bpy.types import Menu
from bpy_extras.object_utils import AddObjectHelper

from . import utils

def check_can_create_joint(context):
    selected = context.selected_objects
    if len(selected) != 2:
        return False
    obj_1 = selected[0]
    obj_2 = selected[1]
    collection1 = obj_1.users_collection[0]
    collection2 = obj_2.users_collection[0]
    if collection1 is None or collection2 is None:
        return False
    
    if collection1 != collection2:
        return False
    
    if utils.gather_name(collection1.name) != "Objects":
        return False
    
    return True

class RISING_PT_CreateJointWheel(bpy.types.Operator, AddObjectHelper):
    bl_idname = "joints.wheel"
    bl_label = "Create wheel joint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return check_can_create_joint(context)
    
    def execute(self, context):

        mesh = bpy.data.meshes.new("WheelJoint")

        bm = bmesh.new()

        bm.verts.new((0, 0, 0))
        bm.to_mesh(mesh)
        mesh.update()
        
        curr_collection = context.selected_objects[0].users_collection[0]
        root = utils.get_parent_cluster_root(curr_collection)
        print("Found root collection", root, curr_collection)
        if root is None:
            return {'FINISHED'}
        
        links_collection = utils.find_collection(root, "Links")
        print("links_collection", links_collection)
        if links_collection is None:
            links_collection = bpy.data.collections.new("Links")
            root.children.link(links_collection)

#        layer_collection = utils.get_layer_collection(bpy.context.layer_collection, links_collection.name)
#        bpy.context.view_layer.active_layer_collection = layer_collection



        obj_1 = context.active_object
        obj_2 = context.selected_objects[0]
        if obj_2 is obj_1:
            obj_2 = context.selected_objects[1]
        
        from bpy_extras import object_utils
        joint = object_utils.object_data_add(context, mesh, operator=self)
        joint.show_in_front = True

        for coll in joint.users_collection:
            coll.objects.unlink(joint)
        links_collection.objects.link(joint)

        const_joint = joint.constraints.new(type='COPY_LOCATION')
        const_joint.target = obj_1
                
        nodegroup_name = "JointWheel"
        utils.link_utils_nodegroup(nodegroup_name)
        
        modifier = joint.modifiers.new(nodegroup_name, "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
        modifier["Input_2"] = obj_1
        modifier["Input_3"] = obj_2
        
        return {'FINISHED'}


class RISING_PT_CreateJointDistance(bpy.types.Operator, AddObjectHelper):
    bl_idname = "joints.distance"
    bl_label = "Create distance joint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return check_can_create_joint(context)
    
    def execute(self, context):

        mesh = bpy.data.meshes.new("DistanceJoint")

        bm = bmesh.new()

        bm.verts.new((0, 0, 0))
        bm.to_mesh(mesh)
        mesh.update()
        
        curr_collection = context.selected_objects[0].users_collection[0]
        root = utils.get_parent_cluster_root(curr_collection)
        if root is None:
            return {'FINISHED'}
        
        links_collection = utils.find_collection(root, "Links")
        if links_collection is None:
            links_collection = bpy.data.collections.new("Links")
            root.children.link(links_collection)

#        layer_collection = utils.get_layer_collection(bpy.context.layer_collection, links_collection.name)
#        bpy.context.view_layer.active_layer_collection = layer_collection

        obj_1 = context.active_object
        obj_2 = context.selected_objects[0]
        if obj_2 is obj_1:
            obj_2 = context.selected_objects[1]
        
        from bpy_extras import object_utils
        joint = object_utils.object_data_add(context, mesh, operator=self)
        joint.show_in_front = True
        
        for coll in joint.users_collection:
            coll.objects.unlink(joint)
        links_collection.objects.link(joint)
        
        const_joint = joint.constraints.new(type='COPY_LOCATION')
        const_joint.target = obj_1
                
        nodegroup_name = "JointDistance"
        utils.link_utils_nodegroup(nodegroup_name)
        
        modifier = joint.modifiers.new(nodegroup_name, "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
        modifier["Input_2"] = obj_1
        modifier["Input_3"] = obj_2
        
        return {'FINISHED'}

class RISING_PT_CreateJointWeld(bpy.types.Operator, AddObjectHelper):
    bl_idname = "joints.weld"
    bl_label = "Create weld joint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return check_can_create_joint(context)
    
    def execute(self, context):

        vertices = [
            (0, 0, 0),
            (-2, 0, 0),
            (0, 0, 2),
            (2, 0, 0),
            (0, 0, -2),
        ]
       
        edges = [
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4),
        ]

        mesh = bpy.data.meshes.new("DistanceJoint")

        bm = bmesh.new()
        
        for v_co in vertices:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in edges:
            bm.edges.new([bm.verts[i] for i in f_idx])
            
        bm.to_mesh(mesh)
        mesh.update()
        
        curr_collection = context.selected_objects[0].users_collection[0]
        root = utils.get_parent_cluster_root(curr_collection)
        if root is None:
            return {'FINISHED'}
        
        links_collection = utils.find_collection(root, "Links")
        if links_collection is None:
            links_collection = bpy.data.collections.new("Links")
            root.children.link(links_collection)

#        layer_collection = utils.get_layer_collection(bpy.context.layer_collection, links_collection.name)
#        bpy.context.view_layer.active_layer_collection = layer_collection

        obj_1 = context.active_object
        obj_2 = context.selected_objects[0]
        if obj_2 is obj_1:
            obj_2 = context.selected_objects[1]
        
        from bpy_extras import object_utils
        joint = object_utils.object_data_add(context, mesh, operator=self)
        joint.show_in_front = True
        
        for coll in joint.users_collection:
            coll.objects.unlink(joint)
        links_collection.objects.link(joint)
        
        const_joint = joint.constraints.new(type='CHILD_OF')
        const_joint.target = obj_1
        const_joint.use_scale_x = False
        const_joint.use_scale_y = False
        const_joint.use_scale_z = False
        const_joint.inverse_matrix = mathutils.Matrix()
                
        const_loc_obj_2 = obj_2.constraints.new(type='COPY_LOCATION')
        const_loc_obj_2.target = joint
        const_rot_obj_2 = obj_2.constraints.new(type='COPY_ROTATION')
        const_rot_obj_2.target = joint
        const_rot_obj_2.mix_mode = "ADD"
        
            
        nodegroup_name = "JointWeld"
        utils.link_utils_nodegroup(nodegroup_name)
        
        modifier = joint.modifiers.new(nodegroup_name, "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
        modifier["Input_2"] = obj_1
        modifier["Input_3"] = obj_2
        
        return {'FINISHED'}

_classes = (
    RISING_PT_CreateJointWheel,
    RISING_PT_CreateJointDistance,
    RISING_PT_CreateJointWeld,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)