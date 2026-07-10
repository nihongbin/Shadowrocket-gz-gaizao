# V5/S5 Research Notes

## 2026-07-10 单一主线收敛

- 当前唯一手机实测基盘是 `local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`。
- 基盘 SHA256 为 `D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`。
- 公开 S5 由 `references/v5-mvp/` 生成，不包含节点、订阅、账号或代理组。
- 本地 V5 与公开 S5 的路由语义一致；公开 S5 只把 33 个上游 `RULE-SET` URL 映射为本仓库受控快照 URL。
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

## 2026-07-10 规则源治理

- 33 个 blackmatrix7 列表已规范化为 `rulesets/v5/` 固定快照，共 6072 条有效规则。
- `ruleset-sources.json` 记录上游 URL、策略、公开快照 URL、语义 SHA256、规则数和 GPL-2.0 边界。
- S5 不再运行时直接跟随 blackmatrix7 `master`；私有 V5 文件及 SHA256 未改。
- 私有 V5 仍保留原上游 URL，只作为实测证据和故障回退基盘；它本身不是冻结后的公开运行产物。
- 每天北京时间 04:17 自动监控语义。只看有效规则集合，忽略注释、时间戳、顺序和重复项。
- 无变化不通知；变化、拉取异常或快照漂移创建/更新 GitHub Issue。
- 真实 Issue 经授权成员评论 `/approve-v5-ruleset-update` 后，自动化才重新拉取、测试并创建 PR；不会自动合并。
- 本地真实拉取演练结果为 0 变化；YouTube 内存模拟成功识别 1 条新增规则，且没有写仓库。
- 线上真实无变化监控、模拟 Issue 通知、模拟批准拒绝、无变化 apply、validation 和 Pages 镜像均已通过；模拟 Issue #4 已关闭，未创建 PR。

## 当前风险

- 固定快照可能暂时落后于上游，这是为稳定性保留的人工审查窗口。
- 首次切换到受控 URL 后仍需手机确认 Shadowrocket 能成功加载全部列表；本地静态一致不等于手机网络一定可达。
- Apple `17.0.0.0/8` 直连是体验取舍，可能向 Apple 暴露真实网络出口。
- S5 只能降低常见 DNS 泄露风险，不能承诺在所有 iOS、Shadowrocket、节点和网络组合下绝对不泄露。

## 后续维护原则

- 不凭品牌名猜域名，只采用真实日志证据。
- 新中国域名必须同时补 DIRECT 和 Host。
- 不确定归属先写入候选记录。
- 上游变化只进入 Issue 和待审 PR；手机实测和人工合并是正式更新的最后两道门。
