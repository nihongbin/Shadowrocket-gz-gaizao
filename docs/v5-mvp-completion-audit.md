# V5/S5 Completion Audit

审计日期：2026-07-10。

## 当前结论

项目已收敛为单一 V5/S5 主线：本地只保留已实测 V5，公开仓库维护与其路由语义一致的 S5，并把第三方运行时规则冻结到本仓库受控快照。

## 已完成

- V5 基盘 hash 已锁定。
- V5 规则已清单化到 `references/v5-mvp/`。
- S5 可由生成器稳定重建。
- 私有 V5 与公开 S5 有效段可自动核对。
- 公开模板不包含节点、订阅、账号或代理组。
- 私有合并器已改为 V5 专用，并锁死本地私有输出目录。
- Pages workflow 只发布 S5 和受控规则快照镜像，发布前执行测试、快照校验和生成检查。
- 33 个 blackmatrix7 规则源已建立固定快照、语义 hash、规则数量和 GPL-2.0 许可证边界。
- 每日语义监控、GitHub Issue 通知、授权后同步、测试后 PR 和禁止自动合并的闭环已在本地实现。
- 真实无变化和模拟 1 条新增规则两条路径均已本地演练通过。
- 旧 A/B/C/D、S0/S1/S1.1/S2 文件及自动化已移除。
- 用户反馈模板不要求截图、完整 IP、节点名、订阅或账号。

## 不属于“已解决”的事项

- 受控快照不会自动跟随上游，因此新规则在人工审查合并前会暂时滞后。
- 首次切换到本仓库快照 URL 仍需手机确认 Shadowrocket 规则集加载状态。
- Apple 直连仍是体验与网络身份暴露之间的取舍。
- DNS 结论仍需按 Wi-Fi、蜂窝、节点和 App 场景实测。

## 发布验收

- PASS - 收敛提交 `35739b1` 已推送到 `main`。
- PASS - GitHub Actions run `29080423533` 成功完成测试和 Pages 发布。
- PASS - raw GitHub 与 GitHub Pages 均返回 HTTP 200。
- PASS - raw、Pages 与本地 S5 SHA256 均为 `12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`。
- PASS - 旧 S1.1 公开文件已从 raw 和 Pages 移除。
- PASS - 旧 S1.1 Issue、PR 和远程自动化分支已收口。

以上是单一 V5/S5 收敛时的历史发布验收。本轮治理闭环追加完成：

- PASS - 快照治理提交 `0eadf9c` 和 Node 24 workflow 更新 `c60dc1f` / `70c35ea` 已推送。
- PASS - Pages run `29083150629`、validation run `29083016651`、无变化 monitor run `29083016958`、无变化 apply run `29083016586` 均成功。
- PASS - 模拟 monitor run `29083194225` 创建 Issue #4；模拟批准 gate run `29083221851` 正确跳过全部更新和 PR 步骤。
- PASS - Issue #4 已关闭，开放 PR 为 0。
- PASS - 当前 S5 本地/raw/Pages SHA256 均为 `80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`。
- PASS - YouTube 快照本地/raw/Pages SHA256 均为 `E9E44675390E8588B19589590A68C01CA570A57BDD4BE52B6DBA69DF5856269B`。
