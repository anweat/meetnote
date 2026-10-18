import bpy,math,json
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[1];M=R/'mechanical';V=R/'visuals';V.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS';scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.5,.5,.5);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-2.2;scene.render.image_settings.file_format='PNG'
def mat(name,c,metal=0,rough=.4,emit=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
mats={k:mat(k,*args) for k,args in {'shell':((.052,.077,.105),0,.3),'lid':((.73,.76,.78),.05,.3),'pcb':((.035,.19,.14),0,.5),'cell':((.37,.4,.45),.5,.3),'chip':((.035,.04,.05),0,.4),'camera':((.05,.055,.06),0,.2),'metal':((.58,.63,.68),.8,.25),'red':((.9,.04,.015),0,.3,2),'blue':((.03,.28,.95),0,.25,2),'amber':((1,.5,.015),0,.25,2),'cap':((.07,.095,.13),0,.4),'hand':((.56,.35,.22),0,.65),'floor':((.16,.19,.23),0,.7)}.items()}
objects={}
manifest=json.loads((M/'scene_manifest.json').read_text())
for row in manifest:
 bpy.ops.wm.stl_import(filepath=str(M/row['mesh']),global_scale=.001)
 o=bpy.context.object;o.name=row['name'];o.location+=Vector((-.041,-.059,0));objects[o.name]=o
 name=o.name
 k='chip'
 if name.startswith('Base'):k='shell'
 elif name.startswith('Lid'):k='lid'
 elif name=='CarrierImportedKiCad':k='pcb'
 elif name=='BatteryEnvelope':k='cell'
 elif name=='Zero2WEnvelope':k='pcb'
 elif name=='CameraEnvelope':k='camera'
 elif name=='HeatSpreader':k='metal'
 elif name.startswith('ButtonAssembly'):k='red' if name.endswith('0') else 'cap'
 elif name.startswith('LightPipe'):k=['red','amber','blue'][int(name[-1])]
 o.data.materials.append(mats[k]);o['dimension_source']='FreeCAD STL in mm; converted to meters using 0.001 exactly';o['engineering_status']='R0 envelope; see fit report'
 if name.startswith(('Base','Lid')):
  bevel=o.modifiers.new('Presentation edge highlight 0.3mm','BEVEL');bevel.width=.0003;bevel.segments=2
# camera glass is a visual-only surface within reserved optical gap, not exported mechanical glass specification.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.0055,depth=.0003,location=(.0155,.026,.0265));lens=bpy.context.object;lens.name='VISUAL_ONLY_LensGlass';lens.data.materials.append(mats['camera'])
# Surface marks on top (all values in meters)
def text(name,body,pos,size=.0025,material='cap'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.000005;o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=pos;o.data.materials.append(mats[material]);return o
marks=[text('Brand','MEETNOTE',(-.030,-.035,.0292),.004),text('Model','R0 / ENGINEERING PROTOTYPE',(-.030,-.041,.0292),.0016),text('Mode','CONSENT  /  CAPTURE',(-.030,-.048,.0292),.0016)]
# Hand is an explicitly schematic 180mm size-reference silhouette, not a photorealistic human hand.
hand=[]
def ellipsoid(name,loc,scale):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mats['hand']);hand.append(o);return o
ellipsoid('ReferencePalm',(.008,-.041,-.014),(.044,.052,.009))
for i,(x,l) in enumerate([(-.027,.072),(-.006,.082),(.015,.078),(.034,.061)]):ellipsoid('ReferenceFinger'+str(i),(x,.004+l/2,-.014),(.009,l/2,.008))
thumb=ellipsoid('ReferenceThumb',(-.043,-.010,-.006),(.014,.04,.01));thumb.rotation_euler[2]=-.5
ellipsoid('ReferenceWrist',(.01,-.10,-.015),(.03,.033,.009))
for o in hand:o.hide_render=True
# Lighting / cameras
def area(name,loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.015))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(.06,-.09,.25),8,.20);area('Fill',(-.14,.02,.15),5,.16);area('Rim',(.05,.16,.18),7,.12);area('Underside',(0,-.04,-.20),4,.18)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='EngineeringCamera';scene.camera=camera;camera.data.type='ORTHO';camera.data.lens=50
scene.render.film_transparent=False;scene.world.use_nodes=True;scene.world.node_tree.nodes.clear();bg=scene.world.node_tree.nodes.new('ShaderNodeBackground');wo=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld');scene.world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);bg.inputs[0].default_value=(.12,.15,.19,1);bg.inputs[1].default_value=.5
# Keep all saved object transforms in engineering coordinates. Views change camera/cut visibility only.
def view(name,loc,target=(0,0,.015),scale=.18):
 camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(V/(name+'.png'));bpy.ops.render.render(write_still=True)
view('01_front',(.135,-.17,.23),scale=.19)
for o in marks:o.hide_render=True
view('02_back',(.13,.16,-.24),scale=.19)
for o in marks:o.hide_render=False
# Geometric section: Boolean cut at X=0 through shells only, retains physical internal component positions.
bpy.ops.mesh.primitive_cube_add(size=1,location=(.125,0,.06));cutter=bpy.context.object;cutter.name='SectionTool_X_Positive';cutter.scale=(.25,.4,.3);cutter.hide_render=True;cutter.display_type='WIRE'
mods=[]
for o in objects.values():
 if o.name.startswith(('Base','Lid')):
  mod=o.modifiers.new('Section at center plane','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;mods.append((o,mod))
for o in marks:o.hide_render=True
view('03_section',(.23,-.16,.17),scale=.19)
for o,mod in mods:o.modifiers.remove(mod)
for o in marks:o.hide_render=False
for o in hand:o.hide_render=False
view('04_hand_scale',(.03,-.08,.36),target=(0,-.018,.008),scale=.27)
for o in hand:o.hide_render=True
camera.location=(.135,-.17,.23);camera.rotation_euler=(Vector((0,0,.015))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.19
scene['engineering_notice']='All device meshes from FreeCAD; RF conflicts and unmodeled cables remain. Hand is a schematic reference; render is not fit proof.'
bpy.ops.wm.save_as_mainfile(filepath=str(V/'MeetNote_R0.blend'))
print('Four views + native .blend saved')
