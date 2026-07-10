# V5/S5 Research Notes

## 2026-07-10 单一主线收敛

- 当前唯一手机实测基盘是 `local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`。
- 基盘 SHA256 为 `D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`。
- 公开 S5 由 `references/v5-mvp/` 生成，不包含节点、订阅、账号或代理组。
- 本地 V5 与公开 S5 的 `[General]`、`[Rule]`、`[Host]` 有效内容逐条一致。
- 旧 A/B/C/D、S0、S1、S1.1、S2 配置、生成脚本和自动化已从当前文件树删除。
- 旧试验仍可通过 Git 历史追溯；DNS B 和 QUIC allow 的无效结论继续记录在 `v5-test-iteration-notes.md`。
- 收敛提交 `35739b1` 已发布；raw 与 Pages 均返回新 S5 hash，旧 S1.1 链接已失效。

## 当前底层逻辑

- Cloudflare DoH 使用 `#proxy`，避免海外/未知解析直接暴露给本地运营商。
- 中国 App 根域通过 `[Host]` 指向 `223.5.5.5` 或 `119.29.29.29`，同时配套 `DIRECT`。
- 测试站、海外账号、AI、流媒体和海外 SDK 前置 `PROXY`。
- 中国本地保护规则排在远程规则之前。
- `GEOIP,CN,DIRECT` 保留为中国体验兜底。
- `[Rule]` 段最后使用 `FINAL,PROXY`。

## 已验证事实

- V5 是朋友当前反馈最稳定的版本。
- DNS B 未观察到 Google fallback 被触发，不能证明速度改善。
- QUIC allow 未证明速度改善，因此不进入基盘。
- 海外 App 首次慢、再次打开快更接近冷启动、缓存、蜂窝链路或节点时段问题，不能只凭一次卡顿修改规则。

## 当前风险

- 33 个远程 `RULE-SET` 使用 blackmatrix7 `master` 地址，内容可能独立于本仓库更新。
- 远程规则变化目前没有真正冻结到人工确认之后，因此不能把“仓库模板没改”等同于“手机运行规则没变”。
- Apple `17.0.0.0/8` 直连是体验取舍，可能向 Apple 暴露真实网络出口。
- S5 只能降低常见 DNS 泄露风险，不能承诺在所有 iOS、Shadowrocket、节点和网络组合下绝对不泄露。

## 后续维护原则

- 不凭品牌名猜域名，只采用真实日志证据。
- 新中国域名必须同时补 DIRECT 和 Host。
- 不确定归属先写入候选记录。
- 远程规则治理应优先考虑固定快照或固定 commit，但这会改变运行依赖，必须单独计划和实机验证。
