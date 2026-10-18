"""PYTHONPATH=<FreeCAD>/lib <FreeCAD>/bin/python this_file.py"""
import FreeCAD as A,Part,Mesh,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];M=R/'mechanical';V=R/'verification';S=M/'meshes';S.mkdir(exist_ok=True)
p=json.loads((M/'parameters.json').read_text());d=A.newDocument('MeetNote_R0');ss=d.addObject('Spreadsheet::Sheet','Parameters')
for row,(key,val) in enumerate([('Width',82),('Length',118),('Height',29),('Wall',1.8),('CarrierZ',11.6),('BatteryZ',2.2),('CameraZ',14)],1):ss.set('A'+str(row),key);ss.set('B'+str(row),str(val)+' mm');ss.setAlias('B'+str(row),key)
def box(name,size,pos,expr=None):
 o=d.addObject('Part::Box',name);o.Label=name;o.Length,o.Width,o.Height=size;o.Placement.Base=A.Vector(*pos)
 if expr:
  for k,v in expr.items():o.setExpression(k,v)
 return o
def cyl(name,r,h,pos):
 o=d.addObject('Part::Cylinder',name);o.Radius=r;o.Height=h;o.Placement.Base=A.Vector(*pos);return o
def cut(name,a,b):
 o=d.addObject('Part::Cut',name);o.Base=a;o.Tool=b;return o
def union(name,ls):
 o=d.addObject('Part::MultiFuse',name);o.Shapes=ls;return o
base=box('BaseOuter',[82,118,16],[0,0,0],{'Length':'Parameters.Width','Width':'Parameters.Length'})
cavity=box('BaseCavity',[78.4,114.4,16],[1.8,1.8,1.8],{'Length':'Parameters.Width-2*Parameters.Wall','Width':'Parameters.Length-2*Parameters.Wall'})
base=cut('BaseShell',base,cavity)
bosses=[]
for i,(x,y) in enumerate(p['case_screws']):
 bosses.append(cut('ScrewBoss'+str(i),cyl('BossOuter'+str(i),3,14,[x,y,1.8]),cyl('BossPilot'+str(i),.85,16,[x,y,1.8])))
# Lower edge near PCB mounting holes; small posts avoid battery pouch.
for i,(x,y) in enumerate([(9,52),(73,52),(9,102),(73,102)]):
 bosses.append(cut('CarrierPost'+str(i),cyl('CarrierPostOuter'+str(i),1.8,9.8,[x,y,1.8]),cyl('CarrierPilot'+str(i),.85,11,[x,y,1.8])))
base=union('BaseWithPosts',[base]+bosses)
# Microphone path: 0.6mm outer aperture, generous port channel through bottom; gasket not yet detailed.
for i,(x,y) in enumerate(p['mic_centers']):base=cut('BaseMicPort'+str(i),base,cyl('MicBore'+str(i),.5,14,[x,y,0]))
# Interface cutouts are provisional dimensional envelopes, actual USB board not selected.
base=cut('BaseUSBOpening',base,box('USBOpeningTool',[11,4,5],[35.5,115,5]))
base=cut('BaseConsentOpening',base,box('ConsentOpeningTool',[4,14,6],[-1,63,5]))
base.Label='BASE - 82x118x16 - prototype'
top=box('LidOuter',[82,118,12.8],[0,0,16.2],{'Length':'Parameters.Width','Width':'Parameters.Length','Height':'Parameters.Height-16.2 mm'})
top=cut('LidShell',top,box('LidCavity',[78.4,114.4,11],[1.8,1.8,16.2]))
for i,(x,y) in enumerate(p['case_screws']):top=cut('LidScrew'+str(i),top,cyl('LidScrewTool'+str(i),1.1,15,[x,y,16]))
top=cut('LidCameraWindow',top,cyl('CameraWindowTool',6.5,5,[56.5,85,26]))
for i,x in enumerate([31,42,53,64]):top=cut('LidButton'+str(i),top,cyl('ButtonTool'+str(i),3.6,5,[x,103,26]))
for i,y in enumerate([86,94,78]):top=cut('LidLED'+str(i),top,cyl('LEDTool'+str(i),1.2,5,[31,y,26]))
top.Label='LID - removable, 0.2mm seam'
# Import the STEP exported by KiCad, do not recreate a nominal PCB box for fit check.
shape=Part.read(str(M/'carrier_from_kicad.step'));bb=shape.BoundBox
# KiCad STEP Y is negative; rotate to map the exported local Y to case Y exactly.
if bb.YMin<-.1:
 shape.rotate(A.Vector(0,0,0),A.Vector(1,0,0),180)
bb=shape.BoundBox;shape.translate(A.Vector(6-bb.XMin,42-bb.YMin,11.6-bb.ZMin))
carrier=d.addObject('PartDesign::Feature','CarrierImportedKiCad');carrier.Shape=shape;carrier.Label='PCB IMPORTED FROM KiCad STEP (board only)'
carrier.addProperty('App::PropertyString','Source').Source='carrier_from_kicad.step'
cell=box('BatteryEnvelope',[60,50,7.3],[11,49,2.2],{'Placement.Base.z':'Parameters.BatteryZ'})
# Nominal Zero board plus explicit conservative top-component envelopes.
soc=box('Zero2WEnvelope',[65,30,6],[8,8,15]);soc.Label='Zero 2 W conservative module envelope; connector geometry pending'
cam=box('CameraEnvelope',[25,24,11.5],[44,73,14],{'Placement.Base.z':'Parameters.CameraZ'});cam.Label='Camera Module 3 maximum envelope; exact lens axis pending drawing'
rf=box('RFKeepout',[72,35,25.4],[5,5,1.8]);rf.Label='RF: no carrier/battery/metal; Zero own board exempt'
spreader=box('HeatSpreader',[30,22,.8],[35,12,24.8]);pad=box('ThermalGapPad',[20,15,3.8],[40,15,21]);spreader.Label='Al heat spreader PROVISIONAL - RF exception must be verified'
# Above RF is intentionally flagged: cannot call close fit solved when heat path violates keepout.
usb=box('USBPowerBoardReserved',[24,12,8],[28,101,3]);usb.Label='UNVERIFIED USB/charge PCB reservation, not a purchased module'
consent=box('ConsentSwitchReserved',[8,14,6],[1.8,63,5]);consent.Label='UNVERIFIED dual pole physical switch reservation'
# Low electronics component envelopes match placed footprints, without pretending package STEP accuracy.
placements=json.loads((R/'electronics/placement_manifest.json').read_text());parts=[]
for c in placements:
 ref=c['reference'];x,y=c['x']+6,c['y']+42
 if ref=='J1':size=[5,51,8];pos=[x-1.3,y-1.3,13.2]
 elif ref.startswith('J'):size=[3,3+(2.54*3 if ref=='J5' else 2.54),8];pos=[x-1.5,y-1.5,13.2]
 elif ref=='U1':size=[7,7,1];pos=[x-3.5,y-3.5,13.2]
 elif ref.startswith('MK'):size=[4,3,1.2];pos=[x-2,y-1.5,13.2]
 elif ref.startswith('SW'):size=[6,6,2.5];pos=[x-3,y-3,13.2]
 else:size=[1.6,.8,.8];pos=[x-.8,y-.4,13.2]
 o=box('ECAD_'+ref,size,pos);o.Label=ref+' approximate component body';parts.append(o)
# Real button caps with stems; travel/coupling unresolved and tracked.
caps=[]
for i,x in enumerate([31,42,53,64]):
 stem=cyl('ButtonStem'+str(i),1.3,11.9,[x,103,16]);cap=cyl('ButtonCap'+str(i),3.25,1.2,[x,103,27.7]);caps.append(union('ButtonAssembly'+str(i),[stem,cap]))
lights=[]
for i,y in enumerate([86,94,78]):lights.append(cyl('LightPipe'+str(i),.9,14.5,[31,y,14]))
d.recompute()

d.recompute()
for obj in d.Objects:
 if hasattr(obj,'Shape') and obj.Shape.isNull(): print('NULL',obj.Name,obj.State)
final=[base,top,carrier,cell,soc,cam,spreader,pad,usb,consent]+parts+caps+lights
# Geometric checks: solid intersections only. No cable bend/electrical/RF/thermal performance inference.
checks=[]
for i,a in enumerate(final):
 for b in final[i+1:]:
  vol=a.Shape.common(b.Shape).Volume
  if vol>0.01:checks.append({'a':a.Name,'b':b.Name,'intersection_mm3':round(vol,4),'status':'UNRESOLVED','note':'positive-volume contact; classify intended thermal contact vs interference manually'})
rfchecks=[]
for a in [carrier,cell,spreader,pad,usb,consent]+parts:
 vol=rf.Shape.common(a.Shape).Volume
 if vol>.01:rfchecks.append({'object':a.Name,'volume_mm3':round(vol,3),'status':'RF_KEEP_OUT_VIOLATION'})
# conservative battery swelling to 8.3mm and lid +/-0.2mm clearance check
clearances={'battery_to_pcb_nominal_mm':11.6-(2.2+7.3),'battery_to_pcb_with_1mm_growth_mm':11.6-(2.2+8.3),'camera_to_lid_inner_mm':27.2-(14+11.5),'pcb_import_bbox_mm':[round(carrier.Shape.BoundBox.XLength,4),round(carrier.Shape.BoundBox.YLength,4),round(carrier.Shape.BoundBox.ZLength,4)],'cables':'not modeled as flexible swept solids; FPC/harness remains unresolved','models':'package body envelopes only; board STEP import verified'}
(V/'mechanical_fit.json').write_text(json.dumps({'solid_intersections':checks,'rf_keepout':rfchecks,'clearances':clearances,'freecad_version':A.Version()},indent=2))
for o in final:
 Mesh.export([o],str(S/(o.Name+'.stl')))
# visibility stored in manifest because headless FreeCAD has no GUI provider
(M/'scene_manifest.json').write_text(json.dumps([{'name':o.Name,'label':o.Label,'mesh':'meshes/'+o.Name+'.stl'} for o in final],indent=2))
Part.export(final,str(M/'MeetNote_assembly.step'));Part.export([base],str(M/'case_base.step'));Part.export([top],str(M/'case_lid.step'))
Mesh.export([base],str(M/'case_base.stl'));Mesh.export([top],str(M/'case_lid.stl'))
d.recompute();d.saveAs(str(M/'MeetNote_R0.FCStd'))
print('FCStd/STEP/STL generated; intersections=',len(checks),'RF=',len(rfchecks),clearances)
