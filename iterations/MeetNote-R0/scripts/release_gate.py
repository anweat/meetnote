"""A failing release gate is expected for this R0. Never suppress native violations."""
from pathlib import Path
import json,sys
r=Path(__file__).resolve().parents[1];e=json.loads((r/'verification/erc.json').read_text());d=json.loads((r/'verification/drc.json').read_text());m=json.loads((r/'verification/mechanical_fit.json').read_text());c=json.loads((r/'electronics/design_components.json').read_text())
errors=[v for s in e['sheets'] for v in s['violations'] if v['severity']=='error'];warnings=[v for s in e['sheets'] for v in s['violations'] if v['severity']=='warning']
report={'release_status':'BLOCKED_NOT_FOR_FAB','erc_errors':len(errors),'erc_warnings':len(warnings),'drc_violations':len(d['violations']),'unconnected_items':len(d['unconnected_items']),'schematic_parity_issues':len(d['schematic_parity']),'unresolved_interface_blocks':sorted({x['ref'] for x in c if 'UNVERIFIED' in x['key']}),'modeled_solid_intersections':len(m['solid_intersections']),'rf_keepout_violations':len(m['rf_keepout']),'physical_tests_performed':False,'physical_tests_required':['2h power and thermal at 35C','multichannel audio continuity and physical capture inhibit','assembled radio and whiteboard camera quality']}
(r/'verification/release_gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(2)
