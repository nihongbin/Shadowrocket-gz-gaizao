# Shadowrocket V5/S5 工作规则

## 项目定位

本项目只维护一条当前主线：朋友实测最稳定的 V5 规则，以及由它脱敏生成的 S5 公开模板。

统一表述为“降低常见 DNS 泄露风险，并提供验证流程”。不得承诺“彻底解决 DNS 泄露”。

## 唯一基盘

- 本地私有 V5：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 私有 V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- 公开 S5：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 一致性口径：私有 V5 与公开 S5 的 `[General]`、`[Rule]`、`[Host]` 有效内容必须逐条一致。
- 节点、订阅、账号和代理组不得进入公开 S5。

旧 A/B/C/D、S0、S1、S1.1、S2、DNS B 和 QUIC allow 均已退出当前文件树，只保留在 Git 历史和 `docs/v5-test-iteration-notes.md` 的决策记录中，不得重新作为基盘。

## 目录约定

- `configs/`：只允许保存当前 S5 公开模板。
- `references/v5-mvp/`：S5 的唯一可维护清单来源。
- `scripts/build-v5-mvp-template.py`：从清单生成 S5。
- `scripts/check-v5-consistency.py`：核对本地 V5 与公开 S5 的有效内容。
- `scripts/merge-v5-private-config.py`：可选的私有节点合并工具，输出只能位于 `local/private-configs/`。
- `tests/`：V5/S5 生成、校验和合并回归测试。
- `local/private-configs/`：只保留当前私有 V5；必须被 `.gitignore` 忽略。
- `.github/workflows/pages.yml`：只发布 S5，不再发布或监控旧版本。

## 修改规则

- 后续新增域名优先修改 `references/v5-mvp/`，不得直接手改最终 S5。
- 中国 `DIRECT` 域名必须同时存在于 `china-direct-domains.txt` 和 `china-host-dns.csv`。
- 测试站、海外账号、AI 和流媒体 `PROXY` 必须排在中国 `DIRECT` 前。
- `[Rule]` 段内最后有效规则必须是 `FINAL,PROXY`。
- 不采纳 DNS B Google fallback、QUIC allow、`always-ip-address = true` 或系统 DNS 回退。
- 任何会改变有效规则的修改都必须先生成、静态检查、手机实测，再决定是否发布。

## 远程规则边界

S5 仍包含 blackmatrix7 `master` 分支远程 `RULE-SET`。这些地址可能在本项目没有提交时发生变化，因此：

- 上游变化不等于 V5 已验证更新。
- 不得只根据文件 hash 变化直接采纳结论。
- 海外误直连、中国误代理或速度异常时，必须结合 Shadowrocket 日志判断。
- 在没有完成固定快照方案前，文档必须持续披露该运行时依赖风险。

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
python scripts\build-v5-mvp-template.py --check
python scripts\check-v5-consistency.py
git status --short
```

只有以上检查通过，并完成必要的手机实测后，才能把有效规则变更写成已验证结论。
