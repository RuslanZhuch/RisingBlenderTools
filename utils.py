import bpy

def gather_name(str):
    parts = str.split('.')
    if len(parts) <= 0:
        return str
    return parts[0]

def find_collection(root, search_name):
    for collection in root.children:
        name = collection.name
        if gather_name(name) == search_name:
            return collection
    
    return None

def find_object(root, search_name):
    for object in root.children:
        name = object.name
        if gather_name(name) == search_name:
            return object
    
    return None

def get_is_cluster_collection(raw_name):
    name = gather_name(raw_name)
    return name == "Dynamic" or name == "Static" or name == "Kinematic"

def get_cluster_collection(root):
    collection = root.children[0]
    if get_is_cluster_collection(collection.name):
        return collection
    return None

def get_cluster_collection_rec(root):
    for collection in root.children:
        if get_is_cluster_collection(collection.name):
            return collection
        return get_cluster_collection_rec(collection)
    return None

def get_parent_cluster_root(curr_collection):
    if get_is_cluster_collection(curr_collection.name):
        return curr_collection
    
    for parent_collection in bpy.data.collections:
        print("parent name", parent_collection.name)
        id = parent_collection.children.find(curr_collection.name)
        if id < 0:
            continue
        
        print("Found parent", parent_collection.name)
        return get_parent_cluster_root(parent_collection) 
    
    return None

def get_parent_collection(curr_collection):
    for parent_collection in bpy.data.collections:
        id = parent_collection.children.find(curr_collection.name)
        if id < 0:
            continue
        
        return parent_collection
        
def get_selected_cluster_root(context):
    curr_object = context.object
    if curr_object is None:
        return None
    
    return get_parent_cluster_root(curr_object.users_collection[0])
    
def get_parent_collection_is(curr_collection, parent_name):
    for parent_collection in bpy.data.collections:
        id = parent_collection.children.find(curr_collection.name)
        if id < 0:
            continue
        return gather_name(parent_collection.name) == parent_name
    
    return False

def get_layer_collection(curr_layer_collection, collection_name_to_find):
    found = None
    if (curr_layer_collection.name == collection_name_to_find):
        return curr_layer_collection
    
    for layer in curr_layer_collection.children:
        found = get_layer_collection(layer, collection_name_to_find)
        if found:
            return found
        
    return None



def get_cluster_from_collection(collection):
    if collection is None:
        return None
    if get_is_cluster_collection(collection.name):
        return collection
    for child in collection.children:
        if get_is_cluster_collection(child.name):
            return child
    return get_parent_cluster_root(collection)
        
def get_cluster_from_active_collection(context):
    return get_cluster_from_collection(context.collection)

def get_cluster_from_collection_rec(collection):
    if collection is None:
        return None
    if get_is_cluster_collection(collection.name):
        return collection
    inner_cluster = get_cluster_collection_rec(collection)
    if inner_cluster is not None:
        return inner_cluster
    return get_parent_cluster_root(collection)

def get_cluster_from_active_object(context):
    if context.object is None:
        return None
    print("get_cluster_from_active_object object", context.object)
    return get_cluster_from_collection(context.object.users_collection[0])
    
def trim_name(name):
    return name.split('.')[0] + ']'

def trim_name_full(name):
    return name.split('.')[0]
    
def get_data_path():
    root_path = bpy.context.scene.re.engine_path
    return bpy.path.abspath(root_path + "hopper\\Hopper\\Hopper\\Resources\\Sources\\Data\\")
    
def link_utils_nodegroup(nodegroup):
    data_path = get_data_path() + "utils.blend\\NodeTree\\"
    bpy.ops.wm.link(filename=nodegroup, directory=data_path)