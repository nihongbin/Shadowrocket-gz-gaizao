# V5 规则源治理闭环

## 为什么要做快照

原 V5 的 33 个 `RULE-SET` 直接引用 blackmatrix7 `master`。即使本项目配置没有改，上游也可能改变手机实际加载的规则。现在公开 S5 改为读取本仓库 `rulesets/v5/` 快照，已实测私有 V5 继续只读保留。私有 V5 仍使用原上游 URL，因此它是证据/回退基盘，不是冻结后的公开运行产物。

## 每日监控

- Workflow：`Monitor V5 Ruleset Semantics`
- 时间：每天北京时间 04:17；也可手动运行。
- 比较口径：去注释、去空行、去重复并排序后的有效规则集合。
- 不通知：上游注释、更新时间、顺序或重复项变化。
- 通知：真实规则新增/删除、上游拉取连续失败、本地快照与注册表漂移。
- 通知形式：GitHub Issue。GitHub 网页通知、App 推送和邮件是否同时收到，由仓库账号的 Watch/Notifications 设置决定。

没有变化时不创建 Issue，也不写仓库。

## 人工确认后开 PR

真实 Issue 标题为：`[V5规则源监控] 上游变化或异常待确认`。

1. 先查看每个源的新增、删除样例和策略是 `DIRECT` 还是 `PROXY`。
2. 只在判断值得进入测试分支后，由 OWNER/MEMBER/COLLABORATOR 单独一行评论：

```text
/approve-v5-ruleset-update
```

3. 自动化重新拉取当前上游。如果变化已经消失，不创建 PR。
4. 如果仍有变化，自动更新快照和语义 hash、重建 S5、运行测试并创建 `automation/v5-ruleset-update` PR。
5. 自动化不会合并 PR。审查差异并按影响范围完成手机测试后，人工决定合并或关闭。
6. PR 合并后更新 raw 和 Pages；PR 中的 `Closes #N` 关闭对应 Issue。

模拟 Issue 带有 `[模拟]` 标记，只验证通知链路，批准工作流会拒绝它。

## 手机实测边界

- `PROXY` 快照新增/删除：重点检查对应海外 App、流媒体、AI 或账号场景是否仍命中 `PROXY`。
- `DIRECT` 快照新增/删除：重点检查是否可能让海外域名直连，以及中国 App 是否误走代理。
- 任何规则异常先回滚到本地私有 V5，不把私有文件上传 GitHub。
- 统一表述为“降低常见 DNS 泄露风险，并提供验证流程”，不承诺绝对不泄露。

## 本地命令

```powershell
python scripts\manage-v5-rulesets.py validate
python scripts\manage-v5-rulesets.py monitor `
  --json-out "$env:TEMP\v5-monitor.json" `
  --markdown-out "$env:TEMP\v5-monitor.md"
python scripts\build-v5-mvp-template.py --check
python -m unittest discover -s tests -v
```
