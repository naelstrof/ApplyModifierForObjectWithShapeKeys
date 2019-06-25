# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2015 Przemysław Bągard
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
    "author":       "Przemysław Bągard and Naelstrof",
    "blender":      (2,80,0),
    "version":      (0,2,0),
    "location":     "Context menu",
    "description":  "Applies modifiers for objects with shape keys. Only works on modifiers that create consistent vertex counts.",
    "category":     "Tool Menu > Modifier Tools"
}

import bpy, math
from bpy.props import *
import time;

# Algorithm:
# - Duplicate active object as many times as the number of shape keys
# - For each copy remove all shape keys except one
# - Removing last shape does not change geometry data of object
# - Apply modifier for each copy
# - Join objects as shapes and restore shape keys names
# - Delete all duplicated object except one
# - Delete old object
# - Restore name of object and object data
def applyModifiersForObjectWithShapeKeys(context, operator, modifierName="", all=False, profile=False):
    firstTime = time.time()
    lastTime = time.time()
    if profile:
        lastTime = time.time()
        print("Apply modifier START: " + str(lastTime))
    
    list_names = []
    list = []
    list_shapes = []
    hasArmature = False
    armatureTarget = None
    
    if all:
        for i in context.active_object.modifiers:
            if ( i.type == "ARMATURE" ):
                hasArmature = True
                armatureTarget = i.object

    if context.active_object.data.shape_keys:
        list_shapes = [o for o in context.active_object.data.shape_keys.key_blocks]
    
    if(list_shapes == []):
        if (all):
            bpy.ops.object.convert()
        else:
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifierName)
        return context.active_object
    
    list.append(context.active_object)
    for i in range(1, len(list_shapes)):
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "constraint_axis":(False, False, False), "mirror":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "texture_space":False, "release_confirm":False})
        list.append(context.active_object)
    
    if profile:
        print("Duplication finished: " + str(time.time()-lastTime))
        lastTime = time.time()
    
    if ( all ):
        bpy.ops.object.select_all(action='DESELECT')
        for i, o in enumerate(list):
            o.select_set(True)
            context.view_layer.objects.active = o
            list_names.append(o.data.shape_keys.key_blocks[i].name)
            bpy.ops.object.shape_key_clear()
            o.data.shape_keys.key_blocks[i].value = 1
            # there's a bug in convert that just applies all modifiers and shape keys.
            # It's much faster than removing shape keys and applying modifiers by about 10x (1000% faster)
            bpy.ops.object.convert()
            o.select_set(False)
    else:
        for i, o in enumerate(list):
            o.select_set(True)
            context.view_layer.objects.active = o
            list_names.append(o.data.shape_keys.key_blocks[i].name)
            for j in range(i+1, len(list))[::-1]:
                o.active_shape_key_index = j
                bpy.ops.object.shape_key_remove()
            for j in range(0, i):
                o.active_shape_key_index = 0
                bpy.ops.object.shape_key_remove()
            o.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove()
            o.select_set(False)
    
    if profile:     
        print("ShapeKey Removal finished: " + str(time.time()-lastTime))
        lastTime = time.time()
    
    bpy.ops.object.select_all(action='DESELECT')
    if (not all):
        for i, o in enumerate(list):
            o.select_set(True)
            context.view_layer.objects.active = o
            # time to apply modifiers
            bpy.ops.object.modifier_apply(override, apply_as='DATA', modifier=modifierName)
            o.select_set(False)
    
    if profile and not all:
        print("Modifier Application finished: " + str(time.time()-lastTime))
        lastTime = time.time()
        
    bpy.ops.object.select_all(action='DESELECT')
    for i in list:
        i.select_set(True)
    context.view_layer.objects.active = list[0]
    bpy.ops.object.join_shapes()
    if (len(list[0].data.shape_keys.key_blocks) != len(list_names)):
        operator.report({"WARNING"}, message="Some keys were lost due to differing vertex counts...")
    for i in range(0, len(list[0].data.shape_keys.key_blocks)):
        list[0].data.shape_keys.key_blocks[i].name = list_names[i]
        
    if profile:
        print("Mesh Join finished: " + str(time.time()-lastTime))
        lastTime = time.time()
    
    bpy.ops.object.select_all(action='DESELECT')
    override = bpy.context.copy()
    override["selected_objects"] = list[1:]
    override["active_object"] = None
    override["object"] = None
    bpy.ops.object.delete(override,use_global=False)
    
    if all and hasArmature:
        context.view_layer.objects.active = list[0]
        list[0].select_set(True)
        bpy.ops.object.modifier_add(type='ARMATURE')
        context.active_object.modifiers[0].object = armatureTarget
    
    if profile:
        print("Deletion finished: " + str(time.time()-lastTime))
        lastTime = time.time()
        print("Apply Modifier FINISHED, total time:" + str(time.time()-firsttime))
    
    return context.active_object

class AMWSK_OT_ApplyAllModifiersForObjectWithShapeKeysOperator(bpy.types.Operator):
    bl_idname = "object.apply_all_modifiers_for_object_with_shape_keys"
    bl_label = "Apply all modifiers (Faster)"
    
    def execute(self, context):
        applyModifiersForObjectWithShapeKeys(context, self, all=True)
        return {'FINISHED'}
    
class AMWSK_OT_ApplyModifierForObjectWithShapeKeysOperator(bpy.types.Operator):
    bl_idname = "object.apply_modifier_for_object_with_shape_keys"
    bl_label = "Apply single modifier"
 
    def item_list(self, context):
        return [(modifier.name, modifier.name, modifier.name) for modifier in bpy.context.active_object.modifiers]
 
    my_enum = EnumProperty(name="Modifier name",
        items = item_list)
 
    def execute(self, context):
        applyModifiersForObjectWithShapeKeys(context, self, self.my_enum)
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class AMWSK_PT_Setup(bpy.types.Panel):
    bl_label = "Modifier Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
 
    def draw(self, context):
        layout = self.layout
        layout.operator("object.apply_modifier_for_object_with_shape_keys")
        layout.operator("object.apply_all_modifiers_for_object_with_shape_keys")

classes = (AMWSK_OT_ApplyAllModifiersForObjectWithShapeKeysOperator, AMWSK_OT_ApplyModifierForObjectWithShapeKeysOperator, AMWSK_PT_Setup)
register, unregister = bpy.utils.register_classes_factory(classes)
 
if __name__ == "__main__":
    register()