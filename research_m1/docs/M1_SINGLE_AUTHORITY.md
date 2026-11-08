# M1 四维轨迹统一模型与取证裁定——唯一实施依据

**Authority ID** `THESIS-M1-SSOT-2026-11-08`  
**状态** `ACTIVE / SCIENTIFIC-SPECIFICATION`（研究模型及证据规则生效，不代表全部实证参数通过）  
**适用项目** 《基于碰撞风险的终端区有人/无人航空器混合运行保护区划设方法研究》  
**实施范围** 天津滨海机场平行进近：左跑道16L RNAV ILS/DME；右跑道16R RNP y (AR)；有人机A320及研究性MQ-9A情景。  
**唯一原则** 本文是模型、命名、证据状态及数据模式的唯一权威。`CODEX_M1_CLEANROOM_TASK.md`仅规定执行步骤，不能增设科学口径。先前`Method-M1/1.0`和所有历史冻结、配置及Gate报告仅留作**来源记录或错误审计资料**，不能与本文拼接构成正式模型。后续修订只修改本文并记录变更，不新建并行规范。

## 1. 本轮取证的真实结论

本轮已用公开权威资料完成**定义与证据适用性核验**，但尚未取得足以认证A320/MQ-9A完整性能包线或标定两机随机误差的原始资料。不得把“已查找证据”误写成“所有参数取证完成”。外部资料均按[证据台账](#附录a-证据台账与允许支持的命题)的适用范围使用。

| 裁定ID | 取证结果与明确界限 | 当前状态 | 实施动作 |
|---|---|---|---|
| P16R-LTP | RNP AR设计以**着陆入口点 LTP**为垂直参考，VPA/RDH与LTP高程和沿程距离相关[E02]；归档程序与旧Gate有32.439431 ft闭合残差[H02]。现有材料**不足以证明**旧软件RW16R与公布LTP同一点、用的是同一入口高程、已正确处理入口内移及高度限制类型。 | `SOURCE_RECONCILIATION_REQUIRED` | 从原始AIP重新取得LTP、跑道入口、移位及各点坐标/高程；独立解析公式核算。不自动修改TCH/VPA或把残差分摊到平滑段。 |
| P16L-FAP | ICAO对ILS精密进近FAP定义是**名义下滑道与前一航段规定最低高度的交点**[E01]。旧Gate的D6.2 ICU定位点、600m/GP交点间隔42.773m仅是历史实现数值[H02]，不能单独证明程序冲突或完全相符。 | `CONSTRAINT_TYPE_REQUIRED` | 从ZBTJ-5A核对600m限制适用区间、DME和RDH定义、真实LTP；程序FAF（图示定位点）、FAP及执行GP捕获时刻分别存储。 |
| P16L-UNIT | MH/T 4019—2012第4.2.1节规定高程基准、第4.3.1节规定**高度以m标注、必要时并列ft**[E03]。 | `SUPPORTED` | 16L600m/2000ft仅作为同一公布标注，不能构造两条精确限制；须按航图的标注关系与高程基准读值。16m/52ft也不得拆成两个精确门限。 |
| P-RF | FAA AC 90-101A为RNP AR运行提供适航及运行批准指导[E04]；RF需特定设备/运行能力；研究性MQ-9A不能自动视为获批。[E05]亦要求RF保持能力。 | `CONDITIONAL_SCENARIO` | 16R使用MQ-9A仅以明确的**假设具备相应导航能力**作为研究情景；输出注明未经实际运行批准核证。 |
| PERF-A320 | Airbus解释VAPP由着陆构型VLS和风修正决定[E06]，不是机型固定进近速度；具体机重/构型及VLS需进一步取证。 | `PARTIAL` | 速度在机型、质量、构型、风条件明确后定义；禁止从历史有人机速度表直接抄值。 |
| PERF-MQ9 | 美国海军MQ-9A Block V技术页公开**最高240 KTAS**[E07]；美国空军MQ-9操作手册提示进近**超过134 KIAS**会触发自动襟翼调度，可能增加操纵难度[E08]；EUROCONTROL 2015 RPAS性能建模技术报告有MQ-9研究参数表[E09]。这三种量的**构型、速度类型、适用对象不同**，均不能直接充当本算例进近GS或最大法向加速度。 | `PARTIAL` | 记录具体型号/Block/重量/构型，进一步查可用进近IAS、爬降率、坡度/载荷等；缺失项限定为有标识的探索性参数扫描，不称已验证性能。 |
| UNCERTAINTY | FAA区分TSE、PDE、NSE、FTE[E10]；平方指数GP具有均方可微性[E11]，但无证据证明它是天津A320/MQ-9A的真实误差分布。旧离散GM的`ρ=0.8@18.52m`已由Gate证实对速度差分造成严重语义问题[H02]。 | `METHOD_CHOSEN, PARAMETERS_NOT_CALIBRATED` | 保留时间相关可微GP作为**待验证研究方法**；不导入旧ρ、旧q95、RNP数值作标准差；样本的速度必须从同一过程导出。 |
| EVIDENCE-CURRENCY | 本项目`ZBTJ.pdf`为**EFF 2024-10-31**的归档程序资料[H01]；本轮未获得对2026-11-08仍有效的AIP逐页核证。 | `HISTORICAL-AIP-SNAPSHOT` | 模型实例首先明确使用“2024-10-31航图研究快照”；不得表述为2026现行运行批准资料。后续若核得更新AIP，在本文记录正式变更。 |

### 1.1 不得误判的三类证据

- **一手规范/程序**：决定程序坐标、限制类型、LTP、VPA、RDH/TCH与运行资格。其他来源不能覆盖。
- **航空器技术/运行与实飞**：用于阶段速度、可行机动、垂直过渡和数据统计。技术概况页的巡航或最大速度不能替代进近速度；个别航班形态不能直接认证完整包线。
- **计算或旧代码事实**：只揭示历史计算的残差、错误或可对照数据；42/42测试PASS不能升格成新模型认证，旧文件不得作为新配置导入源。

## 2. 唯一研究对象与命名

- `aircraft_id`：无含义的实例编号，如`aircraft_01`、`aircraft_02`；`aircraft_class`为`manned`/`rpas`；`aircraft_type`为`A320`/`MQ9A`，不得用`H/U/U90`代替型号。
- `procedure_id`：`ZBTJ_RWY16L_RNAV_ILS_DME`或`ZBTJ_RWY16R_RNP_Y_AR`；`runway_id`为`16L`或`16R`；程序、跑道、机型各是独立字段。
- `scenario_id`：不带隐藏性能含义的唯一编号`case_001`、`case_002`；通过`assignments`数据表准确指明机型、程序、航段进入时刻、气象、质量和构型，严禁以`S_MM/S_MU/HH/U90/HL_REF`代替这些字段。
- `reference_frame_id`：`ZBTJ_ENU_ARP`，明确WGS84经纬度、垂直高程基准及转换；`x/east`东、`y/north`北、`h/altitude_msl`向上；**长度、时间、速度、角度统一SI（rad而不是deg）**，原始航图单位单独保留在证据数据中。
- `segment_id`与`event_id`严格区分：IF、RF、TF、ILS_FINAL等是程序/几何类型；FAP、FAF、GP_CAPTURE是不同事件。研究内部算法断点不能冒充公布定位点。

## 3. 一套模型，而不是三套旧设计拼接

### 3.1 程序约束与水平参考

对`procedure_id=p`，程序对象为`𝒫_p=(c_p(s), 𝒞_p, 𝒩_p)`：`c_p(s)`为按水平弧长`s∈[0,L_p]`参数化的公布参考几何，满足`||c_p′(s)||=1`（分段成立）；`𝒞_p`存放每项带位置/类型/区间/高度基准/来源的限制；`𝒩_p`存放该程序的设备能力和运行前提。**程序参考几何不是自动驾驶实际闭环路径**。若连接处只有曲率阶跃，先记录单侧切向/曲率，不自动加样条改变RF/ILS中心线。

### 3.2 机型可执行的标称运动

对航空器`i`、给定质量/构型/风`Θ_i`，求`V_{h,i}(s)>0`（水平路径上的**地速**）与`h_i(s)`（MSL高），并定义

`T_i(s)=t_{i,entry}+∫_0^s dξ/V_{h,i}(ξ)`；`s_i(t)=T_i^{-1}(t)`；

`r_i^0(t)=[c_{p_i}(s_i(t)),h_i(s_i(t))]`。

统一速度为同一函数的导数：`v_i^0(t)=V_{h,i}[c'_{p_i,x},c'_{p_i,y},h'_i]`；垂直速度`v_{z,i}=V_h h'`；路径角`γ_i=atan h'`；角变化率`γ̇_i=V_h h''/(1+h'^2)`；水平法向加速度`a_{N,i}=V_h² κ_p`。**若发生实际水平过渡，计算使用执行水平曲线而非把参考曲线与执行曲线混用**。由IAS/TAS算GS必须使用已说明的大气和风模型；不得出现速度以kt输出却命名`_mps`或对m/s二次乘转换系数。

**水平执行路径的一致性规则**：默认`c_i^exec(s)=c_{p_i}(s)`。若证据和性能校核确实要求局部执行转接，应另定义`c_i^exec`及其**自身水平弧长**，重新计算相应`T_i(s)`、`h_i(s)`、切向、曲率与随机法向；此时上述公式中的`c_p`在整条标称/随机计算链中统一替换为`c_i^exec`，**不能位置用执行曲线而速度继续取程序参考曲线**。程序几何`c_p`永久保留作偏差/程序约束核查依据，执行曲线不得无依据超出程序容许范围。未能证明必要性时不自动生成局部样条。

**高度求解原则**：给定每一项真实程序限制（minimum/maximum/at/窗口）、LTP/入口高程、VPA、TCH或RDH以及机型速度/下降/转弯可行域，求解满足限制的最低自由度分段标称高度`h_i(s)`；不存在可行解则返回`CONSTRAINT_CONFLICT`或`PERFORMANCE_UNQUALIFIED`，且不偷偷改动航图数据。**不得指定固定400m或281m过渡；过渡位置/时间由区间和能力约束求得**。对未知机型限值只能明确建立`conditional_assumption`的技术性样本，不能输出`qualified`。

### 3.3 正常随机轨迹与速度

本次维持数学上自洽的**候选**时间相关SE高斯过程（不是由FAA/ICAO规定的误差分布）：对`q∈{N,Z}`，`e_{q,i}(t)=σ_{q,i}(s_i(t)) Z_{q,i}(t-t_{i,entry})`，`Cov[Z_q(u),Z_q(u′)]=exp[−(u−u′)²/(2τ_{q,i}²)]`。仅有来源明确的`σ`、`τ`及平滑包络时才可输出`statistically_qualified`；没有数据时只可**明示探索性**样本，不可将其概率用于TLS风险结论。不得从RNP标签推出单轴σ，不得导入历史ρ/q95。

参考方向`n_p(s)=[−T_y(s),T_x(s),0]`，正常随机位置

`R_i(t)=r_i^0(t)+e_{N,i}(t)n_{p_i}(s_i(t))+e_{Z,i}(t)[0,0,1]`。

随机速度必须是`dR_i/dt`；在光滑参考段，`V_i(t)=V_h(1−κ_p e_N)[T_x,T_y,0]+ė_N n_p+[0,0,V_h h′+ė_Z]`。如使用GP离散采样，**同一实现必须联合生成偏差及其时间导数**，不得简单连接离散随机点再将差分速度称为物理速度；也不得把标称速度复制到随机状态。SE核只保证光滑统计过程，不保证速度或过载的确定性上限；若进行机型可行性条件筛选，需明确筛选后分布变化，M2不得沿用筛选前的高斯边际概率。

不再给沿程偏差独立增设第三组GM。进入时差`Δt_entry=t_{R,entry}−t_{L,entry}`以及航班级速度参数变化作为独立定义的运行输入/随机变量，防止重复计数；若没有速度分布依据，就做有边界的场景扫描，不称统计频率。

### 3.4 双机与M2接口

`aircraft_state(t)`结构保留`aircraft_id,scenario_id,procedure_id,aircraft_type,time_abs_s,s_m,east_m,north_m,altitude_msl_m,velocity_e_mps,velocity_n_mps,velocity_u_mps,active,model_status,provenance_id`；`nominal_state`与`sampled_state`为两种不同语义。双机只在相同绝对时间、双侧`active=true`计算`ΔR`与`ΔV`；不做活动域外外推；异常偏航、管制响应、碰撞事件与TLS归M2。

## 4. 唯一配置与实现边界

- 新源代码必须位于仓库内独立`research_m1/`包，唯一配置为`research_m1/config/study.yaml`、唯一正式测试为`research_m1/tests/`。**从空文件独立编写**；不import、不调用、不复制、不改写旧`src/`、`config/`、旧`scripts/`及旧研究YAML；不将旧几何离散点/时间曲线/随机GM作为新配置默认值。第三方普通数值库（numpy/scipy/pyproj等）允许，但版本显式记录。
- 数学公式可以使用公开标准数学和本文件的统一数学定义。重新读取原始AIP坐标、程序编码、机型资料及有授权的监视数据形成新参数，注明来源及签名；不能通过对旧参数进行`*0.514444`之类的批量转换生成所谓新配置。
- `study.yaml`分`airport, procedures, aircraft, operations, uncertainty, scenarios, provenance`七个单一归属字段；各值必须带量纲/来源/审核状态；未知数取`null`并记录`required_evidence`（不得设历史回退值）。`case_001`与`case_002`通过字段决定，不以编号编码航空器类别。**一个配置，不能把多个候选型号/模式混装为“自动回退”**。
- 如果证据不足：支持读取研究配置并给出明确阻断原因；允许在**独立示例命名空间**中以合成数据验证算法，但不得生成名为“天津正式标称轨迹”或“M2_READY”的数据；不得把`null`替换为猜测数值使测试通过。
- 新实现正常状态只能由正式配置解析和新算法产生。旧代码仅可供人工发现失败模式或作为不具方法权威的差异观察；**旧测试42/42通过不是新验收依据**。

## 5. 五道独立验收关口与可交付结果

| Gate | 必须满足的客观条件 | 不满足时允许交付什么 |
|---|---|---|
| `G1_PROGRAM` | 官方AIP快照可追溯；16R LTP/入口移位/坐标高程/2000ft限制性质与3°/TCH关系闭合；16L FAP/FAF/600m限制/RDH定义有依据；无法闭合时说明相矛盾的来源与计算 | `evidence_audit`与`reference_geometry`，**不能**声称正式垂直剖面通过 |
| `G2_AIRCRAFT` | A320/MQ-9A对应阶段速度类型、构型及可行机动界限有可核实依据；RNP AR能力为真实证据或**显式有条件假设** | 研究性可行性区间及`conditional_scenario`，不称运行批准 |
| `G3_NOMINAL` | 新代码独立实现；水平几何程序一致；速度/时间/高度/垂直速度源于同一模型；关键航段单侧运动学检查；已证实程序限制满足 | 合成单元测试及明示`UNQUALIFIED`的参考几何，不生成正式场景模拟结果 |
| `G4_STOCHASTIC` | σ与τ来源清楚，统计含义和相关尺度可验证；同一随机实现的偏差/导数一致；不把样本筛选后分布当原GP | `exploratory`样本及统计诊断，不声称M2概率基线 |
| `G5_HANDOFF` | 双机统一绝对时间、活动域及相对位置/速度语义完整；G1—G4所需资格均通过 | 接口测试数据，不宣布M1正式结束 |

**注意**：科学口径已统一，不等于G1/G2/G4数据事实已全部通过。禁止通过选择旧值、改模型或降低Gate条件来快速宣布`PASS`。可并行推进数学单元测试和证据补强，但证据不足时只能交付有明确限定的内容。

## 6. 版本控制与修改权限

1. 本文是唯一约束文件。`CODEX_M1_CLEANROOM_TASK.md`仅是执行命令，不得修改本文数学定义、状态或判据；Codex不得自行宣布“Method-M1/2.0已冻结”。
2. 一旦有新证据，先在本文**同一证据台账**增加`E##`记录、标记旧证据适用性变化，再建议修改对应条目；未经人工研究裁定，不擅自改变现行公式或任务范围。
3. 任何`source_ref`必须能回指公开URL（带版本）或用户提供的具体AIP/报告文件与页码；`assumption`须标明是否用于探索，不能伪装为`measured`。
4. 新代码不得依赖旧实现或旧配置；可进行只读、单向的差异报告，但旧输出不是回归“金标准”。
5. 结果报告按`SUPPORTED / CONDITIONAL / UNRESOLVED / CONFLICT`分别出具，不把一次测试PASS上推至科研或运行资格通过。

## 附录A 证据台账与允许支持的命题

| 编号 | 来源与可复核定位 | 证据级 | **允许支持** / 禁止推断 |
|---|---|---|---|
| H01 | 本项目`ZBTJ.pdf`，EFF2024-10-31，16R编码p42、16L进近图p43、16R图p53（以实际PDF页码复核） | 归档官方程序快照 | 程序点/程序图示/公布单位；不证明2026现行有效 |
| H02 | `m1_gate_facts.json`、`M1_GATE_REVIEW.md`（2026-11-08，旧工作树读数） | 历史计算诊断 | 16R32.439431ft、16L42.773m和旧GM/速度接口风险；不支持直接复制旧数值到新模型 |
| H03 | `M1垂直模型修正冻结说明_V1.2.md`中CA2922两次实飞形态分析（原始绝对高度基准尚未独立核实） | 实飞二手研究记录 | RF1剖面可变；不支持机型认证/标准误差统计参数 |
| E01 | ICAO Doc 8168 Vol II, 7th ed., Part II Section 1 Ch1 §1.4.2 (2020): https://www.icao.int/sites/default/files/APAC/APAC-FPP/FPP%20Training/FPP%20Training%20in%202024/Pans-Ops%20Procedure%20Design%20Initial%20Course/Courseware/8168_v2_cons_en.pdf | 程序定义 | FAP为名义GP与前一航段最低高度交点；其他IF/FAF定义不能由此随意等同 |
| E02 | ICAO Doc 9905, *RNP AR Procedure Design Manual*, 1st ed. (2009), §4.1.6图4-1（**该公开版较旧**）: https://www.icao.int/meetings/pbn-symposium/documents/9905_cons_en.pdf；3rd ed.(2021) 官方书目: https://store.icao.int/en/required-navigation-performance-authorization-required-rnp-ar-doc-9905 | 程序设计参考 | LTP为RNP AR垂直/坐标参照，提醒复核入口高程；**不作为2021版逐条法规文本** |
| E03 | CAAC, MH/T 4019—2012, §4.2.1、§4.3.1: https://www.caac.gov.cn/XXGK/XXGK/BZGF/HYBZ/202111/P020240719331529051959.pdf；官方信息页 https://www.caac.gov.cn/XXGK/XXGK/BZGF/HYBZ/202111/t20211109_209970.html | 行业标准 | 航图高程基准/公制与英尺并列标注；不证明16L具体高度点的限制类别 |
| E04 | FAA AC 90-101A including Change 1, official descriptor: https://www.faa.gov/airports/resources/advisory_circulars/index.cfm/go/document.information/documentNumber/90-101A | 运行批准指导 | RNP AR需相应飞机资格与运行批准；不认证MQ-9A具备该资格 |
| E05 | Transport Canada AC700-027 §4: https://tc.canada.ca/en/aviation/reference-centre/advisory-circulars/advisory-circular-ac-no-700-027 | RF能力说明 | RF程序执行与监测要求；不等于天津程序的本地运行许可 |
| E06 | Airbus Safety First, *Control Your Speed… During Descent, Approach and Landing*: https://safetyfirst.airbus.com/control-your-speed-during-descent-approach-and-landing/ | 制造商运行资料 | VAPP由VLS构型、风修正决定；不提供本场景固定A320速度 |
| E07 | NAVAIR *MQ-9A Reaper*, Block V: https://www.navair.navy.mil/product/MQ-9A-Reaper | 机型技术概况 | 最大240 KTAS等，**不是**进近CAS/GS或转弯极限 |
| E08 | USAF AFMAN11-2MQ-9V3 (2023-01-12), Appendix A3.6—A3.9, printed p47: https://static.e-publishing.af.mil/production/1/af_a3/publication/afman11-2mq-9v3/afman11-2mq-9v3.pdf | 操作指导 | >134 KIAS的自动襟翼调度提示、坡度与重量条件需要按TO；不能把134kt设为进近目标/最高许可 |
| E09 | L. Carbo, EUROCONTROL EEC Technical Note 15/11/06-50 (2015), *Approach to the Introduction of RPAS in BADA 3*, Table3: https://www.researchgate.net/publication/332670811_APPROACH_TO_THE_INTRODUCTION_OF_RPAS_IN_BADA_3_AIRCRAFT_PERFORMANCE_MODEL_EUROCONTROL | 研究性能模型 | MQ9研究参数如CAS失速和阶段速度可作为**候选证据/范围筛选**；非当前Block的厂家认证手册 |
| E10 | FAA AC90-105A, §4.3: https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_90-105A_Ed_Update_2.pdf | 导航误差定义 | TSE/FTE/NSE/PDE区分；不允许直接由RNP值推出某单轴正态σ |
| E11 | Rasmussen & Williams, *Gaussian Processes for Machine Learning* (2006), Ch4 §4.2: https://gaussianprocess.org/gpml/chapters/RW4.pdf | 概率数学理论 | SE核均方无限可微；**不能**证明该核真实符合具体航迹误差或满足机型速度上限 |
| E12 | EUROCONTROL BADA官方项目：https://www.eurocontrol.int/model/bada | 建模方法背景 | BADA用于机型几何/运动学/动力学模拟；无授权数据不得杜撰A320模型包线 |

## 附录B 仍待解决的最小证据事项（与科学口径区别开）

1. **16R**：归档AIP下的LTP精确位置/高程、公布2000ft的限制类型、VPA/TCH闭合；校验“跑道开始点/移位入口/RW终点”三者是否混用。输出一个明确的数值残差分解和资料来源，而不是新曲线方案。
2. **16L**：归档AIP下600m限制类型和作用范围、D6.2 ICU定位/测距基准、FAP定义、RDH对应的LTP高程；核定原始图示的记录精度，禁止强制DME数值化为精确几何点。
3. **机型**：A320本次重量、着陆构型及VLS或有据参考速度；MQ-9A具体子型、构型、进近IAS与下降/转弯能力。至少给出有出处的正常运行**研究取值/区间**与其适用边界，绝不把巡航速度或134 KIAS提示直接当GS。
4. **统计**：至少能追溯样本的时间戳、经纬度/高度基准、机型、程序阶段、定位残差和对应误差时滞的自相关；无充分数据时将σ、τ写为`null`并保留探索参数专用标签，不引用旧GM参数。
5. **导航资格**：MQ-9A在16R RF/RNP AR按`conditional_navigation_assumption`建模，非实际批准；可行性研究与适航/运行批准结论永久分离。

## 2026-11-08 第二轮取证记录（不改变上述数学规格）

依本轮用户任务授权，记录新恢复资料；下表延续同一证据台账，不构成新规范。

| 编号 | 来源与定位 | 新核实事实与限制 |
|---|---|---|
| E13 | 用户授权本地 `ZBTJ.pdf`，56页，SHA256 `484482e46c7880fb8e4071e26c4af5d2c5d912109ba040ad22250726f129ce98`；p23 ZBTJ-4Y01、p42 ZBTJ-4Z18、p43 ZBTJ-5A、p53 ZBTJ-9E | 已恢复原始程序点和RF/TF编码。各页生效日期分别登记；p53为EFF2024-10-03，p23/42/43为EFF2024-10-31，不能把合并PDF当单一AIRAC。16L不得使用RNP RWY16L的TJ958/TJ901/TJ957路径。 |
| E14 | 用户授权本地 `天津滨海.pdf`，SHA256 `a71fc8268f1b965dcb7f2f6818a9b552616a15b4a5f38c497e965531ed44fd3b`，AD2.12/p12、AD2.19/p17–18，EFF2025-10-02；机场图ZBTJ-2A为EFF2025-09-04 | 可核对LOC/IM/DME各自坐标、入口相对距离与真方位；与2024进近页的版本相容性未核证。只支持明示跨日期的部分参考几何，不证明完整运行程序已通过。 |

`case_001`为同一情景中的两项分配：`aircraft_01/A320/16L`及`aircraft_02/MQ9A/16R`。正式进入时刻仍未决；合成接口示例的相对时刻单独标注，不是航班UTC或机型性能证据。G1垂直/LTP、G2与G4未决，不因本次补录升级。
