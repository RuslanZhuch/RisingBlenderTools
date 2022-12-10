import bpy

import bmesh
from bpy.types import Menu

from . import common_systems
from . import overrites

class RISING_MT_overrites_menu(bpy.types.Menu):
    bl_label = "Overrides menu"
    bl_idname = "menu.overrides"
    
    def draw(self, context):
        layout = self.layout
        
        print("Modifiers to override")
        obj_names, mod_names = overrites.get_possible_overrite_list(context.object)
        for obj_name, mod_name in zip(obj_names, mod_names):
            print(obj_name, mod_name)
            op = layout.operator("overrites.create_override", text="{} from {}".format(mod_name, obj_name))
            op.target_object_name = context.object.name
            op.source_element_name = obj_name
            op.modifier_name = mod_name
                
class RISING_MT_JointsMenu(Menu):
    bl_label = "Create joint"
    bl_idname = "menu.joints"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("joints.wheel",  icon="MESH_PLANE")
        pie.operator("joints.distance",  icon="MESH_PLANE")
        pie.operator("joints.weld",  icon="MESH_PLANE")

class RISING_MT_CreateNewObjectMenu(Menu):
    bl_label = "Create new object"
    bl_idname = "menu.new_object"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("object.new_dynamic",  icon="MESH_PLANE")
        pie.operator("object.new_static",  icon="MESH_PLANE")
        pie.operator("object.new_kinematic",  icon="MESH_PLANE")

class RISING_MT_ObjectsFabricMenu(Menu):
    bl_label = "Create primive"
    bl_idname = "menu.rfabric"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("mesh.polygon_crete",  icon="MESH_PLANE")
        pie.operator("mesh.mesh_create",  icon="MESH_PLANE")
        
class RISING_MT_EditMenu(Menu):
    bl_label = "Edit"
    bl_idname = "menu.redit"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("collision.on_top_en",  icon="MESH_PLANE")
        pie.operator("collision.on_top_dis",  icon="MESH_PLANE")
        pie.operator("wm.call_menu", text="Overrides", icon="MESH_PLANE").name = "menu.overrides"
        
class RISING_MT_CollisionsFabricMenu(Menu):
    bl_label = "Create object"
    bl_idname = "menu.rcollisions"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("collision.circle",  icon="MESH_PLANE")
        pie.operator("collision.polygon",  icon="MESH_PLANE")

class RISING_MT_UtilityMenu(Menu):
    bl_label = "Rising control panel"
    bl_idname = "menu.rutility"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        op = pie.operator("wm.call_menu_pie", text="Create primitive", icon="MESH_PLANE")
        op.name = RISING_MT_ObjectsFabricMenu.bl_idname
        
        op = pie.operator("wm.call_menu_pie", text="Create joint",  icon="MESH_PLANE")
        op.name = RISING_MT_JointsMenu.bl_idname
        
        op = pie.operator("wm.call_menu_pie", text="Create collision",  icon="MESH_PLANE")
        op.name = RISING_MT_CollisionsFabricMenu.bl_idname
        
        op = pie.operator("wm.call_menu_pie", text="Edit",  icon="MESH_PLANE")
        op.name = RISING_MT_EditMenu.bl_idname
        
        op = pie.operator("wm.call_menu_pie", text="Create New object",  icon="MESH_PLANE")
        op.name = RISING_MT_CreateNewObjectMenu.bl_idname
        
        pie.operator("scene.initiate",  icon="MESH_PLANE")
        pie.operator("scene.export_scene",  icon="MESH_PLANE")
        
        #pie.operator("menu.joints",  icon="MESH_PLANE")

_classes = (
    RISING_MT_overrites_menu,
    RISING_MT_JointsMenu,
    RISING_MT_ObjectsFabricMenu,
    RISING_MT_CollisionsFabricMenu,
    RISING_MT_EditMenu,
    RISING_MT_CreateNewObjectMenu,
    RISING_MT_UtilityMenu,
)

keymaps = []

def register_keymap():
    global keymaps
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi_mnu_joints = km.keymap_items.new("wm.call_menu_pie", "J", "PRESS")
    kmi_mnu_joints.properties.name = RISING_MT_UtilityMenu.bl_idname

#    kmi_mnu_fab = km.keymap_items.new("wm.call_menu_pie", "P", "PRESS")
#    kmi_mnu_fab.properties.name = RISING_MT_ObjectsFabricMenu.bl_idname

    kmi_reload = km.keymap_items.new(common_systems.ReloadScene.bl_idname, "R", "PRESS", shift=True)
    #kmi_export = km.keymap_items.new(common_systems.ExportScene.bl_idname, "E", "PRESS", shift=True)
    
#    keymaps.append((
#        km, 
#        kmi_export,
#    ))
    keymaps.append((
        km, 
        kmi_reload, 
    ))

    keymaps.append((
        km, 
        kmi_mnu_joints, 
    ))
    
def unregister_keymap():
    global keymaps
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)   
        
    keymaps.clear()

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
    register_keymap()

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
        
    unregister_keymap()