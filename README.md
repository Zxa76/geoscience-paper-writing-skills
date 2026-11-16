# 油气地学科技论文写作技能

一组用于 Codex 的地学论文写作技能，覆盖沉积地质、地球物理和非常规油气，每个领域提供中文与英文入口。技能围绕作者的研究数据组织论证、检查领域证据链，并改善学术语言表达。

## 六个写作入口

| 研究方向 | 中文稿 | 英文稿 |
|---|---|---|
| 沉积地质 | `$sedimentary-geology-zh` | `$sedimentary-geology-en` |
| 地球物理 | `$geophysics-zh` | `$geophysics-en` |
| 非常规油气 | `$unconventional-petroleum-zh` | `$unconventional-petroleum-en` |

还提供 `$geoscience-paper-writing` 总入口，根据主要科学问题与目标稿件语言选择合适的领域。六个入口共享同级的 `geoscience-paper-writing` 目录，需要作为整套安装。

## 功能

- 支持论文提纲、初稿、结构重组、中文润色、英文润色和中英翻译。
- 涵盖沉积构造、旋回地层、古环境、核磁、岩石物理、地学AI、孔隙、吸附及非常规油气。
- 写作中区分观测事实、模型结果、文献证据和地质解释，保留原始数据、单位与论断强度。
- 针对中文和英文学术语体提供独立的术语、句段组织与不确定性表达规范。
- 可选连接自己的 Zotero Desktop 资料库，通过只读本地API检索题录；写作技能本身不依赖 Zotero。

## 安装

需要 Git 与 Python 3。克隆仓库后运行安装脚本：

```bash
git clone https://github.com/Zxa76/geoscience-paper-writing-skills.git
cd geoscience-paper-writing-skills
python scripts/install.py
```

安装脚本将七个目录复制到 `$CODEX_HOME/skills`；未设置 `CODEX_HOME` 时使用 `~/.codex/skills`。如果目标技能已存在，脚本会停止，避免覆盖已有内容。安装到其他位置可使用 `python scripts/install.py --destination PATH`。

安装后在新 Codex 聊天中调用，例如：

```text
使用 $geophysics-en，根据我提供的中文研究结果和图表起草英文讨论，保留数据与不确定性。
```

也可以使用总入口：

```text
使用 $geoscience-paper-writing，帮我选择适合的入口并重构这篇论文的引言。
```

如果新技能未显示，请检查安装目录；必要时重新打开 Codex。

## 可选：使用 Zotero

在 Zotero Desktop 启用本地 API 后，把 [示例配置](examples/zotero-config.example.json) 复制到 `~/.geoscience-writing/config.json` 并修改为自己的收藏分类。然后按照 [Zotero 说明](skills/geoscience-paper-writing/references/zotero.md) 生成本地索引并检索。

本仓库不附带个人 Zotero 资料、论文摘要或 PDF。默认只缓存题录；仅在用户明确选择时才将摘要保存到本机。配置和索引位于用户主目录，不应提交到公开仓库。题录与摘要不能替代原文核查；工具不会训练模型参数。

## 使用边界

技能提供写作流程与证据检查，研究结论、样品和数据须由作者提供或从可靠来源核实。不要把文献结论写成自己的实验结果，也不要用单个地球化学指标直接证明某种地质成因。

## 验证

```bash
python -m unittest discover -s tests -v
```

## 许可证

[MIT License](LICENSE)。
