# V5/S5 Static Check Report

最后更新：2026-07-10。

本报告只证明本地文件、生成链和公开模板的静态状态，不替代 iPhone 实机验证。

## 基盘

- PASS - 本地私有目录只保留 `S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`。
- PASS - V5 SHA256 为 `D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`。
- PASS - `configs/` 只保留 `S5-scenario-cn-us-v5-mvp-v0.conf`。
- PASS - 私有 V5 被 `.gitignore` 忽略，没有进入待提交列表。

## 一致性

- PASS - V5 与 S5 有效 `[General]` 相同，共 15 条。
- PASS - V5 与 S5 有效 `[Rule]` 相同，共 351 条。
- PASS - V5 与 S5 有效 `[Host]` 相同，共 381 条。
- PASS - `[Rule]` 段最后有效规则为 `FINAL,PROXY`。
- PASS - 中国 DIRECT 根域与 Host DNS 清单一一对应，共 190 个。

## 公开边界

- PASS - S5 不含 `[Proxy]`、`[Proxy Group]`、`[MITM]` 或 `[URL Rewrite]`。
- PASS - S5 不含节点 URI、订阅字段、账号、token、password、secret、API key 或 username。
- PASS - S5 保留 Cloudflare `#proxy` DoH，不含 DNS B Google fallback。
- PASS - S5 保留 `block-quic = all-proxy`，不含 QUIC allow。
- PASS - 文件头包含来源、CC BY-SA 4.0 和清单版本说明。

## 自动化

- PASS - Pages workflow 只发布 S5。
- PASS - Pages 发布前运行全部单元测试和 `build-v5-mvp-template.py --check`。
- PASS - 旧 S1.1 监控和审批 workflow 已移除。
- PASS - 私有合并器只允许输出到 `local/private-configs/`，并要求名为 `PROXY` 的代理组。

## 本地命令

```powershell
python -m unittest discover -s tests -v
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
```

## 线上验收

- PASS - 收敛提交：`35739b1`。
- PASS - GitHub Actions `Publish V5 Public Template` run `29080423533` completed successfully。
- PASS - raw GitHub 返回 HTTP 200，SHA256 为 `12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`。
- PASS - GitHub Pages 返回 HTTP 200，SHA256 与本地 S5 一致。
- PASS - 旧 S1.1 raw 和 Pages 链接均返回 HTTP 404。
- PASS - 旧 S1.1 Issue #1、PR #2 和远程自动化分支已关闭或删除。
