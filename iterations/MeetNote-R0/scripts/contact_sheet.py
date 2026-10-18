from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'visuals';canvas=Image.new('RGB',(1800,2040),'#101c29');d=ImageDraw.Draw(canvas)
f='/System/Library/Fonts/STHeiti Medium.ttc';font=ImageFont.truetype(f,42);small=ImageFont.truetype(f,24)
d.text((52,30),'MeetNote R0  |  82 × 118 × 29 mm',font=font,fill='#edf4f6');d.text((52,92),'机械尺寸驱动的工程展示 · 未通过投板放行 · 尚无实物测试',font=small,fill='#f0b46f')
views=[('01_front.png','正面 / 录制状态'),('02_back.png','背面 / 接口与开孔'),('03_section.png','剖视 / 已建模零件包络'),('04_hand_scale.png','手持比例 / 示意手型，非人体工学验证')]
for i,(n,title) in enumerate(views):
 x=(i%2)*900;y=145+(i//2)*920;im=Image.open(r/n).convert('RGB').resize((872,872));canvas.paste(im,(x+14,y));d.text((x+30,y+875),title,font=small,fill='#dbe7ed')
d.text((40,2000),'外壳、PCB、电池和镜头比例统一；线束、真实器件STEP、公差及射频/热验证仍待完成。',font=small,fill='#c0cbd3');canvas.save(r/'overview.png')
