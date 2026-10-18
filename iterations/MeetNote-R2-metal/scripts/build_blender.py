import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];M=R/'mechanical';V=R/'visuals'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS';s.render.engine='CYCLES';s.cycles.samples=40;s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.exposure=-2.2
s.world.use_nodes=True;s.world.node_tree.nodes.clear();bg=s.world.node_tree.nodes.new('ShaderNodeBackground');wo=s.world.node_tree.nodes.new('ShaderNodeOutputWorld');bg.inputs[0].default_value=(.21,.25,.26,1);bg.inputs[1].default_value=.6;s.world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface'])
def material(n,c,metal=0,rough=.4,em=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],o.inputs['Surface']);p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=em;return m
spec={'aluminum':((.34,.43,.44),.85,.28),'polymer':((.065,.09,.092),0,.5),'steel':((.35,.4,.43),.8,.27),'pcb':((.055,.22,.15),0,.5),'chip':((.025,.034,.04),0,.4),'battery':((.54,.57,.60),.4,.35),'screen':((.02,.035,.04),0,.25),'glass':((.012,.024,.032),.15,.12),'gasket':((.09,.10,.11),0,.65),'adhesive':((.37,.48,.4),0,.55),'ceramic':((.71,.59,.35),0,.42),'fpc':((.65,.32,.045),.2,.38),'thermal':((.47,.58,.64),0,.65),'red':((.8,.09,.04),0,.25,1.5),'amber':((.9,.55,.12),0,.25,1.0),'membrane':((.16,.18,.18),0,.7),'white':((.7,.88,.85),0,.5,1.0)}
mats={k:material(k,*v) for k,v in spec.items()};objs={};manifest=json.loads((M/'scene_manifest.json').read_text());center=Vector((-.038,-.052,0))
for row in manifest:
 bpy.ops.wm.stl_import(filepath=str(M/row['mesh']),global_scale=.001);o=bpy.context.object;o.name=row['name'];o.location+=center;o.data.materials.clear();o.data.materials.append(mats[row['material']]);o['source']='FreeCAD STL mm -> m exactly 0.001';o['evidence']=row['status'];objs[o.name]=o
 if row['group']=='shell':
  mod=o.modifiers.new('Surface highlight only 0.15mm','BEVEL');mod.width=.00015;mod.segments=2
# Engineering-sized text and lens reflections are surface-only visual labels.
marks=[]
def txt(n,body,pos,size,back=False):
 cu=bpy.data.curves.new(n,'FONT');cu.body=body;cu.size=size;cu.extrude=0;o=bpy.data.objects.new(n,cu);s.collection.objects.link(o);o.location=Vector(pos)+center
 if back:o.rotation_euler[0]=math.pi
 o.data.materials.append(mats['white']);marks.append(o);return o
txt('Brand','M E E T N O T E',(.016,.016,.03405),.0033)
txt('Model','R2  /  AI COMPANION',(.016,.011,.03405),.0016)
txt('ScreenStatus','READY',(.026,.061,.00020),.0030,True)
txt('ScreenQuestion','Hold to speak',(.025,.053,.00020),.0020,True)
txt('ScreenBattery','Wi-Fi     78%',(.025,.039,.00020),.0015,True)
# Lens concentric rings fit inside reserved optical opening.
for i,(rad,z,col) in enumerate([(.0058,.03381,'chip'),(.0042,.03384,'glass'),(.0024,.03387,'pcb')]):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=rad,depth=.00002,location=Vector((.0555,.055,z))+center);o=bpy.context.object;o.name='VISUAL_LensLayer'+str(i);o.data.materials.append(mats[col]);marks.append(o)
def area(n,loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.02))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(.09,-.08,.24),6,.18);area('Fill',(-.14,.04,.16),5,.17);area('Edge',(.06,.19,.12),6,.12);area('Backlight',(-.06,.03,-.18),5,.16)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
def view(name,loc,target=(0,0,.017),scale=.17):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(V/(name+'.png'));bpy.ops.render.render(write_still=True)
view('01_front',(.15,-.17,.25),scale=.175)
view('02_back',(.15,.16,-.24),scale=.18)
# True shell cutaway; internals remain at original coordinates.
bpy.ops.mesh.primitive_cube_add(size=1,location=(.15,0,.05));tool=bpy.context.object;tool.name='Section_Xpositive';tool.scale=(.30,.40,.30);tool.hide_render=True;tool.display_type='WIRE';mods=[]
for row in manifest:
 if row['group'] in ['shell','glass','seal']:
  o=objs[row['name']];mod=o.modifiers.new('Engineering center section','BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;mods.append((o,mod))
for o in marks:o.hide_render=True
view('03_section',(.22,-.13,.16),scale=.175)
for o,mod in mods:o.modifiers.remove(mod)
# Exploded assembly view - retain original transforms after export.
original={n:o.location.copy() for n,o in objs.items()}
for row in manifest:
 o=objs[row['name']];n=o.name
 if n.startswith('Rear') or n.startswith('Display') or n.startswith('Screw'):o.location.z-=.026
 elif n=='BatteryEnvelope':o.location.z-=.012
 elif row['group']=='shell' or n in ['CameraCoverGlass','CameraBondRing']:o.location.z+=.040
 elif n.startswith(('GNSS','Compute','CameraModule','Thermal')):o.location.z+=.016
view('04_exploded',(.22,-.18,.18),target=(0,0,.025),scale=.23)
for n,o in objs.items():o.location=original[n]
for o in marks:o.hide_render=False
cam.location=(.15,-.17,.25);cam.rotation_euler=(Vector((0,0,.017))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.175
s['NOTICE']='R2 packaging study. Exact FreeCAD mesh scale. No R2 routed PCB. Unknown component envelopes and unvalidated antenna/thermal/sealing.'
bpy.ops.wm.save_as_mainfile(filepath=str(V/'MeetNote_R2.blend'))
