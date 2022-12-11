import bpy
import json
import os
import subprocess
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty, FloatProperty, PointerProperty

from bpy_extras.object_utils import AddObjectHelper
from bpy.types import PropertyGroup

from mathutils import Vector
import math
from numpy import array

from . import utils


directory_subtype = 'DIR_PATH' if bpy.app.version != (3,1,0) else 'NONE' # https://developer.blender.org/T96691

class CommonProps(PropertyGroup):
    engine_path : StringProperty(name="engine path",description="root file with tools and hopper folders", subtype=directory_subtype)
    output_path : StringProperty(name="output folder",description="Folder export maps to", subtype=directory_subtype)

class RISING_PT_SceneExportPanel(bpy.types.Panel):

    bl_label = "Scene Test Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        row = layout.row()

        row = layout.row()
        row.prop(scene.re, "engine_path")
        row = layout.row()
        row.prop(scene.re, "output_path")
        row = layout.row()
        row.operator("scene.export_scene")

class DependencyOverride:
    def __init__(self, name, src_dependency):
        self.name = name
        self.src_dependency = src_dependency
        self.collision_overrites_names = []
        self.collision_overrites = []
        self.beams_overrites_names = []
        self.beams_overrites = []
        
    def __hash__(self):
        
        collisions_sum = 0
        for col_overrite in self.collision_overrites:
            collisions_sum += col_overrite[0]
            collisions_sum += col_overrite[1]
            collisions_sum += col_overrite[2]
            collisions_sum += col_overrite[3]
        
        return int(hash((collisions_sum, )) / 1000000000)
        
    def add_collision_overrite(self, object_name, data):
        self.collision_overrites_names.append(object_name)
        self.collision_overrites.append(data)
        
    def add_beams_overrite(self, object_name, data):
        self.beams_overrites_names.append(object_name)
        self.beams_overrites.append(data)
        
    def get_name(self):
        return self.name
    
    def get_src_dependency(self):
        return self.src_dependency
            
class ExportScene(bpy.types.Operator, AddObjectHelper):
    bl_label = "Export scene"
    bl_idname = "scene.export_scene"
    
    out_json = []
    #bpy.context.scene.rising_path.engine_path

    
    dependency_objects = dict()
        
    def dump(self, json_data, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)      
        json_data.clear()
    
    def parse_polygons(self, root):
        
        collection = utils.find_collection(root, "Polygons")
        if collection is None:
            return []
        
        json_polygons = []
                
        for object in collection.objects:
            scale = object.scale[0]
            #materials = object.material_slots
            #if len(materials) == 0:
            #    continue
            #material_name = materials[0].name + ".jpg"
                     
            
            mesh = object.data
            vertices = mesh.vertices
            world_mat = object.matrix_world
            v0 = world_mat @ vertices[0].co
            v1 = world_mat @ vertices[1].co
            v2 = world_mat @ vertices[3].co
            v3 = world_mat @ vertices[2].co
            
            
            color_data = [0.55, 0.55, 0.6]
            for modifier in object.modifiers:
                if modifier.type != "NODES":
                    continue
                nodes = modifier.node_group
                if nodes.name != "Color":
                    continue
                for input in nodes.inputs:
                    if input.name == "Color":
                        input_id = input.identifier
                        color_raw = modifier[input_id]
                        color_data = [color_raw[0], color_raw[1], color_raw[2]]
            
            json_polygons.append({
                "v0": [v0[0], v0[2]],
                "v1": [v1[0], v1[2]],
                "v2": [v2[0], v2[2]],
                "v3": [v3[0], v3[2]],
                "color": color_data 
            })
                    
        return json_polygons
        
    def parse_object_refs(self, root, parent_location, parent_scale):
        collection = utils.find_collection(root, "Objects")
        if collection is None:
            return [], dict(), dict(), dict(), dict(), dict()
        
        objects = collection.objects
        dependencies = dict()
        dependencies_locations = dict()
        dependencies_rotations = dict()
        dependencies_scales = dict()
        
        overrides = dict()
        
        json_object_refs = []
        
        for object in objects:
            b_instancer = object.is_instancer
            if not b_instancer:
                continue
            linked_collection = object.instance_collection
            library = linked_collection.library
            if library is None:
                continue
            
            
            dependency_key = utils.trim_name(linked_collection.name_full)
            dependency_key_with_override = dependency_key
            #self.dependency_objects[dependency_key] = library.filepath
            
            overrides_object = utils.find_object(object, "overrides")
            if overrides_object is not None:
                dep_override = DependencyOverride(object.name, dependency_key)
                for modifier in overrides_object.modifiers:
                    if modifier.type != "NODES":
                        continue
                    
                    if modifier.node_group.name == "CollisionCircle" or modifier.node_group.name == "CollisionPolygon":
                        override_data = (
                            modifier["Input_2"],
                            modifier["Input_3"],
                            modifier["Input_4"],
                            modifier["Input_5"],
                            )
                        dep_override.add_collision_overrite(modifier.name, override_data)
                    elif modifier.node_group.name == "Beam":
                        override_data = (
                            modifier["Input_2"],
                            modifier["Input_3"],
                            modifier["Input_4"],
                        )
                        dep_override.add_beams_overrite(modifier.name, override_data)
                        
                dependency_key_with_override = dependency_key + str(hash(dep_override))
                overrides[dependency_key_with_override] = dep_override

            dependencies[dependency_key] = library.filepath
            
            location = (object.location * parent_scale + parent_location)
            object.rotation_mode = 'AXIS_ANGLE'
            rotation = object.rotation_axis_angle   
            object.rotation_mode = 'XYZ'
            scale = object.scale * parent_scale
            
            dependencies_locations[dependency_key] = location
            dependencies_rotations[dependency_key] = rotation
            dependencies_scales[dependency_key] = scale
                        
            json_object_refs.append({
                "name": object.name,
                "dependency" : dependency_key_with_override,
                "location": [
                    location[0],
                    location[1],
                    location[2]
                    ],
                "rotation": [
                    rotation[1],
                    rotation[2],
                    rotation[3],
                    rotation[0]
                    ],
                "scale": [
                    scale[0],
                    scale[1],
                    scale[2]
                    ]
            })
                
        return json_object_refs, dependencies, overrides, dependencies_locations, dependencies_rotations, dependencies_scales
            
    def parse_joint_weld(self, json_joints_welds, object, modifier):
        target1 = modifier["Input_2"]
        target2 = modifier["Input_3"]
        print(target1, target2)
        if (target1 is None) or (target2 is None):
            return
        
        targetOffset = [0, 0]
        for constraint in object.constraints:
            if constraint.type != "CHILD_OF":
                continue
            #if not constraint.use_offset:
            #    continue
            target = constraint.target
            curr_location = object.location
            target.rotation_mode = 'XYZ'
            rotation = target.rotation_euler[1]   
            rx = curr_location[0] * math.cos(rotation) + curr_location[2] * math.sin(rotation)
            ry = curr_location[0] * -math.sin(rotation) + curr_location[2] * math.cos(rotation)
            targetOffset[0] = rx
            targetOffset[1] = ry
                        
        collideConnected = modifier["Input_8"]
        
        dampingRatio = modifier["Input_10"]
        friquencyHZ = modifier["Input_9"]
        
        json_joints_welds.append({
            "target1": target1.name,
            "target2": target2.name,
            "targetOffset": [
                targetOffset[0],
                targetOffset[1]
                ],
            "collideConnected": collideConnected,
            "dampingRatio": dampingRatio,
            "friquencyHZ": friquencyHZ
        })
                
    def parse_joint_distance(self, json_joints_distance, modifier):
        target1 = modifier["Input_2"]
        target2 = modifier["Input_3"]
        print(target1, target2)
        if (target1 is None) or (target2 is None):
            return
        
        target1OffsetX = modifier["Input_4"]
        target1OffsetY = modifier["Input_6"]
                                      
        target2OffsetX = modifier["Input_5"]
        target2OffsetY = modifier["Input_7"]
                                
        collideConnected = modifier["Input_8"]
        
        dampingRatio = modifier["Input_10"]
        friquencyHZ = modifier["Input_9"]
        
        json_joints_distance.append({
            "target1": target1.name,
            "target2": target2.name,
            "target1Offset": [
                target1OffsetX,
                target1OffsetY
                ],
            "target2Offset": [
                target2OffsetX,
                target2OffsetY
                ],
            "collideConnected": collideConnected,
            "dampingRatio": dampingRatio,
            "friquencyHZ": friquencyHZ
        })
                
    def parse_joint_wheel(self, json_joints_wheel, modifier):
        target1 = modifier["Input_2"]
        target2 = modifier["Input_3"]
        print(target1, target2)
        if (target1 is None) or (target2 is None):
            return
        
        target1OffsetX = modifier["Input_4"]
        target1OffsetY = modifier["Input_6"]
                                      
        target2OffsetX = modifier["Input_5"]
        target2OffsetY = modifier["Input_7"]
                                      
        localAxisX = modifier["Input_12"]
        localAxisY = modifier["Input_13"]
                                
        collideConnected = modifier["Input_8"]
        
        max_motor_torque = modifier["Input_14"]
        motor_speed = modifier["Input_15"]
        
        dampingRatio = modifier["Input_10"]
        friquencyHZ = modifier["Input_9"]
        
        json_joints_wheel.append({
            "target1": target1.name,
            "target2": target2.name,
            "target1Offset": [
                target1OffsetX,
                target1OffsetY
                ],
            "target2Offset": [
                target2OffsetX,
                target2OffsetY
                ],
            "localAxis": [
                localAxisX,
                localAxisY
                ],
            "collideConnected": collideConnected,
            "maxMotorTorque": max_motor_torque,
            "motorSpeed": motor_speed,
            "dampingRatio": dampingRatio,
            "friquencyHZ": friquencyHZ
        })
         
    def parse_joints(self, root):
        print("Links root", root)
        collection = utils.find_collection(root, "Links")
        if collection is None:
            return []
               
        print("Parsing joints in", collection.name)
        
        objects = collection.objects
        
        json_joints_welds = []
        json_joints_distance = []
        json_joints_wheel = []
        
        for object in objects:
            print(object.modifiers)
            for modifier in object.modifiers:
                print(modifier.type)
                if modifier.type != 'NODES':
                    continue
                nodes = modifier.node_group
                print(nodes.name)
                if nodes.name == 'JointWeld':
                    self.parse_joint_weld(json_joints_welds, object, modifier)
                elif nodes.name == 'JointDistance':
                    self.parse_joint_distance(json_joints_distance, modifier)
                elif nodes.name == 'JointWheel':
                    self.parse_joint_wheel(json_joints_wheel, modifier)
        
        json_joints = []
        
        json_joints.append({
            "type": "Joints-weld",
            "objects": json_joints_welds
        })
           
        json_joints.append({
            "type": "Joints-distance",
            "objects": json_joints_distance
        })
           
        json_joints.append({
            "type": "Joints-wheel",
            "objects": json_joints_wheel
        })
        
        return json_joints
    
    def parse_object_bounding_box(self, object, json_bounding_box_data):
        center = object.location
        dimensions = object.dimensions
        hDims = dimensions / 2
        
        json_bounding_box_data.append({
            "center": [
                center[0],
                center[2],
                center[1]
            ],
            "hdims": [
                hDims[0],
                hDims[2],
                hDims[1],
            ]
        })        
     
    def prepare_mesh_data(self, mesh, world):
        out_buffer = []
        processed_vertices_id = set()
        out_buffer.append(int(0))
        num_of_vertices = 0
        mesh.calc_loop_triangles()
        sorted_loops = mesh.loops.values()
        sorted_loops.sort(key=lambda loop: (loop.vertex_index))
        for loop in sorted_loops:
            loop_id = loop.index
            vid = loop.vertex_index
            if vid in processed_vertices_id:
                continue
            num_of_vertices += 1
            processed_vertices_id.add(vid)
            #print("Vertex id:", vid)
            vertex = mesh.vertices[vid]
            v_global = world @ vertex.co
            #print("Vertex:", vertex.co)
            out_buffer.append(v_global[0])
            out_buffer.append(v_global[2])
            out_buffer.append(v_global[1])
        out_buffer[0] = num_of_vertices
        
        num_of_indices_id = len(out_buffer)
        out_buffer.append(int(0))
        
        num_of_indices = 0
        for polygon in mesh.loop_triangles:
            for loop_id in reversed(polygon.loops):
                num_of_indices += 1
                vid = mesh.loops[loop_id].vertex_index
                out_buffer.append(vid)
                #print("Index id: ", vid)
        out_buffer[num_of_indices_id] = num_of_indices
        
        print("num of vertices", out_buffer[0])
        print("num of indices", out_buffer[num_of_indices_id])

        return out_buffer     
        
    def parse_mesh(self, root, context):
        collection = utils.find_collection(root, "Mesh")
        if collection is None:
            return [], []
    
        depsgraph = context.evaluated_depsgraph_get()
        
        json_mesh_data = []
        json_bounding_box_data = []
        for object_raw in collection.objects:
            object = object_raw.evaluated_get(depsgraph)
            mesh = object.data
            if mesh is None:
                continue
            mesh_data = self.prepare_mesh_data(mesh, object.matrix_world)               
            json_mesh_data.append(mesh_data)
            
            self.parse_object_bounding_box(object, json_bounding_box_data)
            
        return json_mesh_data, json_bounding_box_data
    
    def parse_collisions(self, root, override):
        
        collection = utils.find_collection(root, "Collision")
        if collection is None:
            return [], []
        
        json_collision_circles_data = []
        json_collision_polygon_data = []
                
        for c_object in collection.objects:
            print(c_object.modifiers)
            for modifier in c_object.modifiers:
                print(modifier.type)
                if modifier.type != 'NODES':
                    continue
                
                override_data = None
                if override is not None:
                    if override.collision_overrites_names.count(c_object.name) > 0:
                        override_id = override.collision_overrites_names.index(c_object.name)
                        override_data = override.collision_overrites[override_id]
                
                nodes = modifier.node_group
                print(nodes.name)
                if nodes.name == 'CollisionCircle':
                    density = modifier["Input_2"]
                    restitution = modifier["Input_3"]
                    friction = modifier["Input_4"]
                    is_sensor = modifier["Input_5"]
                    filter_data = is_sensor
                    filter_data |= (modifier["Input_6"]  << 1 )
                    filter_data |= (modifier["Input_7"]  << 2 )
                    filter_data |= (modifier["Input_8"]  << 3 )
                    filter_data |= (modifier["Input_9"]  << 4 )
                    filter_data |= (modifier["Input_10"] << 5 )
                    filter_data |= (modifier["Input_11"] << 6 )
                    filter_data |= (modifier["Input_12"] << 7 )
                    filter_data |= (modifier["Input_13"] << 8 )
                    filter_data |= (modifier["Input_14"] << 9 )
                    filter_data |= (modifier["Input_15"] << 10 )
                    filter_data |= (modifier["Input_16"] << 11 )
                    filter_data |= (modifier["Input_17"] << 12 )
                    filter_data |= (modifier["Input_18"] << 13 )
                    filter_data |= (modifier["Input_19"] << 14 )
                    filter_data |= (modifier["Input_20"] << 15 )
                    filter_data |= (modifier["Input_21"] << 16 )
                    filter_data |= (modifier["Input_22"] << 17 )
                    filter_data |= (modifier["Input_23"] << 18 )
                    filter_data |= (modifier["Input_24"] << 19 )
                    filter_data |= (modifier["Input_25"] << 20 )
                    filter_data |= (modifier["Input_26"] << 21 )
                    filter_data |= (modifier["Input_27"] << 22 )
                    filter_data |= (modifier["Input_28"] << 23 )
                    filter_data |= (modifier["Input_29"] << 24 )
                    filter_data |= (modifier["Input_30"] << 25 )
                    filter_data |= (modifier["Input_31"] << 26 )
                    filter_data |= (modifier["Input_32"] << 27 )
                    filter_data |= (modifier["Input_33"] << 28 )
                    filter_data |= (modifier["Input_34"] << 29 )
                    filter_data |= (modifier["Input_35"] << 30 )
                    
                    if override_data is not None:
                        density = override_data[0]
                        restitution = override_data[1]
                        friction = override_data[2]
                
                    location = c_object.location
                    
                    radius = c_object.dimensions[0] / 2
                    json_collision_circles_data.append({
                        "radius": radius,
                        "density": density,
                        "restitution": restitution,
                        "friction": friction,
                        "filterData": filter_data,
                        "location": [
                            location[0],
                            location[2]
                        ]
                    })
                elif nodes.name == 'CollisionPolygon':
                    density = modifier["Input_2"]
                    restitution = modifier["Input_3"]
                    friction = modifier["Input_4"]
                    is_sensor = modifier["Input_5"]
                    filter_data = is_sensor
                    filter_data |= (modifier["Input_6"]  << 1 )
                    filter_data |= (modifier["Input_7"]  << 2 )
                    filter_data |= (modifier["Input_8"]  << 3 )
                    filter_data |= (modifier["Input_9"]  << 4 )
                    filter_data |= (modifier["Input_10"] << 5 )
                    filter_data |= (modifier["Input_11"] << 6 )
                    filter_data |= (modifier["Input_12"] << 7 )
                    filter_data |= (modifier["Input_13"] << 8 )
                    filter_data |= (modifier["Input_14"] << 9 )
                    filter_data |= (modifier["Input_15"] << 10 )
                    filter_data |= (modifier["Input_16"] << 11 )
                    filter_data |= (modifier["Input_17"] << 12 )
                    filter_data |= (modifier["Input_18"] << 13 )
                    filter_data |= (modifier["Input_19"] << 14 )
                    filter_data |= (modifier["Input_20"] << 15 )
                    filter_data |= (modifier["Input_21"] << 16 )
                    filter_data |= (modifier["Input_22"] << 17 )
                    filter_data |= (modifier["Input_23"] << 18 )
                    filter_data |= (modifier["Input_24"] << 19 )
                    filter_data |= (modifier["Input_25"] << 20 )
                    filter_data |= (modifier["Input_26"] << 21 )
                    filter_data |= (modifier["Input_27"] << 22 )
                    filter_data |= (modifier["Input_28"] << 23 )
                    filter_data |= (modifier["Input_29"] << 24 )
                    filter_data |= (modifier["Input_30"] << 25 )
                    filter_data |= (modifier["Input_31"] << 26 )
                    filter_data |= (modifier["Input_32"] << 27 )
                    filter_data |= (modifier["Input_33"] << 28 )
                    filter_data |= (modifier["Input_34"] << 29 )
                    filter_data |= (modifier["Input_35"] << 30 )
                    
                    if override_data is not None:
                        density = override_data[0]
                        restitution = override_data[1]
                        friction = override_data[2]
                        
                    world_mat = c_object.matrix_world
                    
                    vertices = c_object.data.vertices
                    if len(vertices) != 4:
                        continue
                    
                    p0 = world_mat @ vertices[0].co
                    p1 = world_mat @ vertices[1].co
                    p2 = world_mat @ vertices[3].co
                    p3 = world_mat @ vertices[2].co
                    
                    json_collision_polygon_data.append({
                        "density": density,
                        "restitution": restitution,
                        "friction": friction,
                        "filterData": filter_data,
                        "points": [
                            p0[0], p0[2],
                            p1[0], p1[2],
                            p2[0], p2[2],
                            p3[0], p3[2]
                        ]
                    })                    
                
        return json_collision_circles_data, json_collision_polygon_data
    
    def parse_beams(self, root, override, parent_location, parent_rotation, parent_scale):
        collection = utils.find_collection(root, "Beams")
        if collection is None:
            return [], []
        
        json_beams_enabled_data = []
        json_beams_disabled_data = []
                
        for object in collection.objects:
            print(object.modifiers)
        
            override_data = None
            if override is not None:
                if override.beams_overrites_names.count(object.name) > 0:
                    override_id = override.beams_overrites_names.index(object.name)
                    override_data = override.beams_overrites[override_id]
            
            for modifier in object.modifiers:
                print(modifier.type)
                if modifier.type != 'NODES':
                    continue
                
                nodes = modifier.node_group
                print(nodes.name)
                if nodes.name == 'Beam':
                    max_length = modifier["Input_2"]
                    width = modifier["Input_3"]
                    enabled = modifier["Input_4"]
                    if override_data is not None:
                        max_length = override_data[0]
                        width = override_data[1]
                        enabled = override_data[2]
                        
                    x = object.location[0]
                    y = object.location[2]

                    rot_parent = parent_rotation[0] * parent_rotation[2]

                    rx = x * math.cos(rot_parent) + y * math.sin(rot_parent)
                    ry = x * -math.sin(rot_parent) + y * math.cos(rot_parent)
                    
                    location = object.location#Vector([rx, 0, ry]) + parent_location
                    
                    object.rotation_mode = 'XYZ'
                    rotation = object.rotation_euler[1] #+ rot_parent
                    
                    beam_data = {
                        "rotation": rotation,
                        "maxLength": max_length,
                        "width": width,
                        "location": [
                            location[0],
                            location[2]
                        ]
                    }
                    if enabled:
                        json_beams_enabled_data.append(beam_data)
                    else:
                        json_beams_disabled_data.append(beam_data)
                    
        return json_beams_enabled_data, json_beams_disabled_data  
    
    def parse_actions(self):
        json_actions_data = []
        
        for action in bpy.data.actions:
                
            action_name = action.name
            
            values_total = []
            types_total = []
            
            if len(action.fcurves) == 0:
                continue
            
            def get_num_of_frames(fcurves):
                c_range = fcurves[0].range()
                return c_range[1] - c_range[0] + 1
            num_of_frames = get_num_of_frames(action.fcurves)
            
            def compute_stride(num_of_frames):
                if num_of_frames > 64:
                    return 2
                return 1
            stride = compute_stride(num_of_frames)
            
            for curve in action.fcurves:                
                if len(curve.keyframe_points) == 0:
                    continue
                
                is_constant = True
                k_value = curve.keyframe_points[0].handle_left[1]
                for keyframe in curve.keyframe_points:
                    if abs(keyframe.handle_left[1] - k_value) > 0.001 or \
                        abs(keyframe.co[1] - k_value) > 0.001 or \
                        abs(keyframe.handle_right[1] - k_value) > 0.001:
                            is_constant = False
                if is_constant:
                    continue
                
                c_range = curve.range()
                num_of_frames = c_range[1] - c_range[0] + 1
                                
                values = []
                
                def populate( multiplier = 1):
                    curr_frame_id = c_range[0]
                    while curr_frame_id <= c_range[1]:
                        value = curve.evaluate(curr_frame_id)
                        values.append(value * multiplier)
                        curr_frame_id += stride
                    
                type = curve.data_path + str(curve.array_index)    
                bNegate = type == "rotation_axis_angle0" or type == "rotation_euler1"
                if bNegate:
                    populate(-1)
                else:
                    populate()
                    
                types_total.append(type)
                values_total.append(values)
                
            frame_delta_time = 1/60
            time_stride = frame_delta_time * stride
            
            if len(values_total) == 0:
                continue

            json_actions_data.append({
                "name": action_name,
                "timeStride": time_stride,
                "types": types_total,
                "data": values_total
            })         
        
        return json_actions_data 

    def parse_tracks(self, root):
        print("---------------Parsing tracks---------------------")
        collection = utils.find_collection(root, "Tracks")
        if collection is None:
            print("No tracks registered")
            return []
        
        json_tracks_data = []
        
        for object in collection.objects:
            if object.data is None:
                continue

            track_data = object.data
            splines = track_data.splines
            if len(splines) == 0:
                continue

            spline = splines[0]

            control_points_x = []
            control_points_y = []

            w_mat = object.matrix_world

            for point in spline.bezier_points:
                def get_x(p):
                    return p[0]
                def get_y(p):
                    return p[2]

                point_left = w_mat @ point.handle_left
                point_center = w_mat @ point.co
                point_right = w_mat @ point.handle_right

                control_points_x.append(get_x(point_left))
                control_points_x.append(get_x(point_center))
                control_points_x.append(get_x(point_right))

                control_points_y.append(get_y(point_left))
                control_points_y.append(get_y(point_center))
                control_points_y.append(get_y(point_right))

            if len(control_points_x) == 0:
                continue

            is_cyclic = spline.use_cyclic_u
            if not is_cyclic:
                control_points_x.pop(0)
                control_points_x.pop(-1)
                control_points_y.pop(0)
                control_points_y.pop(-1)
            else:
                control_points_x.append(control_points_x[0])
                control_points_x.append(control_points_x[1])
                control_points_x.pop(0)
                
                control_points_y.append(control_points_y[0])
                control_points_y.append(control_points_y[1])
                control_points_y.pop(0)

            animation_data = track_data.animation_data
            if animation_data is None:
                continue
            action = animation_data.action
            if action is None:
                continue
            action_name = action.name

            #action_data = self.parse_action(action)
            #if action_data is None:
            #    continue

            json_tracks_data.append({
                "name": object.name,
                "actionName": action_name,
                "pointsX": control_points_x,
                "pointsY": control_points_y
            })

        print("json_tracks_data", json_tracks_data)
        return json_tracks_data
    
    def parse_dependencies(self, dependecies, overrides, dependencies_locations, dependencies_rotations, dependencies_scales, context):
        registered_dependencies_names = []
        registered_dependencies_ids = []
        for id, dep in enumerate(bpy.data.collections):
            #if (dep.library is not None) and (dep.is_library_indirect is False):
            #if dep.is_instancer
            registered_dependencies_names.append(utils.trim_name(dep.name_full))
            registered_dependencies_ids.append(id)
            
        for name in dependecies:
            #if registered_dependencies_names.count(name) == 0:
            #    print("Cannot find dependency", name)
            #    print("Searching dependency override...")
            #    override = overrides.get(name)
            #    if override is None:
            #        print("Cannot find dependency override", name)
            #        continue
            #    src = override.get_src_dependency()
            #    if bpy.data.collections.count(src) == 0:
            #        print("Cannot find source collection", src)
            #        continue
            #    src_collection = bpy.data.collections[src]
            
            overrides_list = [None]
            for override in overrides.values():
                if override.get_src_dependency() == name:
                    overrides_list.append(override)
            local_id = registered_dependencies_names.index(name)
            collection_id = registered_dependencies_ids[local_id]
            
            root_src = bpy.data.collections[collection_id]
            print(overrides_list)            

            for override in overrides_list:
                json_cluster = self.parse_cluster(root_src, context, dependencies_locations[name], dependencies_rotations[name], dependencies_scales[name], override)
                
                root_folder = bpy.path.abspath(bpy.context.scene.re.engine_path)
                
                out_name = name
                if override is not None:
                    out_name = name + str(hash(override))
                
                dependency_src_path = root_folder + "hopper\\Hopper\\Hopper\\Resources\\Sources\\Data\\Intermediate\\" + out_name + ".json"
                self.dump(json_cluster, dependency_src_path)
                print("Intermediate generated for ", out_name)
                
                compiler_path = root_folder + "tools\\MapCompiler\\x64\\Debug\\MapCompiler.exe"
                export_folder = root_folder + "hopper\\Hopper\\Hopper\\Resources\\Clusters" 
                completed = subprocess.run([compiler_path, 
                    "-i", dependency_src_path, "-of", export_folder])
                print("Cluster compilation", out_name, completed)
      
    def parse_cluster(self, root, context, parent_location, parent_rotation, parent_scale, override):
        cluster_name = root.name
        if override is not None:
            cluster_name = cluster_name + str(hash(override))
            
        print("Trying to parse cluster", cluster_name)
        
        cluster_collection = utils.get_cluster_collection(root)
        if cluster_collection is None:
            return []
        
        cluster_type = utils.gather_name(cluster_collection.name)
        print(cluster_type)
                
        #parse objects
        json_object_refs, dependecies, overrides, dependencies_locations, dependencies_rotations, dependencies_scales = \
            self.parse_object_refs(cluster_collection, parent_location, parent_scale)
        
        #parse collisions
        json_collision_circles, json_collision_polygons = self.parse_collisions(cluster_collection, override)
        
        json_beams_enabled, json_beams_disabled = self.parse_beams(cluster_collection, override, parent_location, parent_rotation, parent_scale)
        
        json_tracks = self.parse_tracks(cluster_collection)

        #parse joints
        json_joints = self.parse_joints(cluster_collection)
                
        #parse meshes
        json_meshes, json_boundings = self.parse_mesh(cluster_collection, context)
        
        json_polygons = self.parse_polygons(cluster_collection)
        print(json_polygons)
        print(json_tracks)
        json_cluster = {
            "name": cluster_name,
            "type": cluster_type,
            "objectRefs": json_object_refs,
            "collision-circles": json_collision_circles,
            "collision-polygons": json_collision_polygons,
            "beams-enabled": json_beams_enabled,
            "beams-disabled": json_beams_disabled,
            "joints": json_joints,
            "meshes-v1": json_meshes,
            "boundings": json_boundings,
            "polygons": json_polygons,
            "tracks": json_tracks,
            "actions": {},
        }
        
        #parse dependences 
        self.parse_dependencies(dependecies, overrides, dependencies_locations, dependencies_rotations, dependencies_scales, context)
        
        return json_cluster
    
    @classmethod
    def poll(cls, context):
        selected = context.selected_objects
        return len(selected) > 0

    def execute(self, context):
        
        #root_folder = bpy.context.scene.re.engine_path
        #print("root folder", root_folder)
        filename = bpy.path.basename(bpy.data.filepath).split('.')[0]
        #print("filename", filename)
        #save_path = root_folder + "\\..\\..\\hopper\\Hopper\\Hopper\\Resources\\MapsSrc\\Intermediate\\" + filename + ".json"
        #export_folder = root_folder + "\\..\\..\\hopper\\Hopper\\Hopper\\Resources\\" + "Maps" + "\\ch0" 
        #export_folder_obj = root_folder + "\\..\\..\\hopper\\Hopper\\Hopper\\Resources\\" + "Objects" + "\\testObjs" 
        #
        #print(save_path)
        #print(export_folder)
        #print(export_folder_obj)
        
        print("Export scene")

        selected = context.selected_objects[0]
        cluster_root = utils.get_cluster_from_collection(selected.users_collection[0])
        if cluster_root is None:
            self.report({"INFO"}, "Failed to export, select an object to deduce a cluster")
            return {'FINISHED'}
        cluster = utils.get_parent_collection(cluster_root)
        print("ccc", cluster.name)

        root_folder = bpy.path.abspath(bpy.context.scene.re.engine_path)
        save_path = root_folder + "hopper\\Hopper\\Hopper\\Resources\\Sources\\Intermediate\\" + cluster.name + " [" + filename + "].json"

        #for cluster in bpy.context.scene.collection.children:
        json_scene = self.parse_cluster(cluster, context, Vector([0, 0, 0]), Vector([0, 1, 0, 0]), Vector([1, 1, 1]), None)
        json_scene["actions"] = self.parse_actions()
        print(json_scene)
        self.dump(json_scene, save_path)
            
        #self.parse_polygons()
        #self.parse_objects()
        #self.parse_joints(bpy.context.layer_collection.collection, self.out_json)
        #self.parse_dependencies()
        
        
        compiler_path = root_folder + "tools\\MapCompiler\\x64\\Debug\\MapCompiler.exe"
        #export_folder = bpy.path.abspath(bpy.context.scene.re.output_path) 
        export_folder = root_folder + "hopper\\Hopper\\Hopper\\Resources\\Clusters" 
        completed = subprocess.run([compiler_path, 
                        "-i", save_path, "-of", export_folder])
        print(completed)
        print("Export done!")
        return {'FINISHED'}

_classes = (
    RISING_PT_SceneExportPanel,
    ExportScene,
    CommonProps
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
        
    def make_pointer(prop_type):
        return PointerProperty(name="settings",type=prop_type)

    bpy.types.Scene.re = make_pointer(CommonProps)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.re
