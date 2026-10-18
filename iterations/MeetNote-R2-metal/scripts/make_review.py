from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,csv,html
R=Path(__file__).resolve().parents[1];V=R/'visuals'
font='/System/Library/Fonts/STHeiti Medium.ttc';f=ImageFont.truetype(font,27);small=ImageFont.truetype(font,19)
out=Image.new('RGB',(1640,1830),'#eeeeea');draw=ImageDraw.Draw(out)
draw.text((40,22),'MEETNOTE R2 · 金属结构与内部布局研究',font=f,fill='#263e40')
draw.text((40,65),'主体 76×104×34 mm · 工程包络，未完成真实 PCB / RF / 热 / 密封验证',font=small,fill='#526466')
for i,(fn,title,desc) in enumerate([
 ('01_front.png','01 外侧 / 金属中框＋非金属天线帽','镜头、独立状态灯、侧键与USB开口'),
 ('02_back.png','02 后侧 / 屏幕周边贴合＋可拆盖','玻璃沉台、螺钉沉孔、双挂点'),
 ('03_section.png','03 剖视 / 保留实际内部坐标','显示、电池、主板、计算区、GNSS天线'),
 ('04_exploded.png','04 爆炸图 / 展示装配层次','仅本视图分离部件；原生模型保持装配坐标')]):
 x=30+(i%2)*810;y=112+(i//2)*843
 im=Image.open(V/fn).convert('RGB');im.thumbnail((780,780));out.paste(im,(x,y));draw.text((x,y+786),title,font=f,fill='#203b40');draw.text((x,y+820),desc,font=small,fill='#526466')
out.save(V/'overview.png')
rows=list(csv.DictReader((R/'单台成本明细.csv').open(encoding='utf-8-sig')))
tr=''.join('<tr>'+''.join('<td>'+html.escape(r[k])+'</td>' for k in ['类别','项目','低预算元','高预算元','证据与口径'])+'</tr>' for r in rows)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MeetNote R2 · 金属结构与单台成本</title><style>body{background:#efeee8;color:#20383b;font:16px/1.7 -apple-system,"PingFang SC",sans-serif;margin:0}main{max-width:1180px;margin:auto;padding:38px}h1{font-size:38px;line-height:1.25}h2{margin-top:38px;font-size:24px}img{width:100%;border-radius:12px}a{color:#216d62}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border-bottom:1px solid #cbd2cd;text-align:left}.warning{padding:18px;background:#eadfcc;border-left:4px solid #a27743}.scroll{overflow:auto}.muted{color:#607271}@media(max-width:700px){main{padding:20px}h1{font-size:28px}}</style><main><p class="muted">MEETNOTE / R2 / 2026.09.29</p><h1>金属外壳、局部贴合，<br>把传感器和装配空间一起算进去。</h1><p>已建立60个最终几何对象，含GNSS天线、IMU、屏幕盖板、胶层、螺钉和电池余量。主体76×104×34mm；整体研究估算155–190g。</p><p class="warning">这一版偏大、偏重，用于揭示单台样机的真实工程代价。几何检查无正体积相交，但并非已完成可制造装配；真实PCB、天线匹配、连接固定、排线与连续密封仍待完成。</p><img src="visuals/overview.png" alt="R2正面、背面、剖视和爆炸图，均由FreeCAD工程几何生成"><h2>金属与天线并存，胶用于合适的位置。</h2><p>金属前壳/中框承担结构与热扩散；顶部保留非金属天线帽，后盖可拆。屏幕和镜头保护片采用周边贴合，首件保留返修能力，不整腔灌封，也不宣称防水等级。</p><p>蓝牙沿用计算板已有能力；GNSS用于用户开启的位置记录；IMU可触发运动事件和亮屏，默认不自动启动录音或拍照。</p><h2>只做一台的费用预留</h2><p><b>首轮约1985–4530元；加25%返修余量约2480–5660元。</b>均为预算范围，尚无正式报价，不含研发工时、仪器、认证、云服务和定制光学全贴合。</p><div class="scroll"><table><tr><th>类别</th><th>项目</th><th>低预算/元</th><th>高预算/元</th><th>证据与口径</th></tr>'''+tr+'''</table></div><h2>工程文件</h2><p><a href="mechanical/MeetNote_R2.FCStd">FreeCAD源文件</a> · <a href="mechanical/MeetNote_R2_assembly.step">整体STEP</a> · <a href="visuals/MeetNote_R2.blend">Blender源文件</a> · <a href="单台成本明细.csv">完整成本CSV</a></p><p><a href="docs/设计说明与验证边界.md">设计与验证边界</a> · <a href="docs/单台成本说明.md">单台费用口径</a> · <a href="verification/mechanical_checks.json">几何检查</a></p><p class="muted">参数化方式：编辑parameters.json后运行生成脚本；FreeCAD保留原生可编辑布尔特征。Spreadsheet是参数快照，未全量关联驱动。R0 PCB STEP仅作隐藏参考，不是R2主板。</p></main></html>'''
(R/'review.html').write_text(page)
