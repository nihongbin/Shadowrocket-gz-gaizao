# V5/S5 Release Runbook

## 当前产物

- 私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 公开 S5 SHA256：`80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`
- `manifest_revision`：`00CB8614DD7006F3A8336323C6A14E4DA78E566447552E8D5128D630005DE94E`
- 受控快照：`rulesets/v5/`，33 个源、6072 条有效规则。

## 本地生成和检查

```powershell
python scripts\build-v5-mvp-template.py
python -m unittest discover -s tests -v
python scripts\manage-v5-rulesets.py validate
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
```

## 可选私有合并

仅当用户的完整配置包含 `[Proxy]`、`[Proxy Group]` 和名为 `PROXY` 的代理组时使用：

```powershell
python scripts\merge-v5-private-config.py `
  --base local\private-configs\your-complete-shadowrocket.conf `
  --output local\private-configs\your-v5-private.conf
```

私有输出不得离开 `local/private-configs/`。

## 发布

获得老倪明确确认后：

1. 检查 `git diff` 和敏感信息。
2. 提交并推送 `main`。
3. 等待 `Validate V5 Governed Rules` 和 `Publish V5 Public Template` 完成。
4. 验证 S5 raw、S5 Pages、至少一个 raw 快照和 Pages 快照均返回 HTTP 200。
5. 验证 S5 raw/Pages SHA256 与本地一致，快照有效规则 hash 与注册表一致。

公开链接：

- raw：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- Pages：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf`
- raw 快照示例：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/rulesets/v5/youtube.list`
- Pages 快照示例：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/rulesets/v5/youtube.list`

最近一次线上验收：

- 收敛提交：`35739b1`
- GitHub Actions run：`29080423533`
- raw / Pages：HTTP 200
- 线上 SHA256：`12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`

以上是规则源治理前的历史验收记录。

规则源治理线上验收：

- 实现提交：`0eadf9c`
- Node 24 workflow 提交：`c60dc1f`、`70c35ea`
- Pages：run `29083150629`
- validation：run `29083016651`
- 无变化 monitor / apply：run `29083016958` / `29083016586`
- 模拟 Issue / 拒绝门：Issue #4、run `29083194225` / `29083221851`
- S5 raw / Pages：HTTP 200，SHA256 `80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`
- YouTube 快照 raw / Pages：HTTP 200，SHA256 `E9E44675390E8588B19589590A68C01CA570A57BDD4BE52B6DBA69DF5856269B`

## 上游变化闭环

1. 每日 monitor 无变化时不通知。
2. 收到 `[V5规则源监控] 上游变化或异常待确认` Issue 后先看增删样例。
3. 确认可进入测试 PR 时，授权成员单独一行评论 `/approve-v5-ruleset-update`。
4. 自动化重新拉取并测试；变化仍存在才创建 PR。
5. PR 不自动合并。按 `docs/v5-ruleset-governance.md` 决定手机测试范围。
6. 合并后 Pages 自动发布，相关 Issue 由 `Closes #N` 关闭。

## 回滚

- 规则行为异常时，手机先回滚到本地已实测 V5。
- 仓库回滚必须基于明确的 Git commit，不得从旧 S1/S2 文件重新拼接。
- 不得把私有 V5 上传到 GitHub 作为回滚文件。

## 红线

- 不公开节点、订阅、账号、代理组和私有 V5。
- 不绕过测试直接发布清单修改。
- 不在模拟 Issue 中执行批准，不手改快照或语义 hash。
- 不把上游更新直接当成 V5 已验证更新。
- 不把 DNS B、QUIC allow 或旧版本重新设为基盘。
- 不承诺绝对 DNS 隐私。
