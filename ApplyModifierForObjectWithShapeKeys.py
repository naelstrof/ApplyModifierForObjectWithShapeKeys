# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2019 Naelstrof
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

bl_info = {
    "name":         "Apply modifier for object with shape keys",
    "author":       "Przemysław Bągard and Naelstrof", # Przemysław Bągard made the original, Naelstrof updated it to 2.8
    "blender":      (2,80,0),
    "location":     "View3D",
    "description":  "Applies modifiers even if the object has shape keys. Only works on modifiers that create consistent vertex counts and orders.",
    "category":     "Generic"
}

import bpy, math
from bpy.props import *

# Algorithm:
# - Duplicate active object as many times as the number of shape keys
# - For each copy remove all shape keys except one
# - Removing last shape does not change geometry data of object
# - Apply modifier for each copy
# - Join objects as shapes and restore shape keys names
# - Delete all duplicated object except one
# - Delete old object
# - Restore name of object and object data
def applyModifierForObjectWithShapeKeys(context, modifierName):
    list_names = []
    list = []
    list_shapes = []
    if context.active_object.data.shape_keys:
        list_shapes = [o for o in context.active_object.data.shape_keys.key_blocks]
    
    if(list_shapes == []):
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifierName)
        return context.active_object
    
    list.append(context.active_object)
    for i in range(1, len(list_shapes)):
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "constraint_axis":(False, False, False), "mirror":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "texture_space":False, "release_confirm":False})
        list.append(context.active_object)

    for i, o in enumerate(list):
        override = bpy.context.copy()
        override["active_object"] = o
        override["object"] = o
        override["selected_objects"] = [o]
        
        list_names.append(o.data.shape_keys.key_blocks[i].name)
        for j in range(i+1, len(list))[::-1]:
            o.active_shape_key_index = j
            bpy.ops.object.shape_key_remove(override)
        for j in range(0, i):
            o.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(override)
        o.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove(override)
        
        # time to apply modifiers
        bpy.ops.object.modifier_apply(override, apply_as='DATA', modifier=modifierName)
    
    bpy.ops.object.select_all(action='DESELECT')
    for i in list:
        i.select_set(True)
    override = bpy.context.copy()
    override["active_object"] = list[0]
    override["selected_objects"] = list
    
    bpy.ops.object.join_shapes(override)
    for i in range(0, len(list)):
        list[0].data.shape_keys.key_blocks[i].name = list_names[i]
    
    bpy.ops.object.select_all(action='DESELECT')
    override["selected_objects"] = list[1:]
    override["active_object"] = None
    override["object"] = None
    bpy.ops.object.delete(override,use_global=False)
    return context.active_object

class AMWSK_OT_ApplyModifierWithShapeKeys(bpy.types.Operator):
    bl_label = "Apply modifier for object with shape keys"
    bl_idname = "object.apply_modifier_for_object_with_shape_keys"
 
    def item_list(self, context):
        return [(modifier.name, modifier.name, modifier.name) for modifier in bpy.context.active_object.modifiers]
 
    my_enum = EnumProperty(name="Modifier name",
        items = item_list)
 
    def execute(self, context):
        applyModifierForObjectWithShapeKeys(context, self.my_enum)
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class AMWSK_PT_Panel(bpy.types.Panel):
    bl_idname = "AMWSK_PT_Panel"
    bl_label = "Modifier Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
 
    def draw(self, context):
        self.layout.operator("object.apply_modifier_for_object_with_shape_keys")
 
 
def menu_func(self, context):
    self.layout.operator("object.apply_modifier_for_object_with_shape_keys", 
        text="Apply modifier for object with shape keys")

classes = (AMWSK_OT_ApplyModifierWithShapeKeys, AMWSK_PT_Panel)
register, unregister = bpy.utils.register_classes_factory(classes)