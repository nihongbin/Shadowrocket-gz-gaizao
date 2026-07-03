# S5 V5 MVP 发布闭环 Runbook

本文记录 S5 V5 MVP 从本地清单到公开链接的发布闭环。当前文档只是流程准备，不代表已经发布。

## 当前状态

- V5 唯一基盘：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- V5 基盘 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- S5 公开模板：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- S5 公开模板 SHA256：`B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`
- S5 清单目录：`references/v5-mvp/`
- Pages workflow 已加入 S5 模板发布项；raw GitHub 和 GitHub Pages 链接已完成线上验证。
- raw GitHub S5 链接：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- GitHub Pages S5 链接：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf`
- 已验证 S5 SHA256：`B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`

## 红线确认门

以下动作必须由老倪单独确认后才能执行：

- 修改 `.github/workflows/pages.yml`，把 S5 加入 GitHub Pages 发布产物。
- `git commit`
- `git push`
- 触发 GitHub Pages 公开发布。

没有确认前，只能做本地生成、检查、文档和私有合并验证。

## 本地生成闭环

检查 S5 模板是否由清单稳定生成：

```powershell
python scripts\build-v5-mvp-template.py --check
```

如果清单变更后需要重新生成公开模板：

```powershell
python scripts\build-v5-mvp-template.py
```

如果需要从当前已确认 V5 基盘重新同步清单：

```powershell
python scripts\build-v5-mvp-template.py --sync-manifests
```

注意：同步清单前必须确认 V5 基盘 hash 仍为：

```text
D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD
```

## 私有合并闭环

用户不能直接把公开 S5 模板当作完整 Shadowrocket 配置使用，因为公开模板不含节点和代理组。

私有完整配置生成命令：

```powershell
python scripts\merge-s0-private-config.py --base local\private-configs\your-complete-shadowrocket.conf --v5-mvp --output local\private-configs\your-v5-mvp-private.conf
```

输出必须只在：

```text
local/private-configs/
```

不得复制到：

```text
configs/
docs/
references/
GitHub Pages 公开目录
```

## raw GitHub 链接

只要 S5 模板提交并推送到 `main`，raw GitHub 链接会自然可用：

```text
https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf
```

raw 链接不需要修改 GitHub Actions，但 `git push` 本身是红线动作，必须确认后执行。

## GitHub Pages 链接

Pages workflow 需要在 public artifact 中发布 S5：

```text
configs/S5-scenario-cn-us-v5-mvp-v0.conf -> public/S5-scenario-cn-us-v5-mvp-v0.conf
```

发布后链接：

```text
https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf
```

修改 workflow 属于 CI/CD 红线，需要老倪确认。

## 上游和清单维护

S5 当前不自动跟随上游变化。后续维护流程：

1. 用户反馈问题，按 `docs/v5-mvp-user-test-feedback.md` 收集文字信息。
2. 只把确认归属的中国 App / 中国服务域名加入 `references/v5-mvp/china-direct-domains.txt` 和 `references/v5-mvp/china-host-dns.csv`。
3. 只把确认属于海外账号、AI、流媒体、测试站或海外 SDK 的域名加入对应 `PROXY` 清单。
4. 未确认归属的域名先写入 `references/v5-mvp/candidate-observations.md`。
5. 运行 `python scripts\build-v5-mvp-template.py --check`。
6. 生成模板、手机实测、再决定是否提交。

## 禁止事项

- 不公开 V5 私有完整配置。
- 不公开节点、订阅、账号、代理组。
- 不把 DNS B 或 QUIC allow 作为基盘。
- 不把旧 S1.1 / S2 当作当前主线。
- 不承诺“彻底防 DNS 泄露”，只表述为“降低常见 DNS 泄露风险，并提供验证流程”。
- 不把 `itdog.cn`、`ip.cn`、DNS 测试站、IP 查询站加入 `DIRECT`。
- 不把未确认归属的域名直接加入中国 `DIRECT`。
- 不把海外 AI、流媒体、海外账号域名加入 `DIRECT`。
