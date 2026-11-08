# 16L单段条件LOC参考实施记录

本记录落实用户2026-11-08裁定，不是第二份科学规范；唯一科学模型依据为M1_SINGLE_AUTHORITY.md。独立Clean-room仓库先将16R分支快进合入main，并核验远端main为9c2d8e45830511aa34d23fb8a208c661a58ccb88；此后创建research/16l-loc-reference实施。16L分支不合入main。

## 来源与状态

| 来源 | 生效日期/定位 | 本轮使用及限制 |
|---|---|---|
| H01_4Y01：ZBTJ.pdf | 2024-10-31，p23 | 原始TJ954 N39°16′37.0″ E117°16′39.0″保留；新增TJ919、TJ960坐标仅用于程序元数据，已视觉复核 |
| H01_5A：ZBTJ.pdf | 2024-10-31，p43 | IF TJ954/D9.2 ICU、FAF D6.2 ICU、161°磁航向；TJ919/TJ960→TJ954拓扑。未重判高度限制 |
| H01_AD2025：天津滨海.pdf | 2025-10-02，AD2.12/p12、AD2.19/p17–18 | 真方位154.45°、3200m跑道、LOC坐标与末端外310m、DME/IM各自坐标；真向与磁向分别登记，不强制精确互换 |
| H01_2A_2025 | 2025-09-04 | 保持新包既有ARP ENU；不建立另一套坐标基准 |
| E16：用户本轮实施说明 | 2026-11-08 | 条件水平工程选择；不是数据库坐标、实飞导航捕获、运行批准或跨AIRAC相容性证明 |
| 用户引用Doc8168 §1.3.2及ICAO APAC FPP 2025 p33 | 规范定位由用户提供 | 作为已裁定方案的背景来源，本轮未重新核证规范全文；2025培训链接获取返回HTTP404，未作为新取得的一手证据 |

原始PDF完整SHA256分别为484482e46c7880fb8e4071e26c4af5d2c5d912109ba040ad22250726f129ce98与a71fc8268f1b965dcb7f2f6818a9b552616a15b4a5f38c497e965531ed44fd3b，已复核；原件与页面图片不发布。2024/2025资料相容性仍为CROSS_DATE_UNVERIFIED。

## 参考定义及结果

保留新包独立WGS84→ECEF→ARP ENU实现。以LOC处公布真向构造当地单位向量，再变换至ARP ENU并归一化为u。由LOC位置及3200+310m沿向距离得到条件入口Q；对公布TJ954投影P，计算L=−(P−Q)·u、P_IF_ref=Q−Lu。参考仅为c(s)=P_IF_ref+s*u，0≤s≤L；不改变公布TJ954，不建立连接线、FAF转弯或截获曲线。

条件FAF以DME坐标为圆心、6.2NM为水平半径，与LOC轴线求进近侧交点。它不是斜距解，不猜测DME天线标高或飞行高度。模型进入时刻对应IF_REFERENCE_STATION，不宣称精确飞越公布TJ954。

| 对象/诊断量 | 结果 | 状态/语义 |
|---|---:|---|
| TJ954_PUBLISHED | 原始坐标不变；不赋参考曲线s | 原始字段SOURCE_VERIFIED；ENU投影另标DERIVED_COORDINATE |
| IF_REFERENCE_STATION | s=0m | CONDITIONAL_LOC_REFERENCE |
| IF_PUBLISHED_TO_LOC_CROSS_TRACK_M | 132.041m；左法向带符号−132.041m | 跨日期来源诊断，不是数值误差、正常导航偏差或sigma |
| THR | s=16742.690m | 条件LOC参考入口，不证明精确LTP |
| FAF_D6P2_ICU | s=5579.717m；距入口11162.973m | CONDITIONAL_DME_HORIZONTAL_EVENT，水平距离非斜距 |
| FAP | null | UNRESOLVED |
| GP_CAPTURE | null | UNRESOLVED |
| LOC法与IM法入口差 | 1.712m | 独立来源一致性诊断，不平摊、不调参 |

完整事件ENU、单位向量、版本与诊断保存于reference_geometry_results.json的16L项。TJ919/TJ960→TJ954仅为域外拓扑，不生成IAF进场轨迹。沿程支持仅IF参考站位至THR，段内切向恒定、曲率为0，FAF只是事件。

## 验收与保留项

测试覆盖单段、端点/LOC方向、投影正交性、约132m来源偏差、DME水平交点、事件顺序、FAP/捕获留空、拓扑及配置不修改；非法事件顺序拒绝。全部基础回归36/36通过（原31项加本轮5项），16L专项另行5/5通过，命令和完整输出见loc_reference_tests.json；首次新属性测试在旧FAF起算实现上失败，随后实现本轮裁定。

以main@9c2d8e4核对16R函数、RF求解模块/测试/配置/保存结果及Gate子项不变，原31项基础测试全部保留。唯一科学依据仅修改现有P16L证据条目并增加E16；第2–6章模型定义、命名与G1–G5判据不改。16L约束/高度/速度、机型、运行、随机参数及case_001双机语义均不改。

16L水平状态为CONDITIONAL_LOC_REFERENCE；16L_FULL_NOMINAL和G1_PROGRAM仍UNRESOLVED。16R仍CONDITIONAL_REFERENCE_GEOMETRY。G2–G5状态不变，不宣称程序、机型性能或随机统计资格通过。未开展垂直曲线、性能、随机统计、E1/Flow/CPA/M2/TLS或碰撞风险实验。实现完成后停止，留待人工审计。

改动仅为research_m1中的aip_reference.py、study.yaml、16L旧测试断言与新增test_16l_loc_reference.py，以及README、M1_SINGLE_AUTHORITY、evidence_review、本报告、source_manifest、reference_geometry_results、adjudication、loc_reference_tests和publication_allowlist。完整13项路径见测试记录modified_files；公开白名单增加本报告、专项测试及测试记录三项，不发布原始AIP、图像或个人路径。
