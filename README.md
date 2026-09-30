# Kaggle Skills：有证据的比赛实验流程

当前推荐入口是 **[ml-competition-workflow](skills/ml-competition-workflow/SKILL.md)**。它将数据独立性、可学习监督、部署接入、方向停止和提交完整性放在模型试验之前，适用于Kaggle及其他机器学习比赛。

本次更新来自[Biohub 2026详细复盘](reports/biohub-2026/postmortem.zh-CN.md)。报告区分可核实事实、推断和未知；不将赛后公开资料当成赛时可得证据，也不承诺使用流程即可获奖。

## 使用

安装到Codex后，可以输入：

```text
使用 $ml-competition-workflow 审计当前比赛的数据、验证和已有结果，确定最有依据的下一轮实验。
```

或者指定阶段：

- “按这个skill检查为什么本地提升而线上退化。”
- “使用全部允许训练数据，制定并执行预算内的实验，报告实际消费覆盖。”
- “准备最终拟合和推送运行；不要比赛提交。”
- “复盘这次比赛，明确哪些方向应停止及下一场流程。”

skill会从当前阶段接续，不要求每次重跑完整审计；训练、上传、提交和自动监控仍遵守用户已有授权。

## 安装

需要现有Python 3解释器；新skill和安装器不需要Kaggle包，也不安装任何依赖。请使用项目指定解释器。

Windows PowerShell：

```powershell
$PythonExe = "C:\path\to\python.exe"
& $PythonExe .\scripts\install_workflow.py
```

将示例路径换成实际解释器。默认安装到`$CODEX_HOME/skills/ml-competition-workflow`；未设置CODEX_HOME则使用`~/.codex/skills/ml-competition-workflow`。

指定其他技能目录：

```powershell
& $PythonExe .\scripts\install_workflow.py --target-root "C:\path\to\skills"
```

安装器仅创建新安装或确认现有内容完全一致。遇到不同版本会停止，不删除、不覆盖，也不自动移动旧文件。发现列表未刷新时开启新会话。

也可手动将`skills/ml-competition-workflow`复制到目标技能目录，保持文件夹名不变。

## 文件结构

|路径|用途|
|---|---|
|`skills/ml-competition-workflow/SKILL.md`|当前比赛研究与执行入口|
|`skills/ml-competition-workflow/references/`|数据验证、实验决策、提交、记录模板、案例|
|`scripts/install_workflow.py`|不覆盖旧版本的跨平台安装器|
|`tests/test_install_workflow.py`|安装、重复调用、冲突和路径测试|
|`reports/biohub-2026/`|详细复盘、汇总证据与来源哈希|
|`validation/workflow-20261001.md`|技能结构检查及场景走查记录|

## 相对于旧工具的改进

原仓库擅长资料抓取、Notebook操作和提交账本。新skill补充了原流程中不足的研究判断：

1. 按患者/胚胎/地点等真实来源审计独立性与预训练暴露。
2. 区分允许数据池、实际唯一消费和重复监督曝光。
3. 在扩结构前确认难例可达、特征可辨、监督可学和后续可保留。
4. 将实现复现与最终效果分成两层验收。
5. 为无收益方向设置复审和停止条件，避免无穷诊断或同类微调。
6. 将Notebook完成、推送、提交和有效评分分别记录。
7. 验证隐藏规模资源和最终产物完整性，而非只看占位样本。

## 历史工具

根目录原`SKILL.md`、`commands/`、旧`references/`及Kaggle操作脚本保留作参考，未纳入新安装器的载荷。新入口不依赖它们。

旧`install.ps1`、`install.sh`及卸载脚本面向Claude Code，部分含覆盖或删除行为；它们不是当前推荐安装入口，本次未执行。需要Kaggle CLI工具时按具体任务检查当前API和授权，不直接照搬旧版本参数或自动监控流程。

## 验证

```powershell
& $PythonExe -m unittest discover -s tests -v
& $PythonExe scripts/install_workflow.py --help
```

测试使用独立新目录并保留产物，不自动清理。可以通过`KAGGLE_SKILLS_TEST_ROOT`指定测试产物父目录。结构验证使用Codex自带skill-creator的`quick_validate.py`；具体检查结果见验证记录。

本仓库不包含比赛图像、GT、权重、教师缓存或凭证。复盘中的模型成绩为注明日期和口径的历史记录，不代表最新或最终私榜结果。
