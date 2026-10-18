"""Run with KiCad bundled Python. Generates R0 drafts; never fabrication release."""
from pathlib import Path
import re,json,uuid,copy,csv
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'electronics'; E.mkdir(exist_ok=True)
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
def uid():return str(uuid.uuid4())
def parse(s):
 stack=[[]]
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s):
  if t=='(': a=[];stack[-1].append(a);stack.append(a)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 return stack[0][0]
def items(s,k):return [x for x in s if isinstance(x,list) and x and x[0]==k]
def get(s,k,d=None):return next(iter(items(s,k)),d)
def emit(x):
 if isinstance(x,list):return '('+' '.join(emit(i) for i in x)+')'
 # quote all string tokens except keyword-like atoms/numbers; library S-expr distinguishes strings only at value positions,
 # so use original source extraction for library below
 return str(x)
def sx(x):
 if isinstance(x,list):return '('+str(x[0])+(' '+' '.join(sx(i) for i in x[1:]) if len(x)>1 else '')+')'
 return json.dumps(str(x),ensure_ascii=False)
# serializer must keep numeric/boolean tokens bare
ATOM={'yes','no','input','output','bidirectional','tri_state','passive','power_in','power_out','open_collector','open_emitter','free','unspecified','line','inverted','clock','inverted_clock','input_low','clock_low','output_low','edge_clock_high','non_logic','solid','default','background','none','left','right','top','bottom','hide'}
def ser(x):
 if isinstance(x,list):
  return '('+str(x[0])+(' '+' '.join(json.dumps(str(i)) if not isinstance(i,list) and (x[0] in {'number','name','symbol','property','description','datasheet'} ) else ser(i) for i in x[1:]) if len(x)>1 else '')+')'
 s=str(x)
 return s if re.fullmatch(r'-?\d+(\.\d+)?',s) or s in ATOM else json.dumps(s,ensure_ascii=False)
cache={}
def symbol(lib,n):
 if lib not in cache:cache[lib]=parse((LIB/'symbols'/(lib+'.kicad_sym')).read_text())
 tree=cache[lib]; s=copy.deepcopy(next(x for x in items(tree,'symbol') if x[1]==n))
 ex=get(s,'extends')
 if ex:
  base=symbol(lib,ex[1]); old=base[1].split(':')[-1]
  s.remove(ex)
  for sub in items(base,'symbol'):
   sub=copy.deepcopy(sub);sub[1]=sub[1].replace(old+'_',n+'_');s.append(sub)
  if not get(s,'pin_names') and get(base,'pin_names'):s.append(copy.deepcopy(get(base,'pin_names')))
 s[1]='MeetNote:'+n
 return s
symbols={};components=[];rootid=uid(); sheets={n:uid() for n in ['power','compute','fpga','camera','audio','wireless','ui_debug']}
def symadd(lib,n):
 key=n
 if key not in symbols:symbols[key]=symbol(lib,n)
 return key

def block(n,pins):
 # Deliberately interface contracts, not fabricated package pinouts.
 h=max(10.16,(len(pins)+1)*2.54/2)
 text=f'''(symbol "MeetNote:{n}" (pin_names (offset 0.508)) (in_bom yes) (on_board no)
(property "Reference" "U" (at 0 {h+2} 0) (effects (font (size 1.27 1.27))))
(property "Value" "{n}" (at 0 {-h-2} 0) (effects (font (size 1.27 1.27))))
(symbol "{n}_0_1" (rectangle (start -16 {h}) (end 16 {-h}) (stroke (width 0.254) (type default)) (fill (type background))))
(symbol "{n}_1_1"'''
 for i,(name,typ) in enumerate(pins):
  y=h-2.54-i*2.54
  text+=f'(pin {typ} line (at -20.32 {y} 0) (length 5.08) (name "{name}" (effects (font (size 1 1)))) (number "{i+1}" (effects (font (size 1 1)))))'
 text+='))';symbols[n]=parse(text);return n

def add(sheet,key,ref,value,x,y,nets,fp='',pos=None,unit=1,note='Library geometry; manufacturer pin review pending'):
 c=dict(sheet=sheet,key=key,ref=ref,value=value,x=x,y=y,nets={str(k):v for k,v in nets.items()},fp=fp,pos=pos,unit=unit,uuid=uid(),note=note);components.append(c);return c
R=symadd('Device','R');C=symadd('Device','C');LED=symadd('Device','LED');MIC=symadd('Sensor_Audio','IM69D130');FPGA=symadd('FPGA_Lattice','ICE40UP5K-SG48ITR')
CON=symadd('Connector_Generic','Conn_02x20_Odd_Even');CON2=symadd('Connector_Generic','Conn_01x02');CON4=symadd('Connector_Generic','Conn_01x04');SW=symadd('Switch','SW_Push')
r_fp='Resistor_SMD:R_0603_1608Metric'; c_fp='Capacitor_SMD:C_0603_1608Metric'
# Power is an explicit unresolved subsystem: no made-up charging/regulator pin map.
pwr=block('UNVERIFIED_POWER_ASSEMBLY',[(n,t) for n,t in [('VBUS_5V','power_in'),('BAT_P','power_in'),('NTC_CELL','input'),('GND','power_in'),('SYS_5V','power_out'),('V3V3','power_out'),('V1V2','power_out'),('V2V5','power_out'),('MIC_CAPTURE_VDD','power_out'),('REC_PERMIT','input'),('CAM_PERMIT','input'),('LOW_BAT','output')]])
add('power',pwr,'U10','UNVERIFIED BQ24074 + boost + rails + gating',90,80,{i:n for i,n in enumerate(['VBUS_5V','BAT_P','NTC_CELL','GND','SYS_5V','V3V3','V1V2','V2V5','MIC_CAPTURE_VDD','REC_PERMIT','CAM_PERMIT','LOW_BAT'],1)},note='BLOCKER: power design, USB-C CC detection, thermistor and hard gates not implemented')
for ref,val,xy,ns,pos in [('J2','BATTERY 1S', (160,50),{1:'BAT_P',2:'GND'},(58,15)),('J3','REGULATED 5V IN',(160,80),{1:'SYS_5V',2:'GND'},(58,24)),('J4','CELL NTC',(160,110),{1:'NTC_CELL',2:'GND'},(50,10))]:
 add('power',CON2,ref,val,*xy,ns,'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',pos,note='Provisional 2.54mm engineering header; NOT approved battery connector')
pi={1:'V3V3',2:'SYS_5V',3:'I2C_SDA',4:'SYS_5V',5:'I2C_SCL',6:'GND',7:'FPGA_IRQ',8:'UART_TX',9:'GND',10:'UART_RX',11:'REC_BUTTON',12:'FPGA_RESET',13:'CAM_BUTTON',14:'GND',15:'ZOOM_PLUS',16:'ZOOM_MINUS',17:'V3V3',18:'UPLOAD_LED_CTL',19:'SPI_MOSI',20:'GND',21:'SPI_MISO',22:'FPGA_DONE',23:'SPI_SCK',24:'SPI_CS',25:'GND',26:'CAM_PERMIT',27:None,28:None,29:'REC_PERMIT',30:'GND',31:'LOW_BAT',32:'ERROR_LED_CTL',33:None,34:'GND',35:None,36:None,37:None,38:None,39:'GND',40:None}
add('compute',CON,'J1','Zero 2 W GPIO via short harness',95,90,pi,'Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical',(15,10),note='GPIO physical numbering; harness length and final connector height TBD; not direct stacked HAT')
fpins={1:'V3V3',5:'V1V2',30:'V1V2',29:'V1V2_PLL',24:'V2V5',22:'V3V3',33:'V3V3',49:'GND',7:'FPGA_DONE',8:'FPGA_RESET',14:'SPI_MISO',15:'SPI_SCK',16:'SPI_CS',17:'SPI_MOSI',23:'PDM_D1',25:'PDM_D2',26:'PDM_D3',27:'PDM_D4',28:'PDM_CLK',31:'FPGA_IRQ',35:'AUDIO_MCLK'}
for u,x,y in [(1,65,75),(2,150,75),(3,65,160),(4,150,160)]:add('fpga',FPGA,'U1','ICE40UP5K-SG48ITR',x,y,fpins,'Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm',(34,22),u)
# clock source is placeholder until exact 3.3V 12.288MHz XO selected
clk=block('UNVERIFIED_12M288_XO',[('VDD','power_in'),('GND','power_in'),('OUT','output')]);add('fpga',clk,'Y1','UNVERIFIED 12.288MHz XO',235,65,{1:'V3V3',2:'GND',3:'AUDIO_MCLK'},note='BLOCKER: order code, jitter, supply and footprint not verified')
add('fpga',R,'R1','100R PLL filter provisional',225,115,{1:'V1V2',2:'V1V2_PLL'},r_fp,(40,18))
for i,net in enumerate(['V1V2','V1V2_PLL','V2V5','V3V3']):add('fpga',C,f'C{i+1}','100nF 10V',210+i*18,155,{1:net,2:'GND'},c_fp,(27+i*5,30))
for i,(net,val,pos) in enumerate([('FPGA_RESET','10k',(28,16)),('FPGA_DONE','10k',(35,16))],2):add('fpga',R,f'R{i}',val,215+(i-2)*25,95,{1:'V3V3',2:net},r_fp,pos)
for i,(x,y,pos) in enumerate([(65,65,(4,4)),(160,65,(66,4)),(65,135,(4,66)),(160,135,(66,66))],1):
 add('audio',MIC,f'MK{i}','IM69D130',x,y,{1:f'PDM_D{i}',2:'MIC_CAPTURE_VDD',3:'PDM_CLK',4:'GND',5:'GND'},'Sensor_Audio:Infineon_PG-LLGA-5-1',pos)
 add('audio',C,f'C{i+4}','100nF 10V',x+35,y,{1:'MIC_CAPTURE_VDD',2:'GND'},c_fp,(pos[0]+(4 if pos[0]<35 else -4),pos[1]))
cam=block('EXTERNAL_CAMERA_CSI',[('CSI_P/N','passive'),('CTRL_I2C','bidirectional'),('HARD_PERMIT','input'),('STATUS_SENSE','output')]);add('camera',cam,'A2','Camera Module 3 Standard external FPC',95,70,{1:'CSI_DIRECT_EXTERNAL',2:'CAM_I2C_EXTERNAL',3:'CAM_PERMIT',4:'CAM_HW_ON'},note='External Zero CSI connection; not routed on carrier. Hard power isolation/interposer unresolved')
radio=block('EMBEDDED_WIFI_BLE',[('INTERNAL_BUS','passive')]);add('wireless',radio,'A3','Zero 2 W onboard Wi-Fi BLE',95,70,{1:'RADIO_INTERNAL'},note='Already inside Zero; no second purchased module')
# UI switches are provisional footprints, resistor/LED loops have actual nets.
for i,(name,pos) in enumerate([('REC_BUTTON',(25,61)),('CAM_BUTTON',(36,61)),('ZOOM_PLUS',(47,61)),('ZOOM_MINUS',(58,61))],1):
 add('ui_debug',SW,f'SW{i}',name,40+i*40,60,{1:name,2:'GND'},'Button_Switch_SMD:SW_SPST_TL3342',pos,note='Switch MPN/force/travel not supplier-verified')
 forkey=None
for i,(name,pos) in enumerate([('REC_HW_ON',(25,44)),('CAM_HW_ON',(25,52)),('UPLOAD_LED_CTL',(25,36))],1):
 add('ui_debug',LED,f'D{i}',['RED MIC POWER','AMBER CAMERA POWER','BLUE UPLOAD'][i-1],60+i*48,112,{1:'GND',2:f'LED{i}_A'},'LED_SMD:LED_0603_1608Metric',pos,note='Color/current MPN TBD; REC/CAM driven by hardware sensed rail, not software')
 add('ui_debug',R,f'R{i+3}','1k provisional',60+i*48,92,{1:name,2:f'LED{i}_A'},r_fp,(pos[0],pos[1]-4))
permit=block('UNVERIFIED_HARD_INTERLOCK',[('VDD','power_in'),('GND','power_in'),('REC_PERMIT','output'),('CAM_PERMIT','output'),('REC_HW_ON','output')]);add('ui_debug',permit,'SW5','UNVERIFIED dual-pole consent switch + gates',65,155,{1:'V3V3',2:'GND',3:'REC_PERMIT',4:'CAM_PERMIT',5:'REC_HW_ON'},note='BLOCKER: independent physical camera/microphone enable + anti-backfeed design incomplete')
add('ui_debug',CON4,'J5','UART 3V3 debug',160,160,{1:'GND',2:'UART_TX',3:'UART_RX',4:'V3V3'},'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',(44,14))

# Native hierarchical schematics
names={'power':'01 POWER - UNRESOLVED','compute':'02 COMPUTE AND STORAGE','fpga':'03 FPGA AUDIO FRONT END','camera':'04 CAMERA - EXTERNAL','audio':'05 FOUR MICROPHONES','wireless':'06 WIRELESS - EMBEDDED','ui_debug':'07 UI AND DEBUG'}
def prop(n,v,x,y,hide=False):return f'(property {json.dumps(n)} {json.dumps(v)} (at {x} {y} 0) (effects (font (size 1.1 1.1))'+(' hide' if hide else '')+'))'
def note(t,x,y,size=1.5):return f'(text {json.dumps(t)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid()}))'
def begin(id,title,libs=''):
 return f'(kicad_sch (version 20251024) (generator "eeschema") (uuid {id}) (paper "A4") (title_block (title {json.dumps(title)}) (rev "R0-NOT-FOR-FAB") (comment 1 "UNROUTED DRAFT - ALL BLOCKERS MUST BE CLOSED")) (lib_symbols {libs})'
root=begin(rootid,'MeetNote R0 - Engineering draft')+note('R0 ENGINEERING DRAFT / NOT FOR FABRICATION',25,20,2)
for i,(name,sid) in enumerate(sheets.items()):
 x=25+(i%3)*85;y=45+(i//3)*45
 root+=f'(sheet (at {x} {y}) (size 70 30) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid {sid})'+prop('Sheetname',names[name],x,y-2)+prop('Sheetfile',name+'.kicad_sch',x,y+32)+f'(instances (project "MeetNote" (path "/{rootid}" (page "{i+2}")))))'
root+=f'(sheet_instances (path "/" (page "1"))))';(E/'MeetNote.kicad_sch').write_text(root)
for name,sid in sheets.items():
 cs=[c for c in components if c['sheet']==name];keys=list(dict.fromkeys(c['key'] for c in cs));out=begin(uid(),names[name],' '.join(ser(symbols[k]) for k in keys))
 out+=note('INTERFACE AND PIN DRAFT: see docs/03_ECAD_constraints.md',20,15)
 seenpins=set()
 for c in cs:
  key=c['key'];x,y=[round(round(v/1.27)*1.27,4) for v in (c['x'],c['y'])];s=symbols[key];u=c['unit'];ref=c['ref'];cid=c['uuid']
  out+=f'(symbol (lib_id "MeetNote:{key}") (at {x} {y} 0) (unit {u}) (in_bom yes) (on_board '+('yes' if c['fp'] else 'no')+f') (dnp no) (uuid {cid})'
  out+=prop('Reference',ref,x,y-35)+prop('Value',c['value'],x,y+5,True)+prop('Footprint',c['fp'],x,y,True)+prop('Review',c['note'],x,y,True)
  out+=f'(instances (project "MeetNote" (path "/{rootid}/{sid}" (reference "{ref}") (unit {u})))))'
  for sub in items(s,'symbol'):
   if not (sub[1].endswith(f'_{u}_1') or sub[1].endswith(f'_{u}_0') or sub[1].endswith('_0_1')):continue
   for p in items(sub,'pin'):
    num=get(p,'number')[1];a=get(p,'at');px=round(x+float(a[1]),4);py=round(y-float(a[2]),4);point=(px,py)
    if point in seenpins:continue
    seenpins.add(point);net=c['nets'].get(num)
    if not net:out+=f'(no_connect (at {px} {py}) (uuid {uid()}))';continue
    # short lead directed outward based on pin angle
    ang=int(float(a[3]));dx,dy={0:(-5.08,0),180:(5.08,0),270:(0,-5.08),90:(0,5.08)}[ang];ex=round(px+dx,4);ey=round(py+dy,4)
    out+=f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {uid()}))'
    out+=f'(global_label "{net}" (shape bidirectional) (at {ex} {ey} {180 if ang==0 else 0}) (effects (font (size 1 1)) (justify {"right" if ang==0 else "left"})) (uuid {uid()}))'
 out+=')';(E/(name+'.kicad_sch')).write_text(out)
(E/'MeetNote.kicad_sym').write_text('(kicad_symbol_lib (version 20251024) (generator "kicad_symbol_editor") '+' '.join(ser([s[0],s[1].split(':')[-1]]+s[2:]) for s in symbols.values())+')')
(E/'sym-lib-table').write_text('(sym_lib_table (lib (name "MeetNote") (type "KiCad") (uri "${KIPRJMOD}/MeetNote.kicad_sym") (options "") (descr "Self contained R0 library")))')
(E/'MeetNote.kicad_pro').write_text(json.dumps({'meta':{'filename':'MeetNote.kicad_pro','version':3},'board':{'design_settings':{'rules':{'min_clearance':0.15,'min_track_width':0.2,'min_via_diameter':0.6,'min_through_hole_diameter':0.3}}},'net_settings':{'classes':[{'name':'Default','clearance':0.2,'track_width':0.25,'via_diameter':0.6,'via_drill':0.3,'diff_pair_width':0.2,'diff_pair_gap':0.2,'diff_pair_via_gap':0.25}]},'erc':{'erc_exclusions':[]}},indent=2))
# Actual pads and assigned nets, intentionally no invented autorouting.
b=pcb.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.6))
nets={}
for c in components:
 if not c['fp']:continue
 for name in c['nets'].values():
  if name and name not in nets:
   net=pcb.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
for p,q in list(zip([(3,0),(67,0),(70,3),(70,67),(67,70),(3,70),(0,67),(0,3)],[(67,0),(70,3),(70,67),(67,70),(3,70),(0,67),(0,3),(3,0)])):
 s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in p]));s.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in q]));s.SetLayer(pcb.Edge_Cuts);s.SetWidth(pcb.FromMM(.05));b.Add(s)
fpdir=E/'MeetNote.pretty';fpdir.mkdir(exist_ok=True);seen=set();manifest=[]
for c in components:
 if not c['fp'] or c['ref'] in seen:continue
 seen.add(c['ref']);lib,n=c['fp'].split(':');src=LIB/'footprints'/(lib+'.pretty')/(n+'.kicad_mod');(fpdir/(n+'.kicad_mod')).write_text(src.read_text())
 f=pcb.FootprintLoad(str(fpdir),n);f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPID(pcb.LIB_ID('MeetNote',n));f.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(v) for v in c['pos']]))
 f.SetPath(pcb.KIID_PATH('/'+rootid+'/'+sheets[c['sheet']]+'/'+c['uuid']))
 for pad in f.Pads():
  net=c['nets'].get(pad.GetNumber())
  if net:pad.SetNet(nets[net])
 b.Add(f);manifest.append({'reference':c['ref'],'value':c['value'],'x':c['pos'][0],'y':c['pos'][1],'footprint':n,'height_estimate_mm':8 if c['ref'].startswith('J') else (1.2 if c['ref'].startswith('MK') else 2),'body_model':'not supplier verified'})
 # Match portable footprint identifiers in schematic
for path in list(E.glob('*.kicad_sch'))+[E/'MeetNote.kicad_sym']:
 t=path.read_text()
 for c in components:
  if c['fp']:t=t.replace('"'+c['fp']+'"','"MeetNote:'+c['fp'].split(':')[1]+'"')
 path.write_text(t)
for i,(x,y) in enumerate([(3,10),(67,10),(3,60),(67,60)],1):
 f=pcb.FootprintLoad(str(LIB/'footprints/MountingHole.pretty'),'MountingHole_2.2mm_M2');f.SetReference('H'+str(i));f.SetAttributes(f.GetAttributes()|pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES);f.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));b.Add(f)
t=pcb.PCB_TEXT(b);t.SetText('MEETNOTE R0 - DO NOT FABRICATE');t.SetPosition(pcb.VECTOR2I(pcb.FromMM(35),pcb.FromMM(37)));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(1),pcb.FromMM(1)));t.SetLayer(pcb.B_SilkS);t.SetMirrored(True);b.Add(t)
pcb.SaveBoard(str(E/'MeetNote.kicad_pcb'),b)
(E/'fp-lib-table').write_text('(fp_lib_table (lib (name "MeetNote") (type "KiCad") (uri "${KIPRJMOD}/MeetNote.pretty") (options "") (descr "R0 copied standard footprints; unverified MPNs")))')
(E/'placement_manifest.json').write_text(json.dumps(manifest,indent=2))
(E/'design_components.json').write_text(json.dumps(components,indent=2))
with (E/'BOM_engineering.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Status','Review']);seen=set()
 for c in components:
  if c['ref'] in seen:continue
  seen.add(c['ref']);w.writerow([c['ref'],c['value'],c['fp'],'DRAFT_NOT_FOR_PURCHASE',c['note']])
print('Generated',len(seen),'references,',len(b.GetFootprints()),'footprints,',len(nets),'nets; routing intentionally incomplete')
