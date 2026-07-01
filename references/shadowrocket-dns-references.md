# Shadowrocket DNS 参考来源

本文件只记录可验证资料来源和诊断假设，不把任何外部说法直接当成最终配置结论。

## 官方来源

- Apple App Store - Shadowrocket
  - 链接：https://apps.apple.com/pe/app/shadowrocket/id932747118?l=en-GB
  - 可用信息：官方描述确认 Shadowrocket 支持 DNS 请求日志、本地 DNS 映射，以及 DoH/DoT/DoQ 等安全 DNS 能力。
  - 限制：App Store 不提供完整 `.conf` 参数语义。

- Shadowrocket 官方账号 DNS Override 相关说明
  - 链接：https://x.com/ShadowrocketApp/status/1705278608580620659
  - 可用信息：提到 DNS Override、DoH/DoT/DoQ、`always-ip-address` 相关思路。
  - 限制：社交媒体内容不能替代实机验证。

## 社区来源

- LOWERTOP/Shadowrocket 社区手册
  - 链接：https://github.com/LOWERTOP/Shadowrocket
  - 可用信息：`dns-server` 主要用于解析直连域名；代理域名默认由代理服务器解析。`fallback-dns-server` 为空时可能使用系统 DNS。
  - 限制：社区手册不是官方完整规范，需要结合 Shadowrocket 日志验证。

- haritos90/shadowrocket-config-files 样本
  - 链接：https://github.com/haritos90/shadowrocket-config-files/blob/master/h90_main.conf
  - 可用信息：社区样本中常见 `fallback-dns-server`、`dns-direct-system = false`、`dns-direct-fallback-proxy = true`、`hijack-dns`、`always-ip-address = true` 等组合。
  - 限制：样本目标和本项目不同，不能直接照抄。

## 本轮诊断假设

- A/C 使用国内 DoH，DNS 测试站可能把国内 DoH 显示成异常结果；D1 改用国外 DoH 做对照。
- 如果测试域名命中 `PROXY`，DNS 查询可能由代理服务器完成，本机 `dns-server` 不一定是唯一变量。
- `always-ip-address = true` 可能改变解析路径，但也可能影响 CDN、国内 App、Apple 服务、支付/银行/地图可用性。
- 网上流传的 Cloudflare DNS 覆写 + 清空备用 DNS + 劫持 `8.8.8.8:53` 方案，在老倪当前环境复现失败；它只能作为排查 App 设置入口的线索，不能作为候选结论。
- 没有 Shadowrocket 日志证据前，不判断任何参数“有效”。
