# 上游差异和采纳边界

本文件说明第一阶段为什么不直接采用某个现成仓库，而是先做 A/B/C 验证。

## 上游样本

| 来源 | 文件 | 当前用途 |
|---|---|---|
| Johnshall/Shadowrocket-ADBlock-Rules-Forever | `sr_cnip_ad.conf` | A 组基线，也是 C 组主体来源 |
| NZNL31/Shadowrocket-Ad-DNS-Leak-Rules | `a-nomad.conf` | B 组候选参考样本 |
| colin-chang 原版 a-nomad | `references/colin-chang-a-nomad.conf` | 追溯 NZNL31 README 提到的原版来源 |

## Johnshall 原版

保留：

- 国内外划分 + 去广告的主逻辑。
- `GEOIP,CN,DIRECT` 和 `FINAL,proxy` 的整体分流方向。
- 原有规则主体和广告过滤主体。
- 原有 DoH：`dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query`。

不足：

- 只有基础 DNS 设置，没有形成 DNS 泄露验证闭环。
- 没有显式设置 `dns-fallback-system = false`。
- 没有显式设置 `dns-direct-system = false`。
- 没有显式设置 `dns-direct-fallback-proxy = true`。
- 没有拦截常见硬编码明文 DNS 的候选项。

## NZNL31 / a-nomad 样本

可作为候选参考：

- `dns-fallback-system = false`
- `dns-direct-system = false`
- `dns-direct-fallback-proxy = true`
- `ipv6 = false`
- `prefer-ipv6 = false`

暂不直接采纳：

- 完整 `a-nomad` 策略组。
- 14 万行 `DOMAIN-SUFFIX` 结构。
- 多个远程规则源依赖。
- `dns-server = system`，除非实机验证证明它比 DoH/DoT 或其它方案更稳。

原因：

- v1 的目标是验证 DNS/IPv6/回退相关配置项，不是重做完整分流体系。
- 直接采用 14 万行结构会让问题定位变复杂。
- 多远程规则源会增加可用性和维护不确定性。
- `dns-server = system` 与防 DNS 泄露目标存在表面冲突，需要实机验证后才能判断。

## C 组候选配置

`configs/C-sr_cnip_ad_privacy_hardened_candidate.conf` 基于 Johnshall A 组生成，新增候选项：

```ini
prefer-ipv6 = false
dns-fallback-system = false
dns-direct-system = false
dns-direct-fallback-proxy = true
hijack-dns = 8.8.8.8:53,8.8.4.4:53,1.1.1.1:53,1.0.0.1:53
```

没有加入：

- `dns-server = system`
- NZNL31 完整策略组
- ACL4SSR 远程规则源
- `stun-response-ip`
- `stun-response-ipv6`

## WebRTC/STUN 边界

WebRTC/STUN 不作为 v1 配置实现范围。

- 不在 C 组配置里默认加入 STUN 伪造项。
- 文档只提醒用户确认 Shadowrocket 自带开关。
- WebRTC 测试只用于确认用户端开关是否生效，不作为本配置文件验收目标。

## 结论规则

第一阶段不直接得出最终配置。只有 A/B/C 实机验证后，才决定哪些候选项进入最终 v1。
