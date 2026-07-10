# Shadowrocket V5/S5 中美双市场规则

当前项目只保留一条主线：朋友实测最稳定的 V5，以及由它脱敏生成的 S5 公开模板。

目标是兼顾中国本地 App 体验与海外账号访问：确认过的中国服务使用 `[Host] + DIRECT`，海外账号、AI、流媒体、测试站和未知流量优先使用 `PROXY`。项目只表述为“降低常见 DNS 泄露风险，并提供验证流程”。

## 当前唯一版本

- 本地私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 当前公开 S5 SHA256：`80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`
- 当前 `manifest_revision`：`00CB8614DD7006F3A8336323C6A14E4DA78E566447552E8D5128D630005DE94E`
- 有效内容：`General=15`、`Rule=351`、`Host=381`

本地 V5 与公开 S5 的路由语义一致。唯一有意差异是 33 个 `RULE-SET` URL：私有 V5 保留当时实测的上游地址作为只读基盘，公开 S5 改为本仓库经人工治理的固定快照地址。策略、顺序和其他有效规则仍逐条核对。

## 目录

- `configs/`：只保存 S5 公开模板。
- `references/v5-mvp/`：中国 DIRECT、Host DNS、海外/AI/测试站 PROXY、远程 RULE-SET 和候选记录。
- `rulesets/v5/`：33 个经语义规范化的公开规则快照及 blackmatrix7 GPL-2.0 许可证副本。
- `scripts/build-v5-mvp-template.py`：从清单生成 S5。
- `scripts/manage-v5-rulesets.py`：快照校验、上游语义监控和人工批准后同步。
- `scripts/check-v5-consistency.py`：核对本地 V5 与公开 S5。
- `scripts/merge-v5-private-config.py`：可选的私有节点合并工具。
- `tests/`：生成和合并链回归测试。
- `local/private-configs/`：只保存当前私有 V5，不进入 Git。

## 使用方式

公开模板不包含节点。用户需要在 Shadowrocket 中自行配置节点或订阅，然后使用 S5 规则模板。

公开链接：

- GitHub Pages：<https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf>
- raw GitHub：<https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf>

S5 中的远程规则优先读取本仓库 raw 快照；GitHub Pages 同时发布相同快照作为公开镜像。公开模板和快照都不含节点或账号。

如果用户的完整配置把节点写在 `[Proxy]` 和 `[Proxy Group]` 中，可在本地合并：

```powershell
python scripts\merge-v5-private-config.py `
  --base local\private-configs\your-complete-shadowrocket.conf `
  --output local\private-configs\your-v5-private.conf
```

合并器要求存在名为 `PROXY` 的代理组，并拒绝把私有输出写到 `local/private-configs/` 之外。

## 维护流程

1. 每天北京时间 04:17 自动读取 33 个上游源，只比较有效规则集合。
2. 注释、更新时间、顺序或重复项变化不通知；真实增删或拉取异常才创建/更新 GitHub Issue。
3. 在真实监控 Issue 中审查报告。确认后由仓库 OWNER/MEMBER/COLLABORATOR 单独一行评论 `/approve-v5-ruleset-update`。
4. 自动化重新拉取当前上游、更新快照、重建 S5、运行测试并创建 PR；不会自动合并。
5. 人工审查 PR 和手机实测后再合并。合并才会更新 raw 和 Pages，相关 Issue 随合并关闭。
6. 中国 App 或海外 App 的本项目自维护域名仍只根据真实日志修改 `references/v5-mvp/`，不由第三方上游自动决定。

```powershell
python scripts\build-v5-mvp-template.py
python -m unittest discover -s tests -v
python scripts\manage-v5-rulesets.py validate
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
```

## 已知边界

- 中国白名单域名使用 `223.5.5.5` 或 `119.29.29.29` 是设计目标，不算 DNS 泄露失败。
- 海外、未知、AI 或测试站出现中国本地运营商 DNS 才是失败信号。
- S5 运行时只读取本仓库快照；上游变化在人工确认和合并前不会改变手机运行规则。
- 快照因此可能暂时落后于上游，这是为稳定性保留的审查窗口，不是同步故障。
- `17.0.0.0/8` 保留为 V5 的 Apple 直连体验设置，Apple 流量可能看到真实网络出口。
- 旧版本已从当前文件树删除，但仍可从 Git 历史追溯；不得直接恢复为当前基盘。

## 文档

- `docs/v5-mvp-user-test-feedback.md`：手机验收和反馈模板。
- `docs/v5-mvp-release-runbook.md`：生成、发布和回滚流程。
- `docs/v5-ruleset-governance.md`：上游监控、Issue 通知、批准和 PR 闭环。
- `docs/v5-test-iteration-notes.md`：已作废试验的历史结论。
- `docs/research-notes.md`：当前技术判断和维护边界。
- `docs/static-check-report.md`：当前静态检查结果。
