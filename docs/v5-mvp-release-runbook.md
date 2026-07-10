# V5/S5 Release Runbook

## 当前产物

- 私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 公开 S5 SHA256：`12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`

## 本地生成和检查

```powershell
python scripts\build-v5-mvp-template.py
python -m unittest discover -s tests -v
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
3. 等待 `Publish V5 Public Template` workflow 完成。
4. 验证 raw 和 Pages HTTP 状态及 SHA256。

公开链接：

- raw：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- Pages：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf`

最近一次线上验收：

- 收敛提交：`35739b1`
- GitHub Actions run：`29080423533`
- raw / Pages：HTTP 200
- 线上 SHA256：`12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`

## 回滚

- 规则行为异常时，手机先回滚到本地已实测 V5。
- 仓库回滚必须基于明确的 Git commit，不得从旧 S1/S2 文件重新拼接。
- 不得把私有 V5 上传到 GitHub 作为回滚文件。

## 红线

- 不公开节点、订阅、账号、代理组和私有 V5。
- 不绕过测试直接发布清单修改。
- 不把 DNS B、QUIC allow 或旧版本重新设为基盘。
- 不承诺绝对 DNS 隐私。
