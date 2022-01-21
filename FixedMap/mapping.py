import bpy
from bpy.props import IntProperty, FloatProperty
import bmesh
import mathutils

import numpy as np
from numpy import savetxt
import os

list_vertices_s = []
list_vertices_t = []

class MainPanel(bpy.types.Panel):
    bl_label = "Fixed Map"
    bl_idname = "VIEW_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Set Fixed Map'
    
    def draw(self, context):
        props_s = bpy.context.scene.QueryPropsS
        props_t = bpy.context.scene.QueryPropsT
        layout = self.layout
        layout.scale_y = 1.2
        
        row = layout.row()
        row.prop(props_s, "query", text="Source name ")
        row.operator("wm.ss", icon= 'OBJECT_DATA', text= "Source")
        row = layout.row()
        row.prop(props_t, "query", text="Target name ")
        row.operator("wm.st", icon= 'OBJECT_DATA', text= "Target")
        row = layout.row()
        row.operator("wm.sm", icon= 'MESH_DATA', text= "Select Mode")
        row = layout.row()
        row.operator("wm.atm", icon= 'ADD', text= "Add pair to map")
        row.operator("wm.del", icon= 'REMOVE', text= "Delete pair from map")
        row = layout.row()
        row.operator("wm.exp", icon= 'EXPORT', text= "Export")
        row = layout.row()
        row.operator("wm.exit", icon= 'QUIT', text= "Exit")

class QueryProps(bpy.types.PropertyGroup):
    query: bpy.props.StringProperty(default="testtest")

class SetSource(bpy.types.Operator):
    bl_label = "Add Source"
    bl_idname = "wm.ss"
    
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            global source, name_s
            source = bpy.context.object
            name_s = bpy.context.scene.QueryPropsS.query
        else:
            ShowMessageBox("Select only one object")
        return {'FINISHED'}

class SetTarget(bpy.types.Operator):
    bl_label = "Add Target"
    bl_idname = "wm.st"
    
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            global target, name_t
            target = bpy.context.object
            name_t = bpy.context.scene.QueryPropsT.query
        else:
            ShowMessageBox("Select only one object")
        return {'FINISHED'}

class SelectMode(bpy.types.Operator):
    bl_label = "Select Mode"
    bl_idname = "wm.sm"
    
    def execute(self, context):
        if 'source' in globals() and 'target' in globals():
            source.select_set(True)
            target.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            ShowMessageBox("Source : " + str(source.name) + " Target : " + str(target.name))
        else:
            ShowMessageBox("Source and Target are not selected !", "Warning", 'ERROR')
        return {'FINISHED'}

class AddToMap(bpy.types.Operator):
    bl_label = "Add new pair to map"
    bl_idname = "wm.atm"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        list_selected_s = []
        list_selected_t = []
        for v in source.data.vertices:
            if v.select:
                list_selected_s.append(v.index)
        for v in target.data.vertices:
            if v.select:
                list_selected_t.append(v.index)
        if len(list_selected_s) == 1 and len(list_selected_t) == 1:
            list_vertices_s.append(list_selected_s[0])
            list_vertices_t.append(list_selected_t[0])
            ShowMessageBox("List of source vertices index : " + str(list_vertices_s).strip('[]') + " List of target vertices index : " + str(list_vertices_t).strip('[]'))
        else:
            ShowMessageBox("Select only 1 vertex on the source and 1 vertex on the target", "Warning", 'ERROR')
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
    
class DeleteToMap(bpy.types.Operator):
    bl_label = "Delete the most recent pair to map"
    bl_idname = "wm.del"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        list_vertices_s.pop()
        list_vertices_t.pop()
        ShowMessageBox("List of source vertices index : " + str(list_vertices_s).strip('[]') + " List of target vertices index : " + str(list_vertices_t).strip('[]'))
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
    
class Export(bpy.types.Operator):
    bl_label = "Export"
    bl_idname = "wm.exp"
    
    def execute(self, context):
        parent_dir = './data'
        os.mkdir(parent_dir)
        
        # export obj
        blend_file_path = bpy.data.filepath
        directory = os.path.dirname(blend_file_path)
        
        source.select_set(True)
        target.select_set(False)
        location_s = source.location.copy()
        source.location = (0, 0, 0)
        target_file_s = os.path.join(directory, parent_dir + '/' + name_s + '.obj')
        bpy.ops.export_scene.obj(filepath=target_file_s, use_selection=True)
        source.location = (location_s.x, location_s.y, location_s.z)
        
        source.select_set(False)
        target.select_set(True)
        location_t = target.location.copy()
        target.location = (0, 0, 0)
        target_file_t = os.path.join(directory, parent_dir + '/' + name_t + '.obj')
        bpy.ops.export_scene.obj(filepath=target_file_t, use_selection=True)
        target.location = (location_t.x, location_t.y, location_t.z)
        
        source.select_set(True)
        target.select_set(True)
        
        # create yml file
        f = open(parent_dir + "/fixed_map.yml", "w+")
        
        f.write("source:\n")
        f.write("  reference: " + name_s + ".obj\n\n")
        
        f.write("target:\n")
        f.write("  reference: " + name_t + ".obj\n\n")
        
        f.write("markers:\n")
        for i in range(len(list_vertices_s)):
            f.write('  - "' + str(list_vertices_s[i]) + ':' + str(list_vertices_t[i]) + '"')
            f.write("\n")
        f.close()
        return {'FINISHED'}
    
class Exit(bpy.types.Operator):
    bl_label = "Exit"
    bl_idname = "wm.exit"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        unregister()
        return {'FINISHED'}

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    
    
classes = (
    MainPanel,
    QueryProps,
    SetSource,
    SetTarget,
    SelectMode,
    AddToMap,
    DeleteToMap,
    Export,
    Exit
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.QueryPropsS = bpy.props.PointerProperty(type=QueryProps)
    bpy.types.Scene.QueryPropsT = bpy.props.PointerProperty(type=QueryProps)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del(bpy.types.Scene.QueryPropsS)
    del(bpy.types.Scene.QueryPropsT)

if __name__ == "__main__":
    register()