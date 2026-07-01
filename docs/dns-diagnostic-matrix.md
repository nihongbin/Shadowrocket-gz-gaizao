# D 组 DNS 诊断矩阵

本文件用于 A/B/C 三组全部失效后的第二轮诊断。D 组只用于定位根因，不是最终配置，不对外发布。

## 测试分组

| 组别 | 配置文件 | 目的 | 只验证什么 |
|---|---|---|---|
| D0 | `configs/D0-diagnostic-shadowrocket-default-control.conf` | Shadowrocket 官方默认控制组 | 默认配置下出口、DNS、可用性是什么样 |
| D1 | `configs/D1-diagnostic-minimal-foreign-doh.conf` | 最小规则 + 国外 DoH | 排除 A/C 国内 DoH 或大规则导致误判 |
| D2 | `configs/D2-diagnostic-minimal-foreign-doh-always-ip.conf` | D1 + `always-ip-address = true` | 单独验证该参数是否改变 DNS 表现 |
| D3 | `configs/D3-diagnostic-shadowrocket-default-always-ip.conf` | D0 + `always-ip-address = true` | 在不切换国外 DoH 的情况下单独验证该参数 |

## 固定条件

- 设备：同一台 iPhone 14。
- App：同一个 Shadowrocket 版本。
- 节点：同一个代理节点，测试期间不更换。
- 网络：先固定同一个 Wi-Fi；只有 Wi-Fi 能看出差异时，再用蜂窝复测。
- 操作：每组导入后，先断开 Shadowrocket，再重新连接。
- 隐私：只记录地区、服务商、数量和文字现象，不记录完整 IP，不上传截图。
- IPv6：老倪已强制关闭，本轮不把 IPv6 作为主要变量。

## 测试步骤

1. 导入 D0，选择同一个节点，断开并重新连接 Shadowrocket。
2. 打开 `ipinfo.io` 或 `ip.sb`，只记录出口国家/地区。
3. 打开 `dnsleaktest.com`，运行 Standard test，记录 DNS 服务商、国家/地区和数量。
4. 打开 `ipleak.net` 复核 DNS 结果。
5. 打开 `browserleaks.com/dns`，记录是否出现本地运营商 DNS。
6. 打开 `IPPure`，记录是否出现本地运营商 DNS。
7. 打开 Shadowrocket 日志，记录是否出现系统 DNS、`8.8.8.8:53`、`1.1.1.1:53`、DoH/DoT/DoQ 相关请求。
8. 打开一个国内网站、一个国外网站、App Store、支付/银行/地图类 App，记录是否明显异常。
9. 对 D1、D2、D3 重复 1-8。

## 记录模板

| 日期 | 网络 | 组别 | 出口地区 | DNS 服务商/地区/数量 | 是否显示本地运营商 DNS | Shadowrocket 日志观察 | 可用性问题 | 初步判断 |
|---|---|---|---|---|---|---|---|---|
| 2026-06-30 | Wi-Fi | D0 | 未记录 | `dnsleaktest.com` 和 `ipleak.net` 未见泄露；`browserleaks.com/dns` 和 `IPPure` 显示泄露 | BrowserLeaks DNS 和 IPPure 显示泄露 | 日志未出现 `system`、硬编码 DNS、DoH/DoT/DoQ 关键词 | 未记录 | D0 为混合结果，需用 D1/D2 判断是否为测试方法、浏览器 DNS 路径或默认 DNS 策略差异 |
| 2026-06-30 | Wi-Fi | D1 | 无法测试 | 无法打开测试网站 | 无法测试 | 未记录 | 网络近似断开 | D1 国外 DoH 最小配置不可用，不能作为有效 DNS 结果 |
| 2026-06-30 | Wi-Fi | D2 | 无法测试 | 无法打开测试网站 | 无法测试 | 未记录 | 网络近似断开 | D2 与 D1 一样不可用，无法判断 `always-ip-address` 是否有效 |
| 2026-06-30 | Wi-Fi | D3 | 出口正确 | 四个测试点均显示泄露；DNS 位置和服务商完全暴露 | 全部显示泄露 | 未记录 | 未记录 | D3 比 D0 更差，`always-ip-address = true` 暂不采纳 |
| 2026-06-30 | 蜂窝 | D0 | 未记录 | `dnsleaktest.com` 和 `ipleak.net` 未见泄露；`browserleaks.com/dns` 和 `IPPure` 显示泄露 | BrowserLeaks DNS 和 IPPure 显示泄露 | 日志未出现 `system`、硬编码 DNS、DoH/DoT/DoQ 关键词 | 未记录 | 与 Wi-Fi 一致，暂不优先怀疑单一网络环境 |
|  | 蜂窝 | D1 |  |  |  |  |  |  |
|  | 蜂窝 | D2 |  |  |  |  |  |  |
|  | 蜂窝 | D3 |  |  |  |  |  |  |

## 判定规则

- 如果 D0/D3 出口 IP 都不是代理节点：先排查 Shadowrocket 模式、节点选择和配置是否启用。
- 如果出口 IP 正常但三组 DNS 都显示本地运营商：重点怀疑 Shadowrocket DNS 路径或系统 DNS 回退。
- 如果 `dnsleaktest.com` 和 `ipleak.net` 通过，但 `browserleaks.com/dns` 或 `IPPure` 暴露：优先怀疑测试方法差异、浏览器 DNS 路径、随机域名解析路径或默认 DNS 策略边界，不直接判定整组配置全失效。
- 如果 D1 好于 A/C：A/C 可能因为国内 DoH 或大规则影响导致测试失败。
- 如果 D2 好于 D1：`always-ip-address = true` 进入可继续验证状态，但不能直接进入最终 v1。
- 如果 D1/D2 断网：不要继续用 D1/D2 判断 DNS 泄露，改用 D3 隔离 `always-ip-address = true`。
- 如果 D3 好于 D0：说明 `always-ip-address = true` 可能有诊断价值，但仍需确认 App Store、Apple 服务、支付/银行/地图可用性。
- 如果 D3 破坏国内 App、Apple 服务、支付/银行/地图：`always-ip-address = true` 暂不采纳。
- 如果 D3 比 D0 更差：确认 `always-ip-address = true` 不适合作为当前方向，停止围绕该参数继续叠加配置。

## 下一步出口

- 找到明确根因：把结论写入 `docs/research-notes.md`，再决定是否重做候选配置。
- 没有明确根因：继续保留 D 组为诊断材料，不产出最终配置。
