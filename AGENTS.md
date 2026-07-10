# Shadowrocket V5/S5 工作规则

## 项目定位

本项目只维护一条当前主线：朋友实测最稳定的 V5 规则，以及由它脱敏生成的 S5 公开模板。

统一表述为“降低常见 DNS 泄露风险，并提供验证流程”。不得承诺“彻底解决 DNS 泄露”。

## 唯一基盘

- 本地私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 一致性口径：私有 V5 与公开 S5 的 `[General]`、`[Host]` 必须逐条一致；`[Rule]` 中上游 URL 与本仓库快照 URL 按同一注册表身份归一化后，其余策略、顺序和规则必须逐条一致。
- 节点、订阅、账号和代理组不得进入公开 S5。

旧 A/B/C/D、S0、S1、S1.1、S2、DNS B 和 QUIC allow 均已退出当前文件树，只保留在 Git 历史和 `docs/v5-test-iteration-notes.md` 的决策记录中，不得重新作为基盘。

## 目录约定

- `configs/`：只允许保存当前 S5 公开模板。
- `references/v5-mvp/`：S5 的唯一可维护清单来源。
- `rulesets/v5/`：V5 专用受控规则快照；blackmatrix7 派生内容按 GPL-2.0 单独保留许可证。
- `scripts/build-v5-mvp-template.py`：从清单生成 S5。
- `scripts/manage-v5-rulesets.py`：快照初始化、静态校验、语义监控和批准后同步入口。
- `scripts/check-v5-consistency.py`：核对本地 V5 与公开 S5 的有效内容。
- `scripts/merge-v5-private-config.py`：可选的私有节点合并工具，输出只能位于 `local/private-configs/`。
- `tests/`：V5/S5 生成、校验和合并回归测试。
- `local/private-configs/`：只保留当前私有 V5；必须被 `.gitignore` 忽略。
- `.github/workflows/pages.yml`：发布 S5 和受控快照镜像。
- `.github/workflows/v5-ruleset-monitor.yml`：每日语义监控；只能读取仓库并创建/更新 Issue。
- `.github/workflows/v5-apply-approved-update.yml`：仅接受授权确认，测试通过后创建 PR，不得自动合并。
- `.github/workflows/v5-validation.yml`：PR 和手动触发的公开产物回归检查。

## 修改规则

- 后续新增域名优先修改 `references/v5-mvp/`，不得直接手改最终 S5。
- 中国 `DIRECT` 域名必须同时存在于 `china-direct-domains.txt` 和 `china-host-dns.csv`。
- 测试站、海外账号、AI 和流媒体 `PROXY` 必须排在中国 `DIRECT` 前。
- `[Rule]` 段内最后有效规则必须是 `FINAL,PROXY`。
- 不采纳 DNS B Google fallback、QUIC allow、`always-ip-address = true` 或系统 DNS 回退。
- 任何会改变有效规则的修改都必须先生成、静态检查、手机实测，再决定是否发布。

## 远程规则边界

S5 的 33 个 `RULE-SET` 只允许引用本仓库 `rulesets/v5/` 快照。`ruleset-sources.json` 保存上游地址、策略、语义 hash 和规则数量。

- 语义 hash 只计算去注释、去空行、去重复、排序后的有效规则集合。
- 上游注释、更新时间、顺序和重复项变化不得创建正式更新。
- 上游真实规则增删只允许创建/更新 Issue；不得自动写正式配置。
- 只有 OWNER/MEMBER/COLLABORATOR 在真实监控 Issue 单独一行输入 `/approve-v5-ruleset-update`，才能触发更新 PR。
- PR 创建前必须重拉上游、重建 S5 并通过测试；PR 不得自动合并。
- 合并前仍需根据差异范围决定手机实测，不能把“上游变化”直接写成“V5 已验证更新”。

## 敏感信息边界

禁止提交或公开：

- 私有 V5 原文件
- 节点、订阅、账号、代理组
- token、密码、密钥、验证码
- 完整 IP、运营商、地理位置截图
- 可识别个人或服务账号的信息

## 红线

以下操作必须由老倪明确确认：

- 删除当前 V5 基盘或 Git 历史
- 修改 CI/CD、GitHub Actions、系统配置或密钥
- `git push`、强制推送或公开发布
- 把私有配置移动到公开目录

## 验证命令

```powershell
python -m unittest discover -s tests -v
python scripts\manage-v5-rulesets.py validate
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
git status --short
```

只有以上检查通过，并完成必要的手机实测后，才能把有效规则变更写成已验证结论。

2026-07-10 老倪已明确授权本轮新增 V5 快照、语义监控、Issue、批准后 PR、Pages/raw 发布和对应推送。该授权不自动覆盖未来新增或改变 CI/CD 的动作；后续仍按红线单独确认。
