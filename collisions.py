import bpy

import bmesh
from bpy.types import Menu
from bpy_extras.object_utils import AddObjectHelper

from . import utils

class RISING_PT_CreateCollisionCircle(bpy.types.Operator, AddObjectHelper):
    bl_idname = "collision.circle"
    bl_label = "Create collision circle"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):
        mesh = bpy.data.meshes.new("CircleCollision")

        bm = bmesh.new()
        geom = bmesh.ops.create_circle(bm, segments=16, radius=1) 

        bm.verts.new((0, 0, 0))
        bm.to_mesh(mesh)
        mesh.update()
        
        bpy.context.scene.cursor.location.y = 0

        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)

        from bpy_extras import object_utils
        new_collision = object_utils.object_data_add(context, mesh, operator=self)
        new_collision.show_in_front = True
        
        new_collision.rotation_mode = 'XYZ'
        new_collision.rotation_euler[0] = 3.14 / 2
        
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False, properties=False)
        
        nodegroup = "CollisionCircle"
        utils.link_utils_nodegroup(nodegroup)
        
        modifier = new_collision.modifiers.new("Collision", "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup]
        
        collision_collection = utils.find_collection(root, "Collision")
        print("collision_collection", collision_collection)
        if collision_collection is None:
            collision_collection = bpy.data.collections.new("Collision")
            root.children.link(collision_collection)
        
        for coll in new_collision.users_collection:
            coll.objects.unlink(new_collision)
        collision_collection.objects.link(new_collision)
        
        return {'FINISHED'}
    

class RISING_PT_CreateCollisionPolygon(bpy.types.Operator, AddObjectHelper):
    bl_idname = "collision.polygon"
    bl_label = "Create collision polygon"

    @classmethod
    def poll(cls, context):
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):
        mesh = bpy.data.meshes.new("CirclePolygon")

        bm = bmesh.new()
        
        verts = [
            (-2.0, 0, -2.0),
            (-2.0, 0, 2.0),
            (2.0, 0, 2.0),
            (2.0, 0, -2.0)
        ]

        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
        ]

        for v_co in verts:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in edges:
            bm.edges.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()
        
        bpy.context.scene.cursor.location.y = 0

        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)

        from bpy_extras import object_utils
        new_collision = object_utils.object_data_add(context, mesh, operator=self)
        new_collision.show_in_front = True
        
        nodegroup = "CollisionPolygon"
        utils.link_utils_nodegroup(nodegroup)
        
        modifier = new_collision.modifiers.new("Collision", "NODES")
        modifier.node_group = bpy.data.node_groups[nodegroup]
        
        collision_collection = utils.find_collection(root, "Collision")
        print("collision_collection", collision_collection)
        if collision_collection is None:
            collision_collection = bpy.data.collections.new("Collision")
            root.children.link(collision_collection)
        
        for coll in new_collision.users_collection:
            coll.objects.unlink(new_collision)
        collision_collection.objects.link(new_collision)
        
        
        return {'FINISHED'}
    

class RISING_PT_DisCollisionsOverlay(bpy.types.Operator, AddObjectHelper):
    bl_idname = "collision.on_top_dis"
    bl_label = "Disable collisions overlay"

    @classmethod
    def poll(cls, context):
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):
        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)
            
        if root is None:
            return {'FINISHED'}
        
        links_collection = utils.find_collection(root, "Collision")
        if links_collection is None:
            return {'FINISHED'}
        
        for collision in links_collection.objects:
            collision.show_in_front = False
            
        return {'FINISHED'}
    
class RISING_PT_EnCollisionsOverlay(bpy.types.Operator, AddObjectHelper):
    bl_idname = "collision.on_top_en"
    bl_label = "Enable collisions overlay"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        def check_object(context):
            return utils.get_cluster_from_active_object(context) is not None
        
        def check_collection(context):
            return utils.get_cluster_from_active_collection(context) is not None
        
        return check_object(context) or check_collection(context)
    
    def execute(self, context):
        root = utils.get_cluster_from_active_object(context)
        if root is None:
            root = utils.get_cluster_from_active_collection(context)
            
        if root is None:
            return {'FINISHED'}
        
        links_collection = utils.find_collection(root, "Collision")
        if links_collection is None:
            return {'FINISHED'}
        
        for collision in links_collection.objects:
            collision.show_in_front = True
            
        return {'FINISHED'}

_classes = (
    RISING_PT_CreateCollisionCircle,
    RISING_PT_CreateCollisionPolygon,
    RISING_PT_DisCollisionsOverlay,
    RISING_PT_EnCollisionsOverlay,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)