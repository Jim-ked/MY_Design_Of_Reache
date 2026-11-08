# M1 Clean-room 第二轮执行报告

日期：2026-11-08。此文仅为工程执行记录，唯一数学规格仍为M1_SINGLE_AUTHORITY.md。

## 已执行与范围

本地起点e702194355402511ee89eb47f948376b530f2c07。只继续开发research_m1；未运行或引用历史模型、配置、速度表、GM、C1及其测试金标准。恢复独立原始AIP56页包、页码/日期清单及关键页核读，未复制原件至发布目录。新代码新增geodesy.py、aip_reference.py和CLI，修正双机数组、活动域与相对状态，增加独立测试，更新配置/来源/Gate报告。没有垂直过渡优化、E1/Flow/CPA/TLS/碰撞/M2实验。

## 来源及独立结果

source_manifest.json记录原始文件SHA256、页码、原文单位、日期、提取方法及限制。源文件各页EFF分别为2024-10-03、2024-10-31、2025-09-04和2025-10-02，未假定单一AIRAC或2026有效性。

16R使用4Z18右转2.7NM编码与4Y01原始DMS点；RF1/RF2/TF独立段长为7867.763378/7910.123764/3333.051801m。圆半径与公布点无法同时闭合，TJ903处保留84.284264m位置缺口，不生成补线、不拟合半径、不冒充连续执行轨迹。条件TCH审计残差2.920537m只适用于报告中的临时等式组合；LTP/内移/高度符号不能唯一归因，未静默修正。

16L明确排除TJ958/TJ901/TJ957及RNP RWY16L条目；仅以新核读LOC、IM、DME和真方位构建条件LOC部分。水平D6.2近似最后段为11162.973055m，LOC/IM两法入口差1.712304m。TJ954接入缺口、理论FAP、实际GP_CAPTURE、测距斜距和版本相容性保持未决。分段来源、站点和单侧切向/曲率见reference_geometry_results.json。

case_001同一场景的两机为aircraft_01/A320/16L、aircraft_02/MQ9A/16R；正式t_entry_s和delta均null。正时差定义为第二架减第一架。唯一study.yaml中synthetic_demo的0s/7s进入、20s/16s时长及合成直线仅用于接口测试；不声称实际航班UTC或飞机性能。活动域外不调用求值器、不外推；双侧active时才计算同一时刻位置及速度差。

## 分层验收

| Gate | 科研状态 | 独立可用子成果 |
|---|---|---|
| G1_PROGRAM | UNRESOLVED | SOURCE_VERIFIED原始字段；PARTIAL_REFERENCE段；版本/垂直/LTP未决 |
| G2_AIRCRAFT | UNRESOLVED | MQ9A RNP AR仅条件导航假设；机重/构型/性能无认证 |
| G3_NOMINAL | CONDITIONAL | 独立几何及CONDITIONAL_NOMINAL合成数学演示；不生成正式执行轨迹 |
| G4_STOCHASTIC | UNRESOLVED | SE联合偏差/导数公式测试；sigma/tau为null，STATISTICS_UNCALIBRATED |
| G5_HANDOFF | UNRESOLVED | 双机时间/active/相对状态接口；M2_NOT_QUALIFIED |

数学单元测试通过、程序约束成立、机型适用及统计标定通过是四种不同结论；此轮只支持数学与接口测试、部分参考几何。

## 验证

`python -m unittest discover -s research_m1/tests -v`：17项通过。测试覆盖独立ENU解析例、RF左右曲率、源段缺口不隐藏、16L无RNP点混入、同一随机位置解析速度、SE核导数协方差、双机进入/退出及配置未知值阻断。新包导入/路径扫描与独立发布目录隔离复测须通过才推送。完整输出见test_output.txt。

## 公开发布

目标：https://github.com/Jim-ked/MY_Design_Of_Reache ，分支main。已只读确认远端无heads/tags，独立克隆为空仓库；不复制旧.git、不推原本地分支、不使用force。发布仅使用下列白名单与根README/.gitignore/.gitattributes，拒绝PDF/图像/原始轨迹/凭据/缓存/Windows用户绝对路径。原始文件只登记指纹与获取说明，不再分发。

### 实际发布结果：BLOCKED，未发布成功

已在旧工作树外独立clone空仓库，并在独立目录隔离复测17/17通过；逐文件确认35项白名单、源文档指纹、无用户绝对路径/凭据/二进制源文件。独立代码载荷根提交为`eb48c6ed5781eb8bf2da7ee9d433984e36d92f60`，没有旧项目提交作为父节点。随后仅本报告补录发布失败记录，不修改经过测试的代码载荷。

两次普通`git push -u origin main`均在连接阶段失败：`Failed to connect to github.com port 443 ... Could not connect to server`。已连接GitHub接口可读取目标仓库，核实visibility=public、default_branch=main；但首次README创建也返回`403 Resource not accessible by integration`，未写入成功。最终`git ls-remote origin refs/heads/main`持续无输出，已终止；改用GitHub branches API核验返回`[]`，没有main提交。**remote_sha=null，GitHub提交链接=null**，不能把本地SHA当成远端发布成功。任务书允许网络/认证失败时准确报告阻断，本轮按此停止；不是自动审批拒绝。

网络与仓库写入权限恢复后，在独立发布目录直接执行以下命令即可，不连接原项目历史：

```powershell
git remote get-url origin
git log --oneline --all
git status --short
git push -u origin main
git ls-remote origin refs/heads/main
```

成功后须核对GitHub main的SHA及完整远端文件树。当前只提供本地可复现发布提交和真实失败信息，未声明GitHub发布完成。

### 文件白名单

- `research_m1/evidence/publication_allowlist.json`
- `research_m1/.gitignore`
- `research_m1/README.md`
- `research_m1/config/study.yaml`
- `research_m1/docs/CODEX_M1_CLEANROOM_TASK.md`
- `research_m1/docs/CODEX_M1_ROUND2_CLEANROOM_GITHUB_20261108.md`
- `research_m1/docs/M1_SINGLE_AUTHORITY.md`
- `research_m1/docs/ROUND2_EXECUTION_REPORT.md`
- `research_m1/docs/evidence_review.md`
- `research_m1/evidence/adjudication.json`
- `research_m1/evidence/reference_geometry_results.json`
- `research_m1/evidence/source_manifest.json`
- `research_m1/requirements.txt`
- `research_m1/src/m1_research/__init__.py`
- `research_m1/src/m1_research/__main__.py`
- `research_m1/src/m1_research/aip_reference.py`
- `research_m1/src/m1_research/aircraft_state.py`
- `research_m1/src/m1_research/config_loader.py`
- `research_m1/src/m1_research/generator.py`
- `research_m1/src/m1_research/geodesy.py`
- `research_m1/src/m1_research/procedure_reference.py`
- `research_m1/src/m1_research/scenario_sync.py`
- `research_m1/src/m1_research/smooth_uncertainty.py`
- `research_m1/src/m1_research/time_and_vertical.py`
- `research_m1/test_output.txt`
- `research_m1/tests/__init__.py`
- `research_m1/tests/test_aip_reference.py`
- `research_m1/tests/test_cleanroom_independence.py`
- `research_m1/tests/test_dual_scenario.py`
- `research_m1/tests/test_reference_geometry.py`
- `research_m1/tests/test_time_and_states.py`
- `research_m1/tests/test_uncertainty_and_status.py`

## 停止与未决

完成此次有限工作即停止。后续只待：2024程序与2025机场/导航台相容性；16R编码半径/定位点/LTP/高度限制；16L RNAV接入和高度/FAP/斜距基准；机型性能包线；真实误差数据与sigma/tau标定。未因缺证据发明新模型或降低Gate。
