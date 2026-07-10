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
- PASS - V5 与 S5 的 `RULE-SET` URL 按注册表身份归一化后，有效 `[Rule]` 路由语义相同，共 351 条。
- PASS - V5 与 S5 有效 `[Host]` 相同，共 381 条。
- PASS - `[Rule]` 段最后有效规则为 `FINAL,PROXY`。
- PASS - 中国 DIRECT 根域与 Host DNS 清单一一对应，共 190 个。

## 公开边界

- PASS - S5 不含 `[Proxy]`、`[Proxy Group]`、`[MITM]` 或 `[URL Rewrite]`。
- PASS - S5 不含节点 URI、订阅字段、账号、token、password、secret、API key 或 username。
- PASS - S5 保留 Cloudflare `#proxy` DoH，不含 DNS B Google fallback。
- PASS - S5 保留 `block-quic = all-proxy`，不含 QUIC allow。
- PASS - 文件头区分模板 CC BY-SA 4.0 与快照 GPL-2.0。
- PASS - S5 的 33 个 `RULE-SET` 全部指向本仓库受控 raw URL，不再直接引用 blackmatrix7 `master`。
- PASS - 当前公开 S5 本地 SHA256 为 `80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`。

## 自动化

- PASS - Pages workflow 发布 S5 和同版本受控快照镜像。
- PASS - Pages 发布前运行全部单元测试、快照校验和生成检查。
- PASS - 每日监控 workflow 只有 `contents: read` 和 `issues: write`，不能改仓库。
- PASS - 监控忽略注释、时间戳、顺序和重复项，只报告有效规则增删、拉取异常或快照漂移。
- PASS - 批准 workflow 校验真实监控 Issue、标签、精确命令和 OWNER/MEMBER/COLLABORATOR 身份。
- PASS - 批准 workflow 测试通过后只创建 PR；没有自动合并命令。
- PASS - PR/手动 validation workflow 覆盖全部公开生成和快照检查。
- PASS - 私有合并器只允许输出到 `local/private-configs/`，并要求名为 `PROXY` 的代理组。

## 本地命令

```powershell
python -m unittest discover -s tests -v
python scripts\manage-v5-rulesets.py validate
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
```

## 规则源本地演练

- PASS - 33 个快照与注册表一致，共 6072 条有效规则。
- PASS - 真实上游拉取结果：`OK`，语义变化 0，拉取异常 0，快照漂移 0。
- PASS - YouTube 模拟新增 1 条规则时报告 `CHANGED`，并明确禁止批准模拟结果。
- PASS - 两次演练只写系统临时目录，没有改私有 V5 或额外写仓库文件。

## 线上验收

- PASS - 收敛提交：`35739b1`。
- PASS - GitHub Actions `Publish V5 Public Template` run `29080423533` completed successfully。
- PASS - raw GitHub 返回 HTTP 200，SHA256 为 `12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`。
- PASS - GitHub Pages 返回 HTTP 200，SHA256 与本地 S5 一致。
- PASS - 旧 S1.1 raw 和 Pages 链接均返回 HTTP 404。
- PASS - 旧 S1.1 Issue #1、PR #2 和远程自动化分支已关闭或删除。

## 规则源治理线上验收

- PASS - 治理实现提交 `0eadf9c`、Node 24 workflow 更新 `c60dc1f` / `70c35ea` 已推送到 `main`。
- PASS - 最终 Pages workflow run `29083150629` 成功，发布 S5 和 33 个快照镜像。
- PASS - 独立 validation run `29083016651`、真实无变化 monitor run `29083016958`、无变化 apply run `29083016586` 均成功。
- PASS - Node 24 模拟变化 run `29083194225` 创建 Issue #4，报告 1 条 YouTube 模拟新增规则。
- PASS - 在模拟 Issue 输入批准命令后，gate run `29083221851` 拒绝继续；写仓库、更新、PR 和验证分支步骤全部跳过。
- PASS - Issue #4 已在验证后关闭；开放 PR 为 0，没有把模拟变化写入正式配置。
- PASS - S5 本地/raw/Pages SHA256 均为 `80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`。
- PASS - YouTube 快照本地/raw/Pages SHA256 均为 `E9E44675390E8588B19589590A68C01CA570A57BDD4BE52B6DBA69DF5856269B`。
- INFO - 官方 `actions/deploy-pages@v5` 仍输出一条其依赖的 `punycode` 弃用提示，但没有 Node 20 action 警告，发布结果成功且 hash 一致。
