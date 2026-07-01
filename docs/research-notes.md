# 调研记录

本文件记录暂时无法确认、暂不采纳或需要实机测试才能判断的项目。

## 已确认事实

- Johnshall `sr_cnip_ad.conf` 是国内外划分 + 去广告配置，适合作为 v1 基线。
- NZNL31 `a-nomad.conf` 基于 Johnshall 和 colin-chang 原版 a-nomad，并引入大量 `DOMAIN-SUFFIX` 规则和 ACL4SSR 远程规则。
- colin-chang 原版 `a-nomad.conf` 是 122 行级别的策略组和远程规则配置，不包含 Johnshall 的广告规则主体。

## 需要实机验证

- `dns-fallback-system = false` 是否能稳定阻止系统 DNS 回退。
- `dns-direct-system = false` 是否能阻止直连域名走系统 DNS，且不破坏国内网站可用性。
- `dns-direct-fallback-proxy = true` 是否改善直连解析失败场景，是否带来不必要代理。
- `hijack-dns` 是否能在 iPhone 实际 App 流量中拦截常见硬编码明文 DNS。
- `dns-server = system` 是否比 DoH 更稳。当前不进入 C 组，只有 B 组用于观察。

## 2026-06-30 实机反馈

- 老倪反馈：A/B/C 三组方案全部失效。
- 老倪补充：IPv6 已强制关闭，因此下一步先不把 IPv6 暴露作为主要失败方向。
- 当前缺少具体失败明细，不能判断是 DNS 测试显示本地运营商、WebRTC 暴露、分流不可用，还是 Shadowrocket 配置未按预期生效。
- 该反馈说明第一阶段 A/B/C 都不得进入最终 v1；下一步必须先补齐失败现象，再决定是否新增诊断组或重做候选配置。

## 下一步排查假设

- 如果三组出口 IP 都不是代理节点：优先排查节点选择、全局路由模式、配置是否真正启用。
- 如果出口 IP 正常但 DNS 显示本地运营商：优先排查 Shadowrocket DNS 行为、DNS 测试站点口径、直连域名解析路径。
- 如果只有 WebRTC 暴露：按项目边界先检查 Shadowrocket 自带开关，不把它算作 C 组配置失败。
- 如果国内外访问大面积异常：优先排查规则策略名、代理组选择、最终兜底策略是否匹配当前节点环境。

## 2026-06-30 外部资料检索

- Apple App Store 官方描述确认 Shadowrocket 支持 DNS 请求日志、本地 DNS 映射，以及 DoH/DoT/DoQ 等安全 DNS 能力；但 App Store 不提供完整 `.conf` 参数语义。
  - 来源：https://apps.apple.com/pe/app/shadowrocket/id932747118?l=en-GB
- 社区维护手册说明：`dns-server` 主要用于解析直连域名；代理域名默认由代理服务器解析。这个点会影响 DNS 泄露测试解读：测试域名如果命中 `Proxy`，本机 DNS 参数未必是唯一变量。
  - 来源：https://github.com/LOWERTOP/Shadowrocket
- 社区手册说明：如果 `fallback-dns-server` 为空，默认使用系统 DNS；若查询超时，可能触发备用解析路径。C 组虽然设置了 `dns-fallback-system = false`，但仍需要通过日志确认 Shadowrocket 实际是否执行该参数。
  - 来源：https://github.com/LOWERTOP/Shadowrocket
- Shadowrocket 官方账号曾发布 DNS Override 相关更新思路，包括遇到 DNS 劫持时使用 DoH/DoT/DoQ，并提到 `always-ip-address`。该项可能改变解析路径，但也可能带来 CDN 或分流副作用，不能直接进入正式候选。
  - 来源：https://x.com/ShadowrocketApp/status/1705278608580620659
- 社区配置样本常见做法是显式加入 `fallback-dns-server`、`dns-direct-system = false`、`dns-direct-fallback-proxy = true`、`hijack-dns`、`always-ip-address = true`，但不同样本之间目标差异很大，不能直接照抄。
  - 来源：https://github.com/haritos90/shadowrocket-config-files/blob/master/h90_main.conf

## 新诊断方向

- 新增 D 诊断配置时，先不要合并广告规则和大分流规则，只保留最小 `[General]`、DNS 参数、DNS 泄露测试域名和 `FINAL,PROXY`，用于确认 Shadowrocket DNS 参数是否真正生效。
- D 诊断配置需要分别测试两种 DNS 方向：一组使用国外 DoH/DoT，排除 A/C 国内 DoH 被测试站误判为泄露；另一组测试 `always-ip-address = true`，验证是否能处理本机 DNS 劫持，但必须观察 CDN 和国内可用性副作用。
- 所有新参数都只能进入诊断组，不能直接进入最终 v1。

## D 组诊断材料

- D0：`configs/D0-diagnostic-shadowrocket-default-control.conf`，Shadowrocket 官方默认控制组。
- D1：`configs/D1-diagnostic-minimal-foreign-doh.conf`，最小规则 + 国外 DoH。
- D2：`configs/D2-diagnostic-minimal-foreign-doh-always-ip.conf`，D1 + `always-ip-address = true`。
- D3：`configs/D3-diagnostic-shadowrocket-default-always-ip.conf`，D0 + `always-ip-address = true`，用于在不切换国外 DoH 的情况下隔离该参数。
- 诊断矩阵：`docs/dns-diagnostic-matrix.md`。
- 失败采集表：`docs/dns-failure-intake.md`。
- DNS 参考来源：`references/shadowrocket-dns-references.md`。

## 2026-06-30 D0 实机结果

- Wi-Fi：`dnsleaktest.com` 和 `ipleak.net` 通过，未看到泄露；`browserleaks.com/dns` 和 `IPPure` 显示泄露。
- 蜂窝：结果与 Wi-Fi 一致。
- Shadowrocket 日志：未出现预设关键词，包括 `system`、硬编码 DNS、DoH/DoT/DoQ 相关关键词。
- 初步判断：D0 不是全局失败，而是两个补充测试点暴露。因为 Wi-Fi 和蜂窝一致，暂不优先怀疑单一网络环境；原计划测试 D1/D2，但 D1/D2 已反馈为网络近似断开，后续改用 D3 隔离 `always-ip-address = true`。
- 注意：BrowserLeaks DNS 和 IPPure 的观察口径可能不同于 `dnsleaktest.com`、`ipleak.net`；当前不能只凭单类测试结果下最终结论。

## 2026-06-30 D1/D2 实机结果

- D1：测试网站无法打开，网络近似断开。
- D2：测试网站无法打开，网络近似断开。
- 初步判断：D1/D2 的国外 DoH 最小配置在当前环境不可用，不能用来判断 DNS 泄露是否改善；D2 也无法隔离 `always-ip-address = true` 的作用。
- 下一步：使用 D3 继续测试。D3 基于 D0，只增加 `always-ip-address = true`，用于排除国外 DoH 断网变量。

## 2026-06-30 D3 实机结果

- D3：出口正确，说明代理通道本身生效。
- DNS 测试结果：全部泄露，DNS 位置和服务商完全暴露。
- 对比 D0：D0 至少还有部分测试显示正确位置和服务商，同时混有暴露位置和服务商；D3 则变成全暴露。
- 初步判断：`always-ip-address = true` 在当前环境没有降低风险，反而放大 DNS 暴露表现；该参数暂不采纳，也不再围绕它继续叠加配置。
- 当前剩余问题：出口走代理但 DNS 仍走本地/系统路径，下一步应排查 Shadowrocket 模式、App 内 DNS/Override 设置、浏览器 DNS 路径，以及 iOS 系统级 DNS/VPN 配置冲突。

## 2026-06-30 外部 Cloudflare 覆写方案复现

- 老倪反馈：网上有人使用以下思路成功，但本机实测未成功。
  - DNS 覆写：`https://cloudflare-dns.com/dns-query`
  - DNS 覆写：`https://security.cloudflare-dns.com/dns-query`
  - 备用 DNS：清空
  - 劫持 DNS：`8.8.8.8:53`
- 初步判断：该方案不能直接作为本项目候选项；至少在当前环境，它没有解决 DNS 暴露。
- 需要区分两层设置：网上说的“DNS 覆写”更像 Shadowrocket App 内部设置项，不一定等同于 `.conf` 文件里的 `dns-server`。后续若继续排查，应先确认 App 设置页是否存在系统级覆写、备用 DNS、劫持 DNS 三个独立入口，以及配置文件导入后是否覆盖这些 App 设置。
- 当前不新增基于该方案的候选配置，避免重复走 D1/D2 的国外 DoH 断网路线。

## 2026-06-30 阶段收口结论

- 老倪判断：规则文件方向继续做意义不大，项目暂停。
- 当前证据支持该判断：A/B/C 全部失效；D1/D2 网络近似断开；D3 出口正确但 DNS 全部泄露；Cloudflare 覆写方案复现失败。
- 结论：不产出最终 v1，不继续叠加 `.conf` 参数，不公开发布。
- 如果未来继续，只应转向设备/应用设置链路：Shadowrocket App 内 DNS/Override 设置、iOS 系统 DNS/VPN 配置、浏览器 DNS 路径、其他 VPN/DNS App 冲突。

## 2026-07-01 S0 中美双市场方向

- 新方向不再把目标定义为“所有 DNS 测试网站完全不显示中国 DNS”，而是验证中国本地体验和海外账号侧稳定性之间的平衡。
- S0 目标：中国本地 App 使用中国本地域名池和国内 DNS 保持速度；海外账号侧和未知流量由美国代理兜底。
- Johnshall `sr_top500_whitelist.conf` 可以作为 `[Rule]` 主体来源，但不能无脑当作“中国白名单”。它包含中国域名，也可能包含可直连海外域名。
- `[Host]` 只从中国本地域名池生成，不从所有 `DIRECT` 规则生成。
- 中国本地域名池由 `references/china-local-domain-seeds.txt` 和 Johnshall 中明确的 `.cn` 直连域名组成；后期增删中国 App 域名只改种子表，不改脚本。
- 海外账号覆盖规则必须放在 Johnshall 主体规则之前，防止 TikTok、Instagram、YouTube、X、Facebook、Google、OpenAI、Claude 等账号侧域名被误直连。
- 博主 `a-nomad.conf` 不作为 S0 底座，只借鉴“规则优先级”和 `FINAL,PROXY` 兜底思路。
- 自动更新不写当前运行时间，只写上游 URL、上游 SHA256、规则数量和许可证说明，避免上游无变化时产生无意义差异。
- 当时 GitHub Actions、公开链接、自动写仓库仍属于红线动作；S0 只在文档中写待启用方案，未新增 workflow 文件。该边界后来在 S1.1 阶段由老倪单独确认解除。
- S0 公开模板不含节点和代理组。由于 Shadowrocket 只能选一个配置文件，手机实测必须生成本地私有合并版：保留原始完整配置中的节点/代理组，用 S0 覆盖 `[General]`、`[Host]`、`[Rule]`。
- 私有合并版不得进入仓库、不得记录节点内容、不得公开分享。

## 2026-07-01 S0 验收口径

- 中国白名单域名使用中国 DNS 是设计目标，不算失败。
- 海外账号域名、未知域名、DNS 随机测试域名出现中国本地运营商 DNS 才算失败。
- 海外账号侧优先通过 Shadowrocket 日志确认相关域名命中 `PROXY`；日志不足时，只用出口国家/地区和平台地区表现做辅助判断。
- 不记录完整 IP，不上传截图，不保存节点、订阅、账号或任何敏感信息。
- 如果激进海外 DoH 再次导致断网，本轮结论应是“激进 DNS 底座不可用”，回退到保守 DNS 底座，不继续叠加参数。

## 2026-07-01 S0 首轮实机反馈

- 老倪反馈：按 `default.conf` 合并出的 S0 测试文件，中国 App 正常能访问，海外账号侧/未知流量处于断网状态。
- 初步判断：`[Host]` 中国本地域名池方向大概率有效；断网集中在海外/未知侧，优先怀疑激进海外 DoH 底座导致代理侧解析失败。
- 该判断与 D1/D2 结果一致：国外 DoH 最小配置曾导致网络近似断开。
- 已新增保守合并模式：`scripts/merge-s0-private-config.py --preserve-general`，保留 `default.conf` 的 `[General]`，只替换 S0 `[Host]` 和 `[Rule]`。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S0-default-conservative.conf`。
- 该文件保留 `dns-server = system` 和 `fallback-dns-server = system`，最后一条仍为 `FINAL,PROXY`。

## 2026-07-01 S0 退阶 DNS 思路

- 老倪继续反馈：保守版海外能打开，但 DNS 测试仍显示中国 DNS。
- 新退阶思路：默认使用普通美国 DNS，不使用 DoH；只有命中中国本地域名池的域名才通过 `[Host]` 指定中国 DNS。
- 已新增 `scripts/merge-s0-private-config.py --plain-us-dns` 模式。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S0-default-plain-usdns.conf`。
- 该文件使用 `dns-server = 8.8.8.8, 1.1.1.1` 和 `fallback-dns-server = 8.8.8.8, 1.1.1.1`，并保持 `dns-direct-system = false`、`dns-fallback-system = false`、`dns-direct-fallback-proxy = true`。
- 验证目标：海外不再断网，DNS 测试不再显示中国运营商；中国 App 仍保持可用。

## 2026-07-01 S0 代理 DoH 思路

- 老倪指定新的 DNS 方案：`https://cloudflare-dns.com/dns-query#proxy` 和 `https://security.cloudflare-dns.com/dns-query#proxy`。
- 该方案与激进 DoH 的关键区别是 `#proxy`，目标是让 DNS 查询本身走代理通道，避免本地系统 DNS 介入。
- 已新增 `scripts/merge-s0-private-config.py --proxy-doh` 模式。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh.conf`。
- 该文件设置 `dns-server` 与 `fallback-dns-server` 为上述两个 `#proxy` DoH，并保持 `dns-direct-system = false`、`dns-fallback-system = false`、`dns-direct-fallback-proxy = true`。
- 验证目标：海外不再断网，DNS 测试不再显示中国运营商；中国 App 仍保持可用。

## 2026-07-01 S0 流媒体慢排查

- 老倪反馈：`S0-default-proxy-doh.conf` 不泄露，中国 App 速度可以，但 YouTube 等流媒体明显变慢。
- 规则检查显示 YouTube 主链路已在 Johnshall 规则前强制 `PROXY`，包括 `youtube.com`、`googlevideo.com`、`ytimg.com`、`gstatic.com`、`googleapis.com`。
- 下一步优先测试 QUIC/HTTP3 影响，而不是继续改 DNS 或扩大中国白名单。
- 已新增 `scripts/merge-s0-private-config.py --block-quic` 模式，在 `[Rule]` 最前插入 `AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP`。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh-quic.conf`。
- 该文件保留 `#proxy` DoH，不改变 `[Host]`，只额外阻断 UDP 443，用于验证流媒体慢是否由 QUIC 通过代理表现差导致。

## 2026-07-01 S0 中国 App 误走代理修正

- 老倪反馈：从 Shadowrocket 日志看，中国 App 会走代理，说明分流不够精准。
- 根因修正：`[Host]` 只决定解析，不决定路由；此前中国本地域名池只生成 `[Host]`，没有统一生成前置 `DIRECT` 规则，未被 Johnshall 收录的中国 App 域名会掉到 `FINAL,PROXY`。
- 已更新 `scripts/build-s0-from-johnshall.py`：中国本地域名池同时生成 `[Host]` 和 `[Rule]` 中的 `DIRECT` 保护规则。
- 新规则顺序为：QUIC 阻断、海外账号 `PROXY`、中国本地域名 `DIRECT`、Johnshall 主体、`FINAL,PROXY`。
- 已重新生成 `configs/S0-scenario-cn-us-account-aggressive-v0.conf`，文件头显示 `china_direct=98`。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh-quic-direct.conf`。
- 检查确认：`wechat.com`、`xiaohongshu.com`、`douyin.com`、`bilibili.com`、`taobao.com` 已在 Johnshall 主体前命中 `DIRECT`；`youtube.com`、`googlevideo.com` 仍在前置账号规则中命中 `PROXY`。

## 2026-07-01 S1 lazy 规则增强方向

- S1 目标：保留 S0 已验证的 `#proxy` DoH、中国本地 `[Host]`、中国本地 `DIRECT` 保护、海外/未知 `FINAL,PROXY` 兜底，同时接入 Johnshall `lazy.conf` 的成熟 `[Rule]` 主体。
- 关键边界：不整包复制 `lazy.conf`，只抽取 `[Rule]`；不采用 lazy 的 `[General]`、`[Host]`、`[URL Rewrite]`、`[MITM]`。
- 已新增 `scripts/build-s1-from-lazy.py`，生成 `configs/S1-scenario-cn-us-lazy-rule-v0.conf`。
- S1 `[General]` 固定使用 `https://cloudflare-dns.com/dns-query#proxy` 和 `https://security.cloudflare-dns.com/dns-query#proxy`，并使用 `block-quic = all-proxy`，不再使用 S0 手动插入的 UDP 443 规则作为默认手段。
- S1 `[Host]` 只从 `references/china-local-domain-seeds.txt` 生成，不从 lazy 的 `DIRECT` 规则反推 Host，不保留 `server:system`。
- S1 `[Rule]` 顺序为：海外账号/AI/流媒体前置 `PROXY`、中国本地种子表前置 `DIRECT`、lazy `[Rule]` 主体、`GEOIP,CN,DIRECT`、`FINAL,PROXY`。
- S1 引入远程 `RULE-SET` 依赖；若手机端规则集加载失败，应回退 S0 proxy DoH 版本区分问题，不直接否定底层 DNS/Host/DIRECT 方案。

## 2026-07-01 S1 BrowserLeaks 误直连修正

- 老倪反馈：`browserleaks.com/dns` 页面中 `Your IP Address`、DNS `IP Address`、`ISP` 都显示真实信息；Shadowrocket 日志显示 `browserleaks.com` 命中 `DIRECT`，部分 `.net`、`.org` 随机测试域名命中 `FINAL,PROXY`。
- 结论：这不是单纯 DNS 泄露，而是测试页主域名本身被直连；如果网页访问本身是 `DIRECT`，BrowserLeaks 必然能看到真实出口。
- 根因：S1 从 lazy 主体生成时没有继承 A/B/C/D/S0 中已有的 DNS/IP 测试站 `PROXY` 保护规则。
- 已更新 `scripts/build-s1-from-lazy.py`：新增测试站前置 `PROXY` 保护，包含 `browserleaks.com`、`browserleaks.org`、`dnsleaktest.com`、`ipleak.net`、`ippure.com`、`ipinfo.io`、`ip.sb` 等。
- 已重新生成 `configs/S1-scenario-cn-us-lazy-rule-v0.conf`；私有复测文件现已收纳到 `local/private-configs/desktop-import-2026-07-01/S1-default-lazy-proxy-doh.conf`。
- 验证目标：重新导入后，Shadowrocket 日志中 `browserleaks.com` 必须命中 `PROXY`；若命中 `PROXY` 后仍显示真实 IP，再回到代理绑定或 VPN 接管问题排查。

## 2026-07-01 S1.1 规则源治理方向

- S1 保留为稳定对照组，不覆盖、不删除；S2 保留为严格白名单参考，不作为当前主线。
- S1.1 目标：继承 S1 已验证的 `#proxy` DoH、中国本地 `[Host]`、中国本地 `DIRECT` 保护、成熟规则分流和 `FINAL,PROXY` 兜底，同时把规则源维护从“直接跟随上游”改成“监控、报告、人工确认、PR 更新”。
- 新增公开模板：`configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`。该文件不含节点、订阅、账号、代理组，不命名为 final、stable 或 release。
- S1.1 不再运行时依赖 iab0x00 AI 聚合 `RULE-SET`；iab0x00 只作为 AI 域名参考来源。可采纳域名必须先进入 `references/ai-proxy-domain-seeds.txt`，候选域名只放在 `references/ai-proxy-domain-candidates.txt`。
- 已把当前可替换的 QuantumultX 路径改为 blackmatrix7 的 Shadowrocket 路径；blackmatrix7 远程 `RULE-SET` 暂时保留运行时加载，并进入 `references/rule-source-registry.md` 监控。
- Johnshall `lazy.conf` 在 S1.1 中只作为参考和差异来源。它的 `[General]`、`[Host]`、`[URL Rewrite]`、`[MITM]` 不采用；上游变化不自动写入正式模板。
- GitHub Actions 监控口径：每周检查规则源，无变化不通知；出现不可访问、空规则、高风险格式、hash 变化或可评估新规则机会时，创建或更新 GitHub Issue。
- 人工确认闭环：老倪在 Issue 里使用固定指令确认或拒绝；确认后 Actions 创建 PR 并附带静态检查结果；PR 仍由老倪手动合并，Actions 不直接写主分支正式配置。
- 私有完整配置固定输出到 `local/private-configs/`，该目录已被 `.gitignore` 忽略；桌面测试文件已迁移进项目内本地私有目录，不进入仓库、不公开、不上传 GitHub Pages。

## 2026-07-01 S1.1 线上闭环验证

- 远端仓库已重新创建并推送：`https://github.com/nihongbin/Shadowrocket-gz-gaizao`。
- GitHub Pages 已启用为 Actions 发布源，公开 S1.1 模板链接已返回 HTTP 200：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`。
- raw GitHub 备用链接：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`。
- 正常手动运行 `S1.1 Rule Source Monitor` 时，当前规则源结果为 `severity=OK`，没有创建 Issue，符合“无变化不通知”。
- 使用 `simulate_hash_change=true` 手动模拟 hash 变化后，workflow 创建 Issue #1：`[S1.1规则源监控] P2 - 上游规则源出现需确认变化`。
- 在 Issue #1 评论 `/reject-source-update blackmatrix7-amazon` 后，workflow 创建 PR #2，PR 正文包含静态检查结果，并明确需要人工 review/merge。
- 验证确认：PR #2 只修改 `docs/rule-source-decisions.md`，不包含私有配置、节点、订阅、账号、代理组，也不包含临时报告文件。
- 验证确认：`main`、`origin/main` 和远端 `main` 均保持在同一个提交，Actions 没有直接改写主分支。

## 2026-07-01 S1.1 第二轮日志修正

- 本轮只改当前主线 S1.1，不覆盖旧 S1 对照组。
- 已保留 S1.1 既有修正：`browserleaks.com` 前置 `PROXY`、移除 iab0x00 远程 AI 规则、QuantumultX 路径替换、Google DoH 备用。
- 修正 `hijack-dns`：删除中国 DNS，只保留海外公共 DNS 明文劫持项，避免把中国 DNS 自己也放进劫持列表。
- 补充中国 App 日志域名到 `references/china-local-domain-seeds.txt`，由脚本统一生成 `[Host] + DIRECT`。
- 新增 `references/overseas-proxy-domain-seeds.txt`，把 `crunchyroll.com`、`revenuecat.com`、`bugsnag.com`、`branch.io`、`ipapi.co`、`appsflyersdk.com` 等海外 SDK/服务域名显式放入 Account/media guard，且排在中国 `DIRECT` 前。
- 不把 `insta360.com` 全域直连，只把更窄的 `snssdk.insta360.com` 作为中国 App 日志域名处理。
- `itdog.cn`、`ip.cn`、`qualcomm.cn`、`qianwen.com` 暂不进入默认配置，记录到 `references/s1-1-logfix-candidates.md` 等下一轮日志确认。
- 已生成本地私有测试文件：`local/private-configs/S1-1-default-lazy-stabilized-logfix.conf`。该文件含私有节点/代理组，只能本机测试，不进仓库、不公开。

## 2026-07-01 S2 严格中国 App 白名单方向

- 方向修正：手机 App 是第一保障场景，浏览器测试站只是体检工具；但测试站直连暴露出“未知或误判域名可能被 DIRECT”的底层风险。
- S2 目标：只有本项目确认过的中国 App 域名可以 `DIRECT`，海外 App、AI、流媒体、测试站、未知域名全部 `PROXY`。
- 已新增 `scripts/build-s2-strict-app-whitelist.py`，生成 `configs/S2-scenario-cn-us-strict-app-whitelist-v0.conf`。
- S2 只抽取 lazy 的 `PROXY` 规则；lazy 的所有 `DIRECT`、`GEOIP,CN,DIRECT`、`FINAL` 均被丢弃。
- S2 不使用 `GEOIP,CN,DIRECT`，避免未知域名只因解析到中国 IP 就自动直连。
- S2 `[Host]` 和中国 `DIRECT` 只来自 `references/china-local-domain-seeds.txt`，并在脚本中排除 `bytedance.com`、`byteimg.com`、`snssdk.com` 这类模糊跨境字节域名。
- 已生成复测文件，现已收纳到 `local/private-configs/desktop-import-2026-07-01/S2-default-strict-app-whitelist.conf`。
- 验证目标：微信、支付宝、淘宝、小红书、抖音、B 站、高德、Apple 基础服务尽量命中 `DIRECT`；TikTok、YouTube、Instagram、X、Facebook、ChatGPT/Claude、BrowserLeaks 必须命中 `PROXY`。

## 暂不采纳

- NZNL31 完整 `a-nomad` 策略组。
- 14 万行 `DOMAIN-SUFFIX` 结构。
- 在 S0 中采纳多远程规则源依赖。S1/S2 允许该依赖作为验证变量，但必须保留 S0 作为离线兜底。
- `stun-response-ip` 和 `stun-response-ipv6`。
- `always-ip-address = true`，D3 已证明它在当前环境比 D0 更差。
- Cloudflare DNS 覆写 + 清空备用 DNS + `8.8.8.8:53` 劫持方案，老倪已实测未成功。
- 继续叠加 `.conf` 参数，阶段收口后暂停。
- 把 Johnshall 或 lazy 的 `DIRECT` 规则当作中国本地域名池来生成 `[Host]`。
- 在 S2 中恢复 `GEOIP,CN,DIRECT`。

## 采纳门槛

配置项必须同时满足：

- A/B/C 实机验证中表现有效。
- 没有明显影响国内外分流可用性。
- 能解释清楚它降低的是哪一种风险。
- 不依赖用户提交敏感信息来验证。
