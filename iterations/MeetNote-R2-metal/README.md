# MeetNote R2 · 金属壳、贴合与运动/定位设计研究

2026-09-29。R2延续可挂佩AI助手定位。状态：**机械空间研究，不可直接加工装配或投板**。原R0与R1均保留。

这次实际新增了原生FreeCAD布尔特征装配、60个最终几何对象、壳体/盖板/胶层/密封件/天线与电子包络、STEP/STL导出、Blender原生场景与四幅渲染，以及单台成本工作表。

## 文件入口

- `mechanical/MeetNote_R2.FCStd`：可编辑原生FreeCAD树。尺寸参数在`mechanical/parameters.json`，通过` scripts/build_mechanical.py`重建；文档内Spreadsheet为参数快照，**修改它不会自动驱动全部位置**。原生Box/Cylinder/Cut/Fuse可单独编辑。
- `mechanical/MeetNote_R2_assembly.step`：整体研究装配。
- `mechanical/metal_frame.step`、`rf_cap.step`、`rear_cover.step`：三件主要外壳，以及对应STL。加工前仍需补齐连接、拔刀空间、公差和密封路径。
- `visuals/MeetNote_R2.blend`：模型从FreeCAD STL以0.001固定单位换算导入；设备几何没有为渲染缩小元件。剖视切开外壳；爆炸图临时平移后恢复保存。
- `visuals/01_front.png`、`02_back.png`、`03_section.png`、`04_exploded.png`、`overview.png`：展示与总览。
- `docs/设计说明与验证边界.md`：贴合、射频、运动触发、功耗、装配缺口和证据来源。
- `单台成本明细.csv`、`docs/单台成本说明.md`：一台成品所需最低采购/加工费用的预留，非报价。
- `verification/mechanical_checks.json`、`cost_and_power.json`、`reopen_check.json`：本机检查。
- `review.html`：本地可打开的图文审阅页。

## 关键结论

主体76×104×34mm，挂点使总高约108mm，侧面执行件令最大宽约76.4mm。外壳/密封/紧固等已建模部分估算约74g；加电池与电子后研究估算约155–190g，尚不适合作为轻巧挂坠定型。它揭示现成模组和单件金属结构的代价，不替代R1小型化目标。

当前定义包络之间无>0.01mm³正体积相交，但真实PCB、器件接头、完整排线、支撑固定与连续密封未完成。因此“零相交”不等于可装配、可佩戴、射频正常或可以直接送厂。

单台首轮物料/制造/结构/运费研究预算：**1985–4530元**；再留25%返修余量约**2480–5660元**。不含研发工时、仪器、认证、云服务与定制全贴合。原厂公开售价仅用于参考，人民币分项尚未供应商确认。
