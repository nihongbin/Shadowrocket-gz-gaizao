# Shadowrocket V5/S5 中美双市场规则

当前项目只保留一条主线：朋友实测最稳定的 V5，以及由它脱敏生成的 S5 公开模板。

目标是兼顾中国本地 App 体验与海外账号访问：确认过的中国服务使用 `[Host] + DIRECT`，海外账号、AI、流媒体、测试站和未知流量优先使用 `PROXY`。项目只表述为“降低常见 DNS 泄露风险，并提供验证流程”。

## 当前唯一版本

- 本地私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 当前公开 S5 SHA256：`12B992F086738407E55653184DD6C7FF5FCA3740E96C4CB2B775ECDF45FB1B78`
- 有效内容：`General=15`、`Rule=351`、`Host=381`

本地 V5 与公开 S5 的三个有效段逐条一致。公开 S5 只增加来源、许可证和清单版本注释，不包含节点、订阅、账号或代理组。

## 目录

- `configs/`：只保存 S5 公开模板。
- `references/v5-mvp/`：中国 DIRECT、Host DNS、海外/AI/测试站 PROXY、远程 RULE-SET 和候选记录。
- `scripts/build-v5-mvp-template.py`：从清单生成 S5。
- `scripts/check-v5-consistency.py`：核对本地 V5 与公开 S5。
- `scripts/merge-v5-private-config.py`：可选的私有节点合并工具。
- `tests/`：生成和合并链回归测试。
- `local/private-configs/`：只保存当前私有 V5，不进入 Git。

## 使用方式

公开模板不包含节点。用户需要在 Shadowrocket 中自行配置节点或订阅，然后使用 S5 规则模板。

公开链接：

- GitHub Pages：<https://nihongbin.github.io/Shadowrocket-gz-gaizao/S5-scenario-cn-us-v5-mvp-v0.conf>
- raw GitHub：<https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf>

如果用户的完整配置把节点写在 `[Proxy]` 和 `[Proxy Group]` 中，可在本地合并：

```powershell
python scripts\merge-v5-private-config.py `
  --base local\private-configs\your-complete-shadowrocket.conf `
  --output local\private-configs\your-v5-private.conf
```

合并器要求存在名为 `PROXY` 的代理组，并拒绝把私有输出写到 `local/private-configs/` 之外。

## 维护流程

1. 根据真实日志确认域名归属。
2. 修改 `references/v5-mvp/` 对应清单。
3. 运行生成器更新 S5。
4. 运行全部测试和一致性检查。
5. 用本地 V5 对照手机实测。
6. 明确确认后再提交和发布。

```powershell
python scripts\build-v5-mvp-template.py
python -m unittest discover -s tests -v
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
```

## 已知边界

- 中国白名单域名使用 `223.5.5.5` 或 `119.29.29.29` 是设计目标，不算 DNS 泄露失败。
- 海外、未知、AI 或测试站出现中国本地运营商 DNS 才是失败信号。
- S5 仍运行时依赖 blackmatrix7 `master` 规则地址，上游可能在本项目没有提交时变化。
- `17.0.0.0/8` 保留为 V5 的 Apple 直连体验设置，Apple 流量可能看到真实网络出口。
- 旧版本已从当前文件树删除，但仍可从 Git 历史追溯；不得直接恢复为当前基盘。

## 文档

- `docs/v5-mvp-user-test-feedback.md`：手机验收和反馈模板。
- `docs/v5-mvp-release-runbook.md`：生成、发布和回滚流程。
- `docs/v5-test-iteration-notes.md`：已作废试验的历史结论。
- `docs/research-notes.md`：当前技术判断和维护边界。
- `docs/static-check-report.md`：当前静态检查结果。
