"""Run with Python 3; retain every actual tool return code."""
import subprocess,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'electronics';V=R/'verification';F=E/'NOT_FOR_FAB';F.mkdir(exist_ok=True)
(F/'READ_ME_DO_NOT_FABRICATE.txt').write_text('R0 NOT FOR FABRICATION\nUnrouted board; incomplete power and privacy circuits; unverified parts; DRC/ERC fail.\nThese exports verify export workflow only. DO NOT ORDER PCBS OR ASSEMBLY.\n')
b=str(E/'MeetNote.kicad_pcb');s=str(E/'MeetNote.kicad_sch')
tasks=[('erc',['sch','erc','--format','json','--exit-code-violations','-o',str(V/'erc.json'),s]),('drc',['pcb','drc','--format','json','--schematic-parity','--exit-code-violations','-o',str(V/'drc.json'),b]),('schematic_pdf',['sch','export','pdf','-o',str(E/'schematic.pdf'),s]),('bom_native',['sch','export','bom','-o',str(E/'BOM_native.csv'),s]),('gerber',['pcb','export','gerbers','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts','-o',str(F)+'/',b]),('drill',['pcb','export','drill','--format','excellon','--excellon-separate-th','--generate-map','--generate-report','--report-path',str(F/'drill_report.txt'),'-o',str(F)+'/',b]),('positions',['pcb','export','pos','--format','csv','--units','mm','-o',str(F/'placement.csv'),b]),('pcb_step',['pcb','export','step','--force','--board-only','--user-origin','0x0mm','-o',str(R/'mechanical/carrier_from_kicad.step'),b])]
log=[]
for name,args in tasks:
 p=subprocess.run(['kicad-cli']+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(V/(name+'_command.log')).write_text(p.stdout);log.append({'check':name,'command':['kicad-cli']+args,'return_code':p.returncode});print(name,p.returncode)
(V/'tool_runs.json').write_text(json.dumps(log,indent=2))
