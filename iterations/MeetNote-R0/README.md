# MeetNote R0 — 会议记录设备工程概念原型

**结论：已经建立可编辑产品基线、ECAD/MCAD原型和检查链路；还没有完成可投板的电子工程，更没有实物可用性证明。禁止使用本包制造文件下单。**

建议从 [产品基线与可行性](docs/01_产品基线与可行性.md) 开始，再看 [验收记录](verification/验收记录.md) 和 [关键器件与证据](docs/02_关键器件与证据.md)。

## 当前基线

- Linux SoC：Zero 2 W，512MB RAM、Wi-Fi/BLE、32GB microSD预算。
- 独立FPGA：iCE40UP5K，4×IM69D130同步音频、采样计数、128KiB短缓冲；FPGA收益需和专用音频ADC方案实测比较。
- Camera Module 3自动对焦+1–2×数字裁切，默认只手动拍照，不持续上传视频。
- 推荐尺寸82×118×29mm；78×110×26mm仅为条件化缩小估算，未验证。
- 2500mAh电芯、2.45W输出端平均预算，计老化/损耗/低电量保留后约2.39h；3W则不足2h。
- 35°C环境触温43°C目标尚未证明，散热与RF净空存在2项冲突。
- 自动决定/任务均保持待确认状态，附证据时间戳。

## 工程文件

|项目|入口|状态|
|---|---|---|
|产品基线、架构、预算|[01 产品基线](docs/01_产品基线与可行性.md)|设计估算，有公式/假设/验收条件|
|器件型号、数据手册、供货/价格及替代|[02 器件证据](docs/02_关键器件与证据.md)|区分核查值与估价；未核实项目不放行|
|电源/布线/EMI/回流/射频约束|[03 ECAD约束](docs/03_ECAD_constraints.md)|列出投板前阻断项|
|软件流程、错误恢复与密钥/更新方案|[04 软件协议](docs/04_软件与数据协议.md)|设计；不是已部署固件或服务器|
|装配、公差、已检出冲突和未建模项|[05 机械约束](docs/05_机械装配与制造约束.md)|包络验证，非完整装配放行|
|KiCad项目|[MeetNote.kicad_pro](electronics/MeetNote.kicad_pro)|主图+7个子页，36个原理图引用，35个PCB封装|
|KiCad原理图与PCB|[主图](electronics/MeetNote.kicad_sch)、[PCB](electronics/MeetNote.kicad_pcb)、[8页PDF](electronics/schematic.pdf)|实际网络/封装；仍未布线，电源/时钟/隐私门控占位|
|BOM|[原生导出](electronics/BOM_native.csv)、[带工程备注](electronics/BOM_engineering.csv)|不是完整整机采购放行BOM|
|制造导出|[NOT_FOR_FAB说明](electronics/NOT_FOR_FAB/READ_ME_DO_NOT_FABRICATE.txt)|Gerber、PTH/NPTH钻孔、钻孔图、贴片坐标已导出；禁止下单|
|FreeCAD源文件|[MeetNote_R0.FCStd](mechanical/MeetNote_R0.FCStd)|可编辑尺寸和布尔特征树|
|装配STEP|[整机STEP](mechanical/MeetNote_assembly.step)、[KiCad导出PCB STEP](mechanical/carrier_from_kicad.step)|PCB为真实导入；其余多为近似器件包络|
|外壳STEP/STL|[底壳STEP](mechanical/case_base.step)、[上盖STEP](mechanical/case_lid.step)、[底壳STL](mechanical/case_base.stl)、[上盖STL](mechanical/case_lid.stl)|用于结构原型检查，未作量产强度验证|
|Blender|[可编辑场景](visuals/MeetNote_R0.blend)、[四视图总览](visuals/overview.png)|机械尺寸驱动；手型仅示意|
|API草案|[OpenAPI](software/openapi.yaml)|YAML及本地引用已检查；未部署|
|软件可运行参考|[pipeline.py](software/pipeline.py)、[测试](software/test_pipeline.py)|12项本机测试通过；不含实际采集/ASR/联网驱动|
|完整清单|[FILE_MANIFEST.csv](FILE_MANIFEST.csv)|路径、大小、SHA-256|

## 重建

`scripts/build_electronics.py` 使用KiCad随附Python/pcbnew，生成符号、分层原理图、载板及清单；随后用KiCad CLI导出XML netlist并执行`scripts/sync_netlist.py`同步网络和Review字段。`scripts/export_and_check.py`记录ERC/DRC的实际退出码并导出文件。

`scripts/build_mechanical.py` 使用FreeCAD随附Python，`PYTHONPATH`指向FreeCAD Resources/lib；它读取KiCad STEP并生成FCStd、装配和STL。`scripts/finish_freecad.FCMacro`在原生FreeCAD中保存只显示最终零件的视图属性。macOS的offscreen Qt不支持所需OpenGL，因此此宏使用原生GUI运行。

`scripts/build_blender.py`由Blender后台运行，所有设备STL统一mm→m变换，创建4张图与原生.blend。`scripts/budget_check.py`重新计算预算。`scripts/release_gate.py`本版**故意返回2**，因为客观检查尚未达到放行条件；它不屏蔽任何ERC/DRC错误。

运行软件参考测试：进入software目录，使用安装了requirements.txt依赖的Python执行 `python -m unittest -v test_pipeline`。测试只在临时目录内产生数据和随机密钥，工程包不包含生产凭据。

## 下一版应首先实测的三件事

1. **电池/供电/热**：真实电芯在低电量、拍照+上传峰值和35°C环境连续2h，记录各轨电压/峰值电流/效率、壳体热点和电池温度；验证低电量封存及充电限制。通过条件包括无欠压复位、2h完成、既定触温及电芯规格内运行。
2. **音频连续性与物理停止**：4–8人真实会议，上传/拍照/SD写入并行，注入200ms主机服务停顿；对照采样计数测丢样、串音、噪声和ASR可用度。冻结软件时操作实体开关，硬件采集必须停止、指示灯准确；同时决定FPGA是否值得保留。
3. **带壳图像与无线**：装真实FPC、金属散热件和电池，对比裸板/带壳Wi-Fi有效吞吐、BLE共存及2小时断网续传；在0.5–3m距离拍白板和投影，核查原图/裁切文字可读性、AF、频闪和手抖。通过后再缩小外形。
