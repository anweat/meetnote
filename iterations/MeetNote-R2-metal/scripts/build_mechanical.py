import FreeCAD as A, Part, Mesh, json, math
from pathlib import Path
R=Path(__file__).resolve().parents[1]; M=R/'mechanical'; V=R/'verification'; p=json.loads((M/'parameters.json').read_text())
d=A.newDocument('MeetNote_R2_Metal'); ss=d.addObject('Spreadsheet::Sheet','Parameters')
for i,(key,val) in enumerate([(k,p[k]) for k in ['width','length','height','corner_radius','wall','rf_seam_y']],1):
 ss.set('A'+str(i),key);ss.set('B'+str(i),str(val)+' mm');ss.setAlias('B'+str(i),key)
final=[]; meta={}
def box(n,size,pos):
 o=d.addObject('Part::Box',n);o.Length,o.Width,o.Height=size;o.Placement.Base=A.Vector(*pos);return o
def cyl(n,r,h,pos,axis=None):
 o=d.addObject('Part::Cylinder',n);o.Radius=r;o.Height=h;o.Placement.Base=A.Vector(*pos)
 if axis:o.Placement.Rotation=A.Rotation(A.Vector(0,0,1),A.Vector(*axis))
 return o
def fuse(n,objs):
 o=d.addObject('Part::MultiFuse',n);o.Shapes=objs;return o
def cut(n,a,b):
 o=d.addObject('Part::Cut',n);o.Base=a;o.Tool=b;return o
def common(n,a,b):
 o=d.addObject('Part::Common',n);o.Base=a;o.Tool=b;return o
def rounded(n,w,l,h,r,pos):
 x,y,z=pos
 parts=[box(n+'WebX',[w-2*r,l,h],[x+r,y,z]),box(n+'WebY',[w,l-2*r,h],[x,y+r,z])]
 for i,(cx,cy) in enumerate([(x+r,y+r),(x+w-r,y+r),(x+r,y+l-r),(x+w-r,y+l-r)]):parts.append(cyl(n+'Corner'+str(i),r,h,[cx,cy,z]))
 return fuse(n,parts)
def finish(o,material,status='designed envelope',group='internal'):
 final.append(o);meta[o.Name]={'material':material,'status':status,'group':group};o.addProperty('App::PropertyString','Evidence').Evidence=status;return o
W,L,H,t=p['width'],p['length'],p['height'],p['wall'];cy=p['rf_seam_y']
outer=rounded('OuterTub',W,L,H-1.8,12,[0,0,1.8]);inside=rounded('InsideTool',W-2*t,L-2*t,H-1.5,12-t,[t,t,0]);tub=cut('HollowTub',outer,inside)
metal=common('MetalBlank',tub,box('LowerSplit',[W+2,cy,H+2],[-1,0,0]))
rf=common('RFBlank',tub,box('UpperSplit',[W+2,L-cy-.2,H+2],[-1,cy+.2,0]))
# Optical seating: cover disk inserted into through bore, perimeter adhesive below glass.
metal=cut('MetalCameraBore',metal,cyl('OpticalBore',8,5,[55.5,55,30]))
metal=fuse('MetalOpticalSeat',[metal,cut('OpticalSeatRing',cyl('OpticalSeatOD',8.4,.4,[55.5,55,32.5]),cyl('OpticalSeatID',6.2,.6,[55.5,55,32.4]))])
# Hardware indicator windows (separate mic and camera status).
for i,(x,y) in enumerate([(18,61),(18,66)]):metal=cut('MetalLampCut'+str(i),metal,box('LampTool'+str(i),[12,1.6,4],[x,y,31]))
# USB at lower edge; two side button openings and a hard privacy slider.
metal=cut('MetalUSB',metal,box('USBTool',[11,4,5],[32.5,-1,8]))
for i,y in enumerate([25,39]):metal=cut('MetalButtonCut'+str(i),metal,box('ButtonTool'+str(i),[4,10,5],[W-2,y,20]))
metal=cut('MetalPrivacyCut',metal,box('PrivacyTool',[4,12,5],[-1,33,20]))
# Acoustic bores through outward face, membrane seats beneath the front skin.
for i,(x,y) in enumerate([(7,64),(70.5,64),(9,91),(68,91)]):
 tool=cyl('MicPortTool'+str(i),.55,4,[x,y,31]);
 if y<cy:metal=cut('MetalMic'+str(i),metal,tool)
 else:rf=cut('RFMic'+str(i),rf,tool)
metal=finish(metal,'aluminum','6061 candidate; tool access and tolerances not reviewed','shell');metal.Label='6061 metal front + middle frame / 1.5mm nominal'
rf=finish(rf,'polymer','RF window geometry; material and antenna tuning pending','shell');rf.Label='Nonmetal antenna cap / no metallized paint'
# Rear nonmetal cover; internal flange and four independent screw bosses.
back=rounded('RearBlank',W-1,L-1,1.5,11.5,[.5,.5,0]);back=cut('RearScreenOpening',back,rounded('ScreenHole',30.6,36.6,3,3,[22.45,31.2,-.5]))
back=cut('RearGlassRecess',back,rounded('GlassPocket',33.9,41.4,1.25,3.2,[20.8,28.8,-.1]))
# Screen glass has perimeter seat; visible aperture smaller than glass.
back=finish(back,'polymer','removable backplate; no IP rating','shell')
gasketOuter=rounded('GasketOuter',W-3.4,L-3.4,.3,10.3,[1.7,1.7,1.5]);gasketInner=rounded('GasketInner',W-5.8,L-5.8,.5,9.1,[2.9,2.9,1.4]);gasket=finish(cut('RearCompressionGasket',gasketOuter,gasketInner),'gasket','compressed thickness 0.30mm target; stock 0.40mm candidate','seal')
# Screws are accessible through back; bosses attached to side wall by webs.
for i,(x,y) in enumerate([(6,8),(70,8),(6,96),(70,96)]):
 boss=cut('Boss'+str(i),cyl('BossOuter'+str(i),2.6,7,[x,y,1.8]),cyl('BossBore'+str(i),.85,8,[x,y,1.6]));finish(boss,'aluminum' if y<cy else 'polymer','M2 pilot/insert placeholder; threads not modeled','fastener')
 stem=cyl('ScrewStem'+str(i),.8,6,[x,y,.3]);head=cyl('ScrewHead'+str(i),1.7,.7,[x,y,0]);screw=fuse('Screw'+str(i),[stem,head]);finish(screw,'steel','M2 geometric placeholder','fastener')
 # bore backplate and head pocket, preserving finished object identity list
 old=back;final.remove(old);back=cut('RearScrewHole'+str(i),old,cyl('RearScrewBore'+str(i),1.0,2,[x,y,-.2]));back=cut('RearHeadPocket'+str(i),back,cyl('HeadPocketTool'+str(i),1.9,.9,[x,y,-.1]));back=finish(back,'polymer','removable backplate; recessed screw heads','shell')
# Two separated load bearing polymer lugs, loop bores run through Z.
lugs=[]
for i,x in enumerate([21,34]):
 lug=cut('StrapLug'+str(i),rounded('LugBlank'+str(i),7,10,4,2,[x,98,22]),box('LugBore'+str(i),[3,5,6],[x+2,100,21]));lugs.append(lug)
final.remove(rf);rf=finish(fuse('RFCapWithStrapLugs',[rf]+lugs),'polymer','integrated lugs; pull force and cap retention OPEN','shell')
# Top-cap attachment joint: explicit adhesive strip at center seam front, not a full sealing path.
finish(box('TopCapBond',[55,.2,1.2],[10,cy,32.6]),'adhesive','0.20mm adhesive gap; perimeter continuity and fixture unresolved','seal')
# Internal motherboard placeholder, not R0 imported PCB; component envelopes explicitly identified.
car=box('CarrierPCB_Proposed',p['carrier']['size'],p['carrier']['position'])
for i,(x,y) in enumerate([(7,13),(69,13),(7,78),(69,78)]):car=cut('CarrierHole'+str(i),car,cyl('CarrierHoleTool'+str(i),1.1,3,[x,y,15.5]))
for i,(x,y) in enumerate([(7,13),(69,13),(7,78),(69,78)]):
 post=cut('PCBPost'+str(i),cyl('PCBPostOuter'+str(i),2,14.5,[x,y,1.5]),cyl('PCBPostBore'+str(i),1.0,15,[x,y,1.3]));finish(post,'polymer','spacer envelope; attachment and preload OPEN','fastener')
finish(car,'pcb','proposed board shape only; NOT imported KiCad / no netlist','pcb')
for n,key,mat in [('BatteryEnvelope','battery','battery'),('ComputeZero2WEnvelope','compute','pcb'),('CameraModuleEnvelope','camera','chip'),('DisplayModuleEnvelope','display','screen')]:finish(box(n,p[key]['size'],p[key]['position']),mat,'verified XY where stated; maximum envelope; exact connectors pending')
# Glass rear and perimeter tape with central optical air gap (not OCA full lamination).
glass=finish(rounded('DisplayCoverGlass',33.5,41,.7,3,[21,29,.25]),'glass','cover glass placeholder; rear z=.25..95mm','glass')
ring=cut('DisplayPerimeterTape',rounded('TapeOuter',33.5,41,.2,3,[21,29,.95]),rounded('TapeInner',29.5,35,.4,2,[23,32,.85]));finish(ring,'adhesive','perimeter tape; custom die cut, not full optical bonding','seal')
finish(cyl('CameraCoverGlass',7.8,.7,[55.5,55,33.1]),'glass','optical window material/AR coating pending','glass')
finish(cut('CameraBondRing',cyl('CameraTapeOD',7.8,.2,[55.5,55,32.9]),cyl('CameraTapeID',6.2,.4,[55.5,55,32.8])),'adhesive','window bond ring; needs supporting ledge','seal')
# Actual optical barrel indicated inside module envelope; reference feature excluded from collision list.
barrel=cyl('REFERENCE_LensBarrel',5.5,8,[55.5,55,22.5]);meta[barrel.Name]={'material':'lens','status':'visual aid inside reserved camera envelope','group':'reference'}
# GNSS: chip + dedicated antenna ground board + ceramic patch. Ground is intentional, not a zero-metal keepout.
finish(box('GNSS_LC76G',[9.7,10.1,2.4],[45,80,19]),'chip','LC76G module envelope; selected variant and footprint not frozen')
finish(box('GNSSGroundBoard',[24,24,1],[43,78,25.5]),'pcb','antenna ground reference placeholder; actual required dimensions unknown')
finish(box('GNSSPatchReservation',p['gnss_patch']['size'],p['gnss_patch']['position']),'ceramic',p['gnss_patch']['status'])
# Clear area above compute module upper end for WiFi/BT; direction of real onboard antenna unresolved.
radio=box('REFERENCE_WiFiBT_RFZone',[31,27,12],[4,72,21]);meta[radio.Name]={'material':'rf','status':'conservative study zone; not chip supplier keepout','group':'reference'}
# Board-level functions outside large modules. No invented commercial MPNs.
for n,s,pos,mat,st in [
 ('FPGA_iCE40UP5K',[7,7,1],[39,27,17.6],'chip','QFN48 body envelope; support parts reserved separately'),
 ('IMU_BMI270',[2.5,3,.8],[39,40,17.6],'chip','14-LGA vendor dimensions; interrupts and axis orientation pending'),
 ('PowerPathReserved',[15,10,3],[49,14,17.6],'chip','UNSELECTED charger/boost/protection group'),
 ('AlwaysOnControllerReserved',[5,5,1],[39,18,17.6],'chip','UNSELECTED wake/NTC/rail-control device'),
 ('FuelGaugeReserved',[3,3,1],[42,36,17.6],'chip','UNSELECTED gauge with I2C'),
 ('ClockConfigReserved',[6,5,1.5],[49,28,17.6],'chip','FPGA oscillator/configuration envelope'),
 ('SpeakerEnclosure',[18,12,4],[44,80,4],'polymer','UNSELECTED speaker plus acoustic chamber'),
 ('USBChargeConnector',[11,11,4.5],[32.5,1.5,8],'steel','UNSELECTED actual port/support board; grommet pending'),
 ('ScreenFPCVertical',[.2,5,10],[18.5,34,5],'fpc','routing corridor only; no bend radius proof'),
 ('ScreenFPCFlat',[3.5,5,.2],[18.5,34,4.8],'fpc','routing corridor only'),
 ('CameraFPCCorridor',[.2,17,6],[40.5,46,19],'fpc','routing corridor only; endpoints not connected'),
 ('ThermalBridge',[18,15,6.7],[12,28,24],'aluminum','rigid thermal bridge; intentional top contact'),
 ('ThermalPad',[18,15,1.8],[12,28,30.7],'thermal','compressed pad target; touches front inside surface'),
 ]:finish(box(n,s,pos),mat,st)
finish(cyl('HapticMotor',5,3,[11.5,53,4]),'steel','UNSELECTED ERM motor; mount isolation pending')
for i,(x,y) in enumerate([(7,64),(70.5,64),(9,91),(68,91)]):
 finish(box('Mic'+str(i),[4,3,1.2],[x-2,y-1.5,29.9]),'chip','PDM body placeholder; daughterboard and wiring OPEN')
 finish(cut('MicGasket'+str(i),cyl('MicGasketOD'+str(i),2.5,1.2,[x,y,31.1]),cyl('MicGasketID'+str(i),.65,1.5,[x,y,31])),'gasket','acoustic isolation tube placeholder')
 finish(cyl('MicMembrane'+str(i),2,.1,[x,y,32.3]),'membrane','UNSELECTED acoustic membrane; insertion loss/IP untested')
for i,y in enumerate([61,66]):finish(box('LightPipe'+str(i),[11.6,1.2,2.4],[18.2,y+.2,31.5]),'red' if i==0 else 'amber','separate microphone/camera status lightpipe','external')
for i,y in enumerate([25,39]):finish(box('SideButton'+str(i),[2.1,9,4],[74.1,y+.5,20.5]),'polymer','button cap; switch travel and seal OPEN','external')
finish(box('PrivacySlider',[2.2,11,4],[-.2,33.5,20.5]),'red','physical permission switch actuator; internal switch not selected','external')
# Reference old PCB imported as a separate hidden comparison, NOT claimed to match R2.
oldpath=R.parent/'MeetNote-R0/mechanical/carrier_from_kicad.step'
if oldpath.exists():
 old=Part.read(str(oldpath));bb=old.BoundBox
 if bb.YMin<-.1:old.rotate(A.Vector(0,0,0),A.Vector(1,0,0),180)
 bb=old.BoundBox;old.translate(A.Vector(3-bb.XMin,10-bb.YMin,16-bb.ZMin));ref=d.addObject('PartDesign::Feature','REFERENCE_R0_PCB_STEP');ref.Shape=old;ref.addProperty('App::PropertyString','Evidence').Evidence='actual imported R0 board; excluded from R2 assembly; pads/components incompatible'
d.recompute()
# Remove stale intermediate metadata; pairwise positive-volume intersections are reported.
manifest=[]
for o in final:
 if o.Shape.isNull() or not o.Shape.isValid():raise RuntimeError('invalid '+o.Name)
 Mesh.export([o],str(M/'meshes'/(o.Name+'.stl')))
 manifest.append({'name':o.Name,'label':o.Label,'mesh':'meshes/'+o.Name+'.stl',**meta[o.Name]})
inter=[]
for i,a in enumerate(final):
 for b in final[i+1:]:
  v=a.Shape.common(b.Shape).Volume
  if v>.01:inter.append({'a':a.Name,'b':b.Name,'volume_mm3':round(v,3),'status':'REVIEW_REQUIRED'})
# RF volume checks allow GNSS intended ground but flag enclosure intrusion into WiFi reserved volume.
rfchecks=[]
for a in final:
 if meta[a.Name]['material'] in ['aluminum','steel'] or a.Name in ['BatteryEnvelope','ThermalPad']:
  v=a.Shape.common(radio.Shape).Volume
  if v>.01:rfchecks.append({'part':a.Name,'overlap_mm3':round(v,3)})
mass={}
dens={'aluminum':.0027,'polymer':.0012,'steel':.0078,'glass':.0025,'gasket':.0011,'adhesive':.001,'thermal':.002,'membrane':.001}
for o in final:
 if meta[o.Name]['group'] in ['shell','seal','glass','fastener','external'] and meta[o.Name]['material'] in dens:mass[o.Name]=round(o.Shape.Volume*dens[meta[o.Name]['material']],2)
report={'version':A.Version(),'parts':len(final),'all_final_solids_valid':True,'positive_volume_intersections':inter,'RF_zone_metal_conflicts':rfchecks,'mass_modeled_shell_seals_fasteners_g':mass,'modeled_partial_mass_g':round(sum(mass.values()),2),'nominal_body_mm':[W,L,H],'external_strap_lug_total_height_mm':108,'battery_swelling_to_PCB_mm':16-(6.8+7.3+1),'battery_to_display_mm':6.8-(2.1+4),'manufacturing_status':'BLOCKED - packaging study, no R2 ECAD integration, unknown supplier envelopes/adhesives/RF/thermal','R0_PCB_imported':oldpath.exists(),'R0_PCB_used_as_R2_board':False}
(V/'mechanical_checks.json').write_text(json.dumps(report,indent=2))
(M/'scene_manifest.json').write_text(json.dumps(manifest,indent=2));Part.export(final,str(M/'MeetNote_R2_assembly.step'))
for name,obj in [('metal_frame',metal),('rf_cap',rf),('rear_cover',back)]:Part.export([obj],str(M/(name+'.step')));Mesh.export([obj],str(M/(name+'.stl')))
d.recompute();d.saveAs(str(M/'MeetNote_R2.FCStd'));print(json.dumps(report,indent=2))
