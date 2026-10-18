"""Import exported native netlist into PCB, including explicit unused-pin nets."""
from pathlib import Path
import xml.etree.ElementTree as X
import pcbnew as p
R=Path(__file__).resolve().parents[1];E=R/'electronics';tree=X.parse(E/'netlist.xml');b=p.LoadBoard(str(E/'MeetNote.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByName().values()}
for n in tree.findall('./nets/net'):
 name=n.attrib['name']
 if name not in nets:
  net=p.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
 for node in n.findall('node'):
  f=fps.get(node.attrib['ref'])
  if f:
   for pad in f.Pads():
    if pad.GetNumber()==node.attrib['pin']:pad.SetNet(nets[name])
for c in tree.findall('./components/comp'):
 f=fps.get(c.attrib['ref'])
 if f:
  for fld in c.findall('./fields/field'):
   name=fld.attrib['name']
   if name in ['Footprint','Datasheet','Description']:continue
   f.SetField(name,fld.text or '');field=f.GetField(name);field.SetVisible(False);field.SetLayer(p.F_Fab);field.SetPosition(f.GetPosition())
p.SaveBoard(str(E/'MeetNote.kicad_pcb'),b)
print('Native netlist synchronized; no DRC exclusions added')
