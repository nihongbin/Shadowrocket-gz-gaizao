# Johnshall 白名单来源说明

## 来源

- 仓库：`https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- 分支：`release`
- S0 使用文件：`sr_top500_whitelist.conf`
- Raw 地址：`https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/release/sr_top500_whitelist.conf`

## 采纳范围

- S0 读取上游 `[Rule]` 主体，保留可解析的 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD`、`IP-CIDR`、`IP-CIDR6`、`GEOIP` 规则。
- 策略名统一为 `DIRECT` / `PROXY`。
- 上游 `FINAL` 不直接保留，S0 统一在文件末尾写入 `FINAL,PROXY`。
- Johnshall 只作为 `[Rule]` 主体来源，不等于纯中国白名单。

## 排除范围

- 不采用 `sr_cnip_ad.conf` 作为 S0 主体。
- 不采用广告版本。
- 不引入广告拦截主体、MITM、URL Rewrite。
- 不把全部 `DIRECT` 规则用于 `[Host]`。
- 不保留额外远程 `RULE-SET` 依赖，避免手机端再拉取第三方规则源。

## Host 生成边界

- `[Host]` 只从中国本地域名池生成。
- 中国本地域名池包括：
  - `references/china-local-domain-seeds.txt` 中的人工种子表。
  - Johnshall 中明确的 `.cn` 直连域名。
- 海外账号覆盖域名不得进入 `[Host]`，即使它们出现在 Johnshall 的 `DIRECT` 规则里。

## 许可证

Johnshall 上游使用 Creative Commons Attribution-ShareAlike 4.0 International License。若未来公开发布 S0 配置，必须保留署名和相同协议说明。

## 稳定元数据

生成配置只写稳定元数据：

- 上游 URL
- 上游 SHA256
- 规则数量
- 许可证说明

不写当前运行时间，避免上游无变化时产生无意义差异。
