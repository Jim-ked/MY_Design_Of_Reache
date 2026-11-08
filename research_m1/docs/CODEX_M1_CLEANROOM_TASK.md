# Codex执行任务：M1取证固化与独立新建生成器（Clean-room）

**唯一规范**：`M1_SINGLE_AUTHORITY.md`，Authority ID `THESIS-M1-SSOT-2026-11-08`。本任务书只能安排实施，不能修改其数学模型、证据结论和变量命名。若二者冲突，以唯一规范为准并停止冲突步骤。  
**工作仓库**：本地`m1_trajectory`，先核对Git HEAD与未提交文件，不擅自清理用户的76项历史未跟踪资产。  
**性质**：独立全新实现；不得使用旧源码作为模板或导入依赖。先证据，后实现；模型无证据的地方**明确留空**，不做自动继承。

## 0. 阅读与执行纪律（不可跳过）

1. 首先阅读`M1_SINGLE_AUTHORITY.md`全文及附录A、B。首次执行时将两份文件放入新包的`docs/`；在结果中记录该文件的SHA256。**不另创第二份“正式参数表”或“V2冻结说明”**。
2. 阅读项目提供的原始`ZBTJ.pdf`（EFF2024-10-31；核对16R编码/航图、16L RNAV ILS/DME航图），并读取附录A列出的外部官方规范或制造商公开资料；网络无法取得的来源写`not_accessible`，绝不能猜测其细节。
3. 旧工作树中的`src/`、`config/`、`scripts/`、`tests/`与`results/`只允许**只读**查看错误现象或Gate报告；**禁止复制、导入、继承、迁移、重命名后搬运或行级改写旧实现**。禁止直接使用旧水平曲线坐标数组、旧速度锚点、旧GM参数或旧随机种子填新配置。
4. 允许使用公共数学公式、官方程序原始数据及标准第三方数值库。所有运行性输入必须从**原始依据重新登记**，有`evidence_id`、适用日期、单位、基准和审核状态。
5. 不运行E1、Flow、CPA、TLS/碰撞或M2实验；不提交“全部科研Gate PASS”一类不成立的结论；不删除/覆盖现有仓库历史成果。

## 1. 第一阶段——取证复核（先交付，可独立验收）

新建独立目录：

```text
research_m1/
  docs/
    M1_SINGLE_AUTHORITY.md           # 唯一规范原件，不得自行修改
    CODEX_M1_CLEANROOM_TASK.md        # 当前执行说明
    evidence_review.md                # **只记录证据检查与状态，不设新方法**
  evidence/
    source_manifest.json              # AIP/外部来源、页码/URL、日期、单位、SHA256
    adjudication.json                 # 每项Gate对应证据及状态，未知为null
  config/
    study.yaml                        # 唯一参数入口；允许研究性未决值null
  src/
    m1_research/                      # 从空目录编写的新实现
  tests/                               # 全新独立测试
```

A. **程序**：重新从原始AIP记录16R 16L所有程序定位点、航段类型、规定高度类型、所用入口/LTP高程及位移、VPA/TCH或GP/RDH。特别核查16R旧计算32.439431ft差异是否因LTP、程序弧长或高度限制类别导致；16L区分D6.2 ICU FAF、理论FAP和实际GP捕获，并核对600m的适用范围。给出推导、来源页码与差异表；证据不足则保留`UNRESOLVED`。

B. **性能**：分别列出A320和MQ-9A具体子型、适用构型/重量、阶段IAS/CAS/TAS/GS、下降/转弯能力的来源；严格区分NAVAIR 240 KTAS最高速度、USAF >134 KIAS自动襟翼提示及EUROCONTROL研究模型参数；**不得**把任一项改名成MQ9A最终进近GS。整理可引用的研究性速度/机动区间（有证据才填写）、禁止无据估算绝对限值。

C. **误差**：列出已获得/未获得的真实轨迹残差数据；核定高度基准与时间戳。不能从两条CA2922剖面形态或旧GM ρ、q95推断GP σ、τ。必要时只列出拟合方法及数据要求，不虚构统计值。

D. 输出`evidence_review.md`与`adjudication.json`，必须显示每项证据支持到哪一步、缺什么、是否阻挡正式标称和风险用途。**不得以数学可解代替航图或机型真实约束**。

## 2. 第二阶段——从零独立实现统一数学模型

仅依据`M1_SINGLE_AUTHORITY.md`第2—4节开发，不读取旧src/config，不要求旧测试通过，不保留旧字段别名。新包建议最小模块：

- `procedure_reference.py`：从AIP参数重建RF/TF/ILS参考几何、事件、限制对象；执行几何与程序参考分开；必要时先支持部分`REFERENCE_ONLY`输出。
- `aircraft_state.py`：`aircraft_type, mass, configuration, navigation_qualification, performance_evidence`结构；不设默认A320/MQ9速度。
- `time_and_vertical.py`：单一SI速度—时间积分与垂直约束求解；从同一位置/时间关系解析计算速度和运动学；冲突显式返回。
- `smooth_uncertainty.py`：基于研究性SE核的时间相关偏差及**同一实现的导数联合采样**；所有σ、τ若未标定，统计合格状态必须为false。不得通过对离散噪声线性插值和差分来模拟可飞速度。
- `scenario_sync.py`：明确`aircraft_id/procedure_id/scenario_id`、绝对时间和active掩码；输出同一时刻的双机位置及速度。
- `config_loader.py`：只读取`research_m1/config/study.yaml`。不设旧字段兼容、历史转换器、自动回退、缺省速度值。

不得新增无关高保真六自由度、FMS模拟、碰撞风险、障碍物建模或大规模蒙特卡洛实验。若可行性约束资料不足，可用独立**合成输入**进行方程及接口测试，但不能用这些合成数值生成天津“正式”场景结果。

## 3. 代码独立性与科研Gate——必须可自动检查

### 独立性
- 新包不得有`from src...`、`import src...`、`../config`、`human_baseline`、`rpas_baseline`、`U90`、`HL_REF`、`HH`、`legacy`字段或运行时旧文件路径引用。
- 新代码不调用旧`Procedure`/`VerticalProfile`/`C1Transition16L`/`SpeedProfile`/`markov_paths`函数；其数值算法必须重新按唯一数学规格实现。
- 运行时阻断未证明来源的配置；用本目录外的旧配置文件启动时应明确拒绝，不默默映射。
- 允许对旧结果**单向只读对比**错误诊断，但不能把旧数值当成正确答案或自动调整新实现去匹配旧输出。

### 新测试（全部全新编写）
1. 基础单位/坐标/真航向：m、s、m/s、rad一致，给定已知几何可解析验证。
2. 合成RF圆弧与TF直线的点、切向、曲率及边界单侧状态正确；真实程序需独立官方输入才验收。
3. 单一`V_h(s)`得到`T(s)`及`r(t)`，反算`ds/dt=V_h`；垂直速度`v_z=V_hh'`，验证单位无二次转换。
4. 同一随机SE实现偏差及时间导数数学一致；固定随机种子仅用于算法复现，不作为研究证据。
5. 同时刻双机活动域无外推，坐标、高度、速度有可追踪单位。
6. 条件不成立时分别输出`CONSTRAINT_CONFLICT`、`PERFORMANCE_UNQUALIFIED`、`STATISTICS_UNCALIBRATED`，不默默求值。
7. 配置自包含测试：隔离新包运行环境后不需要任何旧文件或旧仓库模块。
8. 科学状态正确性：合成测试可PASS，但无LTP、性能包线或统计标定时`G1/G2/G4`绝不可自动PASS。

## 4. 审计交付与停止条件

交付：`research_m1/`目录、唯一`study.yaml`、`source_manifest.json`、`adjudication.json`、`evidence_review.md`、源码、新单元测试、`README.md`运行说明、测试输出与Git提交号。`README`只能说明如何执行，不得另定研究公式和参数；任何文档冲突均回归唯一规范。

报告中明确列出：
- 当前证据已支持的程序点/公式/模型约束；
- 尚存的16R LTP/TCH、16L高度/FAP、机型包线、GP幅度/相关时间参数；
- 取得哪些新证据后可以从`REFERENCE_ONLY`升级`NOMINAL_QUALIFIED`与`M2_READY`；
- 与旧项目的代码隔离验证结果；
- 运行结果的研究用途边界。

**关键停止规则**：若无法从原始AIP定位关键高度基准或资料不支持机型性能参数，不得用旧数值或自己选择的“合理数值”填补；继续完成可独立验证的通用模型和测试，标注正式场景阻断项并在本次提交给出已完成的最大成果。不允许为了“交付完整”改变模型定义或降低证据标准。
