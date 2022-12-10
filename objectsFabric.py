import bpy

import bmesh
from bpy.types import Menu
from bpy_extras.object_utils import AddObjectHelper

from . import utils

from bpy.props import (
    FloatProperty,
)

def add_polygon():
    
    verts = [
        (-2.0, 0, -2.0),
        (-2.0, 0, 2.0),
        (2.0, 0, 2.0),
        (2.0, 0, -2.0)
    ]

    faces = [
        (0, 1, 2, 3)
    ]

    return verts, faces

class RISING_OT_CreatePolygon(bpy.types.Operator, AddObjectHelper):
    """Add a simple box mesh"""
    bl_idname = "mesh.polygon_crete"
    bl_label = "Create polygon"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):

        verts_loc, faces = add_polygon()

        mesh = bpy.data.meshes.new("Polygon")

        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        bpy.context.scene.cursor.location.y = 0

        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)

        from bpy_extras import object_utils
        new_polygon = object_utils.object_data_add(context, mesh, operator=self)
                
        polys_collection = utils.find_collection(root, "Polygons")
        print("polys_collection", polys_collection)
        if polys_collection is None:
            polys_collection = bpy.data.collections.new("Polygons")
            root.children.link(polys_collection)
        
        for coll in new_polygon.users_collection:
            coll.objects.unlink(new_polygon)
        polys_collection.objects.link(new_polygon)
        
        nodegroup_name = "Metrics"
        utils.link_utils_nodegroup(nodegroup_name)
        
        modifier = new_polygon.modifiers.new(nodegroup_name, "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup_name]

        return {'FINISHED'}
    
class RISING_OT_CreateMesh(bpy.types.Operator, AddObjectHelper):
    bl_idname = "mesh.mesh_create"
    bl_label = "Create mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):

        mesh = bpy.data.meshes.new("Mesh")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm) 

        bm.verts.new((0, 0, 0))
        bm.to_mesh(mesh)
        mesh.update()

        bpy.context.scene.cursor.location.y = 0

        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)

        from bpy_extras import object_utils
        new_polygon = object_utils.object_data_add(context, mesh, operator=self)
                        
        mesh_collection = utils.find_collection(root, "Mesh")
        print("mesh_collection", mesh_collection)
        if mesh_collection is None:
            mesh_collection = bpy.data.collections.new("Mesh")
            root.children.link(mesh_collection)
        
        for coll in new_polygon.users_collection:
            coll.objects.unlink(new_polygon)
        mesh_collection.objects.link(new_polygon)

        return {'FINISHED'}


class RISING_OT_CreateObjectDynamic(bpy.types.Operator, AddObjectHelper):
    bl_idname = "object.new_dynamic"
    bl_label = "Create dynamic object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):

        cluster_collection_root = bpy.data.collections.new("NEW OBJECT")
        context.scene.collection.children.link(cluster_collection_root)
        
        cluster_collection_type = bpy.data.collections.new("Dynamic")
        cluster_collection_root.children.link(cluster_collection_type)
        
        cluster_collection_objects = bpy.data.collections.new("Objects")
        cluster_collection_type.children.link(cluster_collection_objects)

        return {'FINISHED'}
    
class RISING_OT_CreateObjectStatic(bpy.types.Operator, AddObjectHelper):
    bl_idname = "object.new_static"
    bl_label = "Create static object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):

        cluster_collection_root = bpy.data.collections.new("NEW OBJECT")
        context.scene.collection.children.link(cluster_collection_root)
        
        cluster_collection_type = bpy.data.collections.new("Static")
        cluster_collection_root.children.link(cluster_collection_type)
        
        cluster_collection_objects = bpy.data.collections.new("Objects")
        cluster_collection_type.children.link(cluster_collection_objects)

        return {'FINISHED'}
    
class RISING_OT_CreateObjectKinematic(bpy.types.Operator, AddObjectHelper):
    bl_idname = "object.new_kinematic"
    bl_label = "Create kinematic object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):

        cluster_collection_root = bpy.data.collections.new("NEW OBJECT")
        context.scene.collection.children.link(cluster_collection_root)
        
        cluster_collection_type = bpy.data.collections.new("Kinematic")
        cluster_collection_root.children.link(cluster_collection_type)
        
        cluster_collection_objects = bpy.data.collections.new("Objects")
        cluster_collection_type.children.link(cluster_collection_objects)

        return {'FINISHED'}

_classes = (
    RISING_OT_CreatePolygon,
    RISING_OT_CreateMesh,
    RISING_OT_CreateObjectDynamic,
    RISING_OT_CreateObjectStatic,
    RISING_OT_CreateObjectKinematic,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

