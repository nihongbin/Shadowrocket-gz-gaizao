# V5/S5 Completion Audit

审计日期：2026-07-10。

## 当前结论

项目已收敛为单一 V5/S5 主线：本地只保留已实测 V5，公开仓库只维护与其有效规则一致的 S5。

## 已完成

- V5 基盘 hash 已锁定。
- V5 规则已清单化到 `references/v5-mvp/`。
- S5 可由生成器稳定重建。
- 私有 V5 与公开 S5 有效段可自动核对。
- 公开模板不包含节点、订阅、账号或代理组。
- 私有合并器已改为 V5 专用，并锁死本地私有输出目录。
- Pages workflow 只发布 S5，发布前执行测试和生成检查。
- 旧 A/B/C/D、S0/S1/S1.1/S2 文件及自动化已移除。
- 用户反馈模板不要求截图、完整 IP、节点名、订阅或账号。

## 不属于“已解决”的事项

- 远程 `master` RULE-SET 仍可能在本仓库未提交时变化。
- Apple 直连仍是体验与网络身份暴露之间的取舍。
- DNS 结论仍需按 Wi-Fi、蜂窝、节点和 App 场景实测。

## 发布验收

本次收敛提交推送后必须确认：

- GitHub Actions Pages workflow 成功。
- raw GitHub 返回 HTTP 200。
- GitHub Pages 返回 HTTP 200。
- raw、Pages 与本地 S5 SHA256 一致。
