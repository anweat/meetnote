import json,csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=[
('电子','计算板（含RAM、Wi-Fi/蓝牙）','Zero 2 W参考',120,200,'原厂$15参考价；人民币为零售到手预算，不是报价'),
('电子','自动对焦相机与Zero适配排线','Camera Module 3 Standard参考',180,260,'原厂起价$25；原配排线不兼容Zero，另计适配线'),
('电子','1.69英寸彩屏','ST7789V2现成模组参考',60,100,'厂商搜索页单件$9.49；国内库存价未核'),
('电子','FPGA与配置/时钟/增量电源','iCE40UP5K-SG48候选',80,160,'设计估算，非开发板价格；RTL/电路未完成'),
('电子','四麦与音频外围','IM69D130候选',40,90,'设计估算；声学膜/胶圈列在结构项'),
('电子','GNSS接收器及备份电源外围','LC76G系列候选，型号后缀待定',70,140,'设计估算；厂商$14.99开发模块仅作对照，板尺寸不可代入裸模组'),
('电子','GNSS天线、馈线及匹配件','18×18×4包络占位',25,60,'未选型/未报价；与上项分开，若买含天线套件须去重'),
('电子','六轴IMU与外围','BMI270候选',15,45,'设计估算；DFRobot BMI160整板49元是替代台架参考，不是BMI270报价'),
('电子','32GB存储','高耐久microSD待选',25,50,'设计估算'),
('电子','充电/电源路径/升压/电量计/保护','待选型',80,160,'设计估算；小批最低采购与备用件可能增加现金支出'),
('电子','带保护和温度检测电池','2500mAh候选',40,80,'设计估算；放电能力与公差待证据'),
('电子','扬声器/功放/振动','待选型',30,65,'设计估算'),
('电子','连接器/排线/按键/灯/小阻容','待选型',50,100,'设计估算，不含焊接人工'),
('电子','低功耗管理/唤醒/传感器接口','待选型',30,60,'设计估算；不能把Linux软件睡眠当硬断电'),
('制造','PCB最小批次现金支出','4层常规工艺候选',80,200,'即使只装1台也按整批付款；不假设优惠券/免费打样'),
('制造','钢网/焊接/检查','手工返修或小批贴装',300,800,'工厂最低费用/人工预留；无正式SMT报价'),
('结构','CNC铝中框含常规表面处理','6061候选',450,1200,'单件复杂度估算；不是嘉立创已报价'),
('结构','非金属天线帽与后盖','树脂/尼龙打印或简易加工',80,200,'单台研究件；最终PC材料另核'),
('结构','屏幕/镜头保护片与切割','玻璃或透明塑料候选',80,200,'周边贴合；不包含定制OCA光学全贴合'),
('结构','密封圈/胶/膜/导热垫','小包材采购',80,180,'含试装损耗的估算；无IP验证'),
('结构','紧固件/挂绳/小固定件','标准件候选',20,60,'估算'),
('其他','多批运费/耗材','预留',50,120,'估算')]
with (R/'单台成本明细.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['类别','项目','候选路线','低预算元','高预算元','证据与口径']);w.writerows(rows)
groups={}
for cat,_,_,lo,hi,_ in rows:
 groups.setdefault(cat,[0,0]);groups[cat][0]+=lo;groups[cat][1]+=hi
base=[sum(x[3] for x in rows),sum(x[4] for x in rows)]
r={'currency':'CNY','quantity':'1 assembled unit; minimum purchasing batches paid in full','not_a_quote':True,'groups':groups,'first_build_range':base,'with_25_percent_rework_reserve':[round(v*1.25) for v in base],'excludes':['engineering labor and firmware development','test instruments','cloud recurring fees','certification','injection mold','custom optical full lamination'], 'thermal_extra_W_assumptions':{'gnss_full_module_and_antenna':.18,'imu_and_always_on':.025},'recording_total_W_with_GNSS':2.805,'runtime_2500mAh_h':5.8608/2.805}
(R/'verification/cost_and_power.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
