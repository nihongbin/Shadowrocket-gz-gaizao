# S5 V5 MVP 完成度审计

审计日期：2026-07-03

本文件按原始目标逐项核对当前状态。结论先行：S5 V5 MVP 本地产品化、公开模板、私有合并闭环、raw GitHub 链接、GitHub Pages 链接和用户反馈流程均已完成并验证。

## 基盘确认

- 要求：必须以 V5 私有配置为唯一基盘。
- 文件：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 当前 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 状态：完成。

## V5 清单化

- 要求：中国 App / 中国服务 DIRECT 域名清单。
- 证据：`references/v5-mvp/china-direct-domains.txt`
- 状态：完成。

- 要求：中国 Host DNS 清单。
- 证据：`references/v5-mvp/china-host-dns.csv`
- 状态：完成。

- 要求：海外强制 PROXY 清单。
- 证据：`references/v5-mvp/overseas-proxy-rules.txt`
- 状态：完成。

- 要求：AI / 流媒体 / 测试站保护清单。
- 证据：`references/v5-mvp/ai-proxy-rules.txt`、`references/v5-mvp/test-site-proxy-rules.txt`
- 状态：完成。

- 要求：远程 RULE-SET 注册表。
- 证据：`references/v5-mvp/remote-rulesets.csv`
- 状态：完成。

- 要求：候选观察清单。
- 证据：`references/v5-mvp/candidate-observations.md`
- 状态：完成。

## 自动生成脚本

- 要求：从清单生成公开 V5 MVP 规则模板。
- 证据：`scripts/build-v5-mvp-template.py`
- 验证：`python scripts\build-v5-mvp-template.py --check`
- 当前输出 SHA256：`B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`
- 状态：完成。

## 公开模板

- 要求：新增公开模板，不含节点、订阅、账号、代理组。
- 证据：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 检查结论：不含 `[Proxy]`、`[Proxy Group]`、节点 URI、token/password/secret 字段。
- 状态：完成。

## 私有合并闭环

- 要求：用户用自己的完整 Shadowrocket 配置 + V5 公开模板生成本地私有完整配置。
- 证据：`scripts/merge-s0-private-config.py --v5-mvp`
- 验证：`python scripts\merge-s0-private-config.py --base local\private-configs\desktop-import-2026-07-01\S0-private-merged.conf --v5-mvp --dry-run`
- 输出限制：只允许写入 `local/private-configs/`。
- 状态：完成。

## 自动更新和发布闭环

- 要求：接入 GitHub Pages / raw GitHub 公开模板更新。
- raw GitHub：S5 模板提交并推送到 `main` 后，raw 链接自然可用。
- GitHub Pages：`.github/workflows/pages.yml` 已加入 S5 模板发布项。
- raw GitHub 验证：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf` 返回 HTTP 200，SHA256 为 `B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`。
- GitHub Pages 验证：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf` 返回 HTTP 200，SHA256 为 `B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`。
- GitHub Actions 验证：`Publish Public Templates` run `28637570862` completed with success.
- 状态：完成。

## 用户反馈维护流程

- 要求：新增 MVP 用户测试文档或反馈模板，不收集敏感截图、完整 IP、节点名、订阅、账号。
- 证据：`docs/v5-mvp-user-test-feedback.md`
- 状态：完成。

## 文档同步

- 要求：README、research notes、static check 或相关文档同步当前 MVP 状态。
- 证据：
  - `README.md`
  - `AGENTS.md`
  - `docs/research-notes.md`
  - `docs/static-check-report.md`
  - `docs/v5-mvp-release-runbook.md`
  - `docs/v5-mvp-user-test-feedback.md`
- 状态：完成。

## 当前剩余动作

无。后续只在用户反馈或清单变更时进入维护流程。
