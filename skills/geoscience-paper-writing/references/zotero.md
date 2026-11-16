# 可选：本地 Zotero 文献索引

本套件不附带个人文献库、题录、摘要或 PDF。写作本身不依赖 Zotero；需要结合个人文献库时，可使用系统提供的 Zotero 工具，或使用此目录中的 `../scripts/zotero_catalog.py`。

## 配置

在 Zotero Desktop 启用本地 API，保持 Zotero 运行。复制仓库中的 `examples/zotero-config.example.json` 到用户主目录下的 `.geoscience-writing/config.json` 并按自己的收藏分类修改，或调用时通过 `--config` 指定独立配置。示例中的中文类名只是初始模板，不要求使用者具有相同分类；安装后的技能不需要保留该仓库相对路径。

`root` 和 `groups` 各项可以是名称字符串，或 `{"name":"收藏名称","key":"ABCDEFGH"}` 对象。名称按大小写和完整字符精确匹配；分类只在指定根收藏的后代中查找。同名存在多个匹配时，填写对应 Zotero 收藏 key 消除歧义；根收藏亦可指定 key。脚本会遍历指定小类的下级收藏。三个 domain 键为 `sedimentary`、`geophysics`、`unconventional`，不需要某一分类时可使用空数组。

## 刷新、查看、检索

把 `<script>` 替换成安装目录的 `geoscience-paper-writing/scripts/zotero_catalog.py` 绝对路径，以下命令适用于安装了 Python 3 的 Windows、macOS 和 Linux：

```text
python -X utf8 <script> refresh
python -X utf8 <script> inventory
python -X utf8 <script> search adsorption --domain unconventional --language en --limit 8
python -X utf8 <script> item ABCDEFGH
```

`refresh` 仅使用 `127.0.0.1:23119` 的本地只读 GET API；收集所有数据成功后才原子替换旧快照，失败不覆盖旧快照。默认数据文件是用户主目录 `.geoscience-writing/catalog.json`，配置、快照和生成的文献数据不属于公开仓库。`--data` 可覆盖快照路径，`--config` 可覆盖配置路径，两个参数放在子命令之前。

默认只存题录。明确需要时，`refresh --include-abstracts` 才把摘要存于本地索引；这些摘要可能受版权保护且包含敏感资料，不要提交、公开或再分发。`search --abstracts` 会在输出中显示本地已存摘要。检索按空格分词且各词均需匹配，并按题目和分类相关性排序。

## 语言、证据与安全

语言字段与标题字符共同确定 `zh`、`en` 或 `unknown`。无语言字段的拉丁字母标题仅推断为英文，可能是其他西文；中文标题和英文语言字段冲突会标记 `language_conflict`，必须核对后再作为语言范文。文献语言不限定稿件语言，相关的另一语种论文仍可用于科学证据。未来年份可能是预出版卷期，需查证。

条目按 Zotero item key 去重，跨领域可重复使用；引用时按 DOI/标题复核不同 key 是否重复。题录和摘要不能证明已经读过全文，也不能支撑未在摘要明确出现的实验数值和方法细节；需要时在获得用户授权后只读相关原文。引用应保留真实作者、题名和来源，不凭题录推断证据。

本工具不读取全文或附件、不修改 Zotero 收藏、条目或标签，也不上传数据。若本地 API 未启用或不可用，请先在 Zotero 中检查本地 API 设置；离线时已有快照仍可供 `inventory` 和 `search` 使用。
