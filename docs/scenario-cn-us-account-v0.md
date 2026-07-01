# S0/S1/S1.1/S2 中美双市场场景验证

本文件用于 iPhone 14 + Shadowrocket 实机测试。S0/S1/S1.1/S2 都不是最终配置，也不是 DNS 绝对隐私方案。

## 目标

- 中国本地体验：微信、支付宝、淘宝、小红书、抖音、B 站、高德、Apple 基础服务尽量保持本地 CDN 速度。
- 海外账号侧：TikTok、Instagram、YouTube、X、Facebook、ChatGPT/Claude 走美国代理。
- 未知流量：由 `FINAL,PROXY` 兜底。

## 配置文件关系

S0/S1/S1.1/S2 有两层文件：

- 公开规则模板：`configs/S0-scenario-cn-us-account-aggressive-v0.conf`、`configs/S1-scenario-cn-us-lazy-rule-v0.conf`、`configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf` 或 `configs/S2-scenario-cn-us-strict-app-whitelist-v0.conf`，只包含 `[General]`、`[Host]`、`[Rule]`，不包含节点、代理组或订阅。
- 私有完整配置：由你的原始完整配置和公开模板合并生成，包含原始节点/代理组，不得进入仓库。

如果 Shadowrocket 只能选一个配置文件，不能直接导入公开 S0/S1/S1.1/S2 模板测试；必须使用私有完整配置。

## 本地私有合并

使用方式：

```powershell
python scripts\merge-s0-private-config.py --base "local\private-configs\你的原始完整配置.conf" --output "local\private-configs\S0-private-merged.conf"
```

如果激进海外 DoH 版本出现“中国 App 正常、海外账号侧断网”，改用保守 DNS 底座：

```powershell
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --preserve-general --output "local\private-configs\S0-default-conservative.conf"
```

如果保守 DNS 底座表现为“海外能打开，但 DNS 测试显示中国 DNS”，改测普通美国 DNS 退阶版：

```powershell
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --plain-us-dns --output "local\private-configs\S0-default-plain-usdns.conf"
```

如果要测试 DNS 查询强制走代理 DoH：

```powershell
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --proxy-doh --output "local\private-configs\S0-default-proxy-doh.conf"
```

如果 proxy DoH 不泄露但 YouTube 等流媒体明显变慢，测试 QUIC 阻断版：

```powershell
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --proxy-doh --block-quic --output "local\private-configs\S0-default-proxy-doh-quic.conf"
```

如果日志显示中国 App 仍会走代理，先重新生成 S0 模板，再测试中国本地域名 DIRECT 保护版：

```powershell
python scripts\build-s0-from-johnshall.py
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --proxy-doh --block-quic --output "local\private-configs\S0-default-proxy-doh-quic-direct.conf"
```

如果要测试 S1 lazy 规则增强版：

```powershell
python scripts\build-s1-from-lazy.py
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --template "configs\S1-scenario-cn-us-lazy-rule-v0.conf" --output "local\private-configs\S1-default-lazy-proxy-doh.conf"
```

如果要测试 S1.1 规则源治理增强版：

```powershell
python scripts\build-s1-1-stabilized.py
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --template "configs\S1-1-scenario-cn-us-lazy-stabilized-v0.conf" --output "local\private-configs\S1-1-default-lazy-stabilized.conf"
```

如果要测试 S2 严格中国 App 白名单版：

```powershell
python scripts\build-s2-strict-app-whitelist.py
python scripts\merge-s0-private-config.py --base "local\private-configs\desktop-import-2026-07-01\youtube-default.conf" --template "configs\S2-scenario-cn-us-strict-app-whitelist-v0.conf" --output "local\private-configs\S2-default-strict-app-whitelist.conf"
```

脚本行为：

- 只保留原始配置里的 `[Proxy]` 和 `[Proxy Group]` 节点/代理组段落。
- 不保留原始配置里的 `[URL Rewrite]`、`[MITM]` 或其他非代理段落。
- 用 S0/S1/S1.1/S2 模板替换 `[General]`、`[Host]`、`[Rule]`。
- 使用 `--template` 时，可以指定 S1 公开模板；不传时默认使用 S0 模板。
- 使用 `--preserve-general` 时，保留原始 `[General]`，只替换 `[Host]` 和 `[Rule]`。
- 使用 `--plain-us-dns` 时，保留原始 `[General]` 的基础参数，但将默认 DNS 改为 `8.8.8.8 / 1.1.1.1`。
- 使用 `--proxy-doh` 时，保留原始 `[General]` 的基础参数，但将默认 DNS 改为 `https://cloudflare-dns.com/dns-query#proxy` 和 `https://security.cloudflare-dns.com/dns-query#proxy`。
- 使用 `--block-quic` 时，在 `[Rule]` 最前插入 UDP 443 阻断，用于验证 QUIC/HTTP3 是否拖慢流媒体；S1 默认已使用 `block-quic = all-proxy`，通常不需要再叠加该参数。
- 默认只允许把私有合并结果写到 `local/private-configs/`；拒绝写进 `configs/`、`docs/`、`references/` 等公开区。
- 不打印节点内容，只输出段落统计。

## 导入方式

本地验证阶段：

1. 使用私有合并版 `S0-private-merged.conf` 或 `S1-default-lazy-proxy-doh.conf` 导入 Shadowrocket。
2. 确认它保留了原始配置里的美国节点/代理组。
3. 固定同一个美国节点或美国策略组。
4. Shadowrocket 首页“全局路由”选择“配置”。
5. 每次切换配置后，先断开 Shadowrocket，再重新连接。

公开链接启用后：

- 优先使用 GitHub Pages 公开链接作为 Shadowrocket 订阅地址。
- 如果 Pages 未启用，再使用 raw GitHub 链接。
- 注意：公开 S0 模板不含节点，公开链接只适合规则模板更新；私有完整配置仍需本地合并。
- 注意：公开 S1/S1.1 模板同样不含节点；S1.1 还依赖已登记的远程 blackmatrix7 `RULE-SET`，手机端需要能加载这些规则源。
- 注意：公开 S2 模板同样不含节点；S2 更安全但可能让未收录的中国 App 域名走代理。
- 老倪已确认 S1.1 本轮启用 GitHub Actions、公开链接、自动 Issue、确认后 PR 和远端推送；私有完整配置仍不得上传 GitHub。

## 测试步骤

1. 先在 Wi-Fi 下测试，记录出口国家/地区，不记录完整 IP。
2. 如果 Wi-Fi 基本可用，再用蜂窝网络复测。
3. 中国本地 App 测试：
   - 微信：消息、图片、小程序。
   - 支付宝：首页、付款码入口。
   - 淘宝/天猫：商品图、搜索。
   - 小红书：信息流图片和视频。
   - 抖音：视频加载。
   - B 站：视频加载。
   - 高德：地图搜索。
   - Apple 基础服务：App Store、iCloud 基础同步。
4. 海外账号侧测试：
   - TikTok、Instagram、YouTube、X、Facebook 至少各打开一次。
   - ChatGPT 或 Claude 至少打开一次。
   - 优先看 Shadowrocket 日志，确认相关域名命中 `PROXY`。
   - 如果日志不足，再用同节点下出口国家/地区和平台地区表现辅助判断。
5. DNS 测试网站只做辅助记录：
   - `dnsleaktest.com`
   - `ipleak.net`
   - `browserleaks.com/dns`
   - IPPure

## 判断标准

- 中国白名单域名使用中国 DNS 不算失败，这是 S0 的设计目标。
- 海外账号域名、未知域名、DNS 随机测试域名出现中国本地运营商 DNS，才算失败。
- 海外账号侧如果日志显示命中 `DIRECT`，算失败。
- 海外账号侧如果日志显示命中 `PROXY`，但平台仍提示异常，只记录现象，不直接判定配置失败。
- 若 S0 出现大面积断网，优先判断激进海外 DoH 底座不可用，不继续叠加参数。
- 若 S1 出现海外侧断网或规则失效，先回退到 S0 proxy DoH 版本，区分 lazy 远程 `RULE-SET` 加载问题和底层 DNS 问题。
- 若 S2 出现中国 App 可用但变慢，优先看日志补种子表；不要恢复 `GEOIP,CN,DIRECT` 或 lazy `DIRECT`。
- 若 S2 出现海外 App 直连，算严重失败，优先检查前置 `PROXY` 规则和 Shadowrocket 是否使用了正确配置。

## 记录模板

不要上传截图，不记录完整 IP、节点名、订阅链接、账号信息。

```text
测试日期：
网络：Wi-Fi / 蜂窝
Shadowrocket 版本：
节点国家/地区：美国

出口国家/地区：
DNS 测试站点显示的 DNS 国家/地区和服务商：

中国本地 App：
微信：
支付宝：
淘宝/天猫：
小红书：
抖音：
B 站：
高德：
Apple 基础服务：

海外账号侧：
TikTok 日志是否命中 PROXY：
Instagram 日志是否命中 PROXY：
YouTube 日志是否命中 PROXY：
X 日志是否命中 PROXY：
Facebook 日志是否命中 PROXY：
ChatGPT/Claude 日志是否命中 PROXY：

异常现象：
是否需要回退：
```

## 回退口径

- 如果私有合并版比原始完整配置更差，先回到原始完整配置，不继续叠参数。
- 如果激进版表现为中国 App 正常、海外账号侧断网，优先改测 `S0-default-conservative.conf`。
- 如果保守版海外可用但 DNS 显示中国，改测 `S0-default-plain-usdns.conf`。
- 如果普通美国 DNS 仍显示中国或不稳定，改测 `S0-default-proxy-doh.conf`。
- 如果 `S0-default-proxy-doh.conf` 不泄露但流媒体慢，改测 `S0-default-proxy-doh-quic.conf`。
- 如果日志显示中国 App 域名命中 `PROXY`，改测 `S0-default-proxy-doh-quic-direct.conf`。
- 如果只是中国 App 慢，优先补 `references/china-local-domain-seeds.txt`，再重新生成 S0。
- 如果海外账号侧误直连，优先补账号覆盖域名，再重新生成 S0。
- 如果 DNS 测试显示中国 DNS，但只发生在中国白名单域名，不算失败。
- 如果 S1 里 lazy 远程 `RULE-SET` 加载失败，先回退 `S0-default-proxy-doh-quic-direct.conf`；不要直接把 S1 判定为底层方案失败。
- 如果 S2 中国 App 走代理，先补 `references/china-local-domain-seeds.txt`，再重新生成 S2。
- 如果 S2 出现未收录域名走代理，这是设计结果，不算泄露；只有海外/未知域名直连才算失败。
