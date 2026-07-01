# Shadowrocket S0/S1/S1.1/S2 中美双市场场景验证

当前项目状态：A/B/C/D 保留为 DNS 泄露诊断记录，不再产出最终 v1；S0 用来测试“中国本地体验保速度、海外账号侧和未知流量走美国代理兜底”的最小闭环，S1 在 S0 基础上接入 Johnshall `lazy.conf` 的成熟 `[Rule]` 主体，S1.1 在 S1 上做规则源治理、AI 自维护和 GitHub 通知闭环，S2 只作为“严格中国 App 白名单 + 海外/未知全部代理”的安全边界参考。

S0/S1/S1.1/S2 都不是“DNS 绝对隐私方案”。它允许中国白名单域名使用中国 DNS 获取更近 CDN；失败标准是海外账号域名、未知域名、AI 域名或 DNS 随机测试域名暴露到中国本地运营商 DNS。

## 当前材料

- `configs/A-johnshall-sr_cnip_ad.conf`：Johnshall 原版国内外划分 + 去广告配置，作为旧 A 组记录。
- `configs/B-nznl31-a-nomad.conf`：NZNL31 的 `a-nomad.conf` 样本，作为旧 B 组记录。
- `configs/C-sr_cnip_ad_privacy_hardened_candidate.conf`：旧候选增强配置，A/B/C 全部失效后不进入最终。
- `configs/D*-diagnostic-*.conf`：DNS 行为诊断配置，只保留为排查记录。
- `configs/S0-scenario-cn-us-account-aggressive-v0.conf`：S0 最小闭环公开规则模板，不含节点和代理组，不是 final、stable 或 release。
- `configs/S1-scenario-cn-us-lazy-rule-v0.conf`：S1 lazy 规则增强公开规则模板，不含节点和代理组，不是 final、stable 或 release。
- `configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`：S1.1 规则源治理增强公开模板，不含节点和代理组，不是 final、stable 或 release。
- `configs/S2-scenario-cn-us-strict-app-whitelist-v0.conf`：S2 严格中国 App 白名单公开规则模板，不含节点和代理组，不是 final、stable 或 release。
- `references/china-local-domain-seeds.txt`：S0/S1/S1.1/S2 `[Host]` 生成使用的中国本地域名种子表。
- `references/ai-proxy-domain-seeds.txt`：S1.1 AI 正式代理清单，进入配置。
- `references/ai-proxy-domain-candidates.txt`：S1.1 AI 候选清单，不自动进入配置。
- `references/rule-source-registry.md`：S1.1 外部规则源注册表。
- `scripts/build-s0-from-johnshall.py`：从 Johnshall `sr_top500_whitelist.conf` 生成 S0 配置。
- `scripts/build-s1-from-lazy.py`：从 Johnshall `lazy.conf` 只抽取 `[Rule]` 主体生成 S1 配置。
- `scripts/build-s1-1-stabilized.py`：生成 S1.1 公开模板，移除 iab0x00 运行时依赖并替换 QuantumultX 路径。
- `scripts/build-s2-strict-app-whitelist.py`：从 Johnshall `lazy.conf` 只抽取 `PROXY` 规则生成 S2 配置。
- `scripts/merge-s0-private-config.py`：把用户本地原始完整配置和 S0/S1/S1.1/S2 模板合并，输出到 `local/private-configs/` 的私有完整配置。
- `.github/workflows/`：S1.1 每周规则源监控、Issue 通知、确认后 PR、GitHub Pages 公开模板发布。
- `local/private-configs/`：本地私有配置区，保存原始完整配置和私有合并测试文件；该目录被忽略，不进入仓库、不公开。
- `local/intake/`：本地输入材料区，保存桌面导入的分析文档和临时材料；该目录被忽略。

## S0 设计口径

- Johnshall `sr_top500_whitelist.conf` 只作为 `[Rule]` 主体来源，不等于纯中国白名单。
- `[Host]` 只从中国本地域名池生成：本项目种子表 + Johnshall 中明确的 `.cn` 直连域名。
- 海外账号覆盖规则放在 Johnshall 规则前，先拦住 TikTok、Instagram、YouTube、X、Facebook、Google、OpenAI、Claude 等主域名。
- 未知流量由 `FINAL,PROXY` 兜底。
- S0 模板本身没有 `[Proxy]`、`[Proxy Group]` 或节点信息；如果 Shadowrocket 只能选一个配置文件，必须先生成私有合并版再导入手机。
- 不加入 `always-ip-address = true`，不引入广告拦截、MITM、URL Rewrite。

## S1 设计口径

- S1 继续使用已验证方向：`#proxy` DoH、中国本地域名 `[Host]`、中国本地 `DIRECT` 保护、海外/未知 `PROXY` 兜底。
- S1 只抽取 Johnshall `lazy.conf` 的 `[Rule]` 主体，不采用其 `[General]`、`[Host]`、`[URL Rewrite]`、`[MITM]`。
- S1 保留 lazy 的远程 `RULE-SET`，用于补强 YouTube、Netflix、TikTok、OpenAI、Google、微信、抖音、小红书等成熟分流。
- S1 的 `[Host]` 仍只从 `references/china-local-domain-seeds.txt` 生成，不从 lazy 的 `DIRECT` 规则反推 Host。
- S1 存在远程 `RULE-SET` 加载风险；如果手机端加载失败或断网，回退到 S0 proxy DoH 版本。

## S1.1 设计口径

- S1.1 保留 S1 已验证方向：`#proxy` DoH、中国本地域名 `[Host]`、中国本地 `DIRECT` 保护、海外/未知 `FINAL,PROXY` 兜底。
- S1.1 不再运行时依赖 iab0x00 AI 聚合规则；AI 规则由 `references/ai-proxy-domain-seeds.txt` 生成，候选清单只监控不进配置。
- S1.1 继续保留 blackmatrix7 Shadowrocket `RULE-SET` 作为运行时远程规则源，并纳入 `references/rule-source-registry.md` 监控。
- Johnshall `lazy.conf` 在 S1.1 中只作为参考和差异监控来源，不自动改正式模板。
- S1.1 通过 GitHub Actions 每周监控上游；无变化不通知，有变化或异常才创建/更新 Issue，人工确认后只创建 PR，不直接合并主分支。

## S2 设计口径

- S2 以手机 App 场景为第一保障对象，浏览器测试站只作为体检工具。
- S2 只允许本项目确认的中国 App 域名直连；海外 App、AI、流媒体、测试站和未知域名统一走 `PROXY`。
- S2 只保留 lazy 的 `PROXY` 规则，不保留 lazy 的任何 `DIRECT`、`GEOIP,CN,DIRECT` 或 `FINAL`。
- S2 不使用 `GEOIP,CN,DIRECT`，避免“解析到中国 IP 的未知域名”自动直连。
- S2 初始排除 `bytedance.com`、`byteimg.com`、`snssdk.com`，保留更明确的中国抖音域名。
- S2 的代价是：未收录的中国 App 域名会走代理，可能变慢；后续通过补种子表解决。

## 如何继续

先阅读：

- `docs/scenario-cn-us-account-v0.md`
- `docs/research-notes.md`
- `docs/static-check-report.md`
- `references/johnshall-whitelist-sources.md`
- `references/johnshall-lazy-sources.md`
- `references/s2-strict-app-whitelist-sources.md`

手机测试不能直接导入公开 S0/S1/S1.1/S2 模板。应先用 `scripts/merge-s0-private-config.py` 读取 `local/private-configs/` 里的原始完整配置，生成同目录下的私有完整配置，再导入 Shadowrocket。后续公开链接只能指向不含节点和代理组的公开模板，不能指向 `local/`。

## 公开模板链接

- GitHub 仓库：https://github.com/nihongbin/Shadowrocket-gz-gaizao
- GitHub Pages S1.1 模板：https://nihongbin.github.io/Shadowrocket-gz-gaizao/S1-1-scenario-cn-us-lazy-stabilized-v0.conf
- raw GitHub 备用链接：https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf

公开链接只发布不含节点、订阅、账号和代理组的 S1.1 模板。手机实测仍以 `local/private-configs/` 下的私有完整配置为准。

## 来源和许可证

本项目参考：

- `Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- `NZNL31/Shadowrocket-Ad-DNS-Leak-Rules`
- `colin-chang` 原版 `a-nomad.conf`

上游配置采用 Creative Commons Attribution-ShareAlike 4.0 International License。若未来公开发布改编配置，必须保留署名并使用相同协议。

## 当前限制

- A/B/C 三组已反馈全部失效，不能进入最终 v1。
- D1/D2 已反馈为网络近似断开；D3 已反馈为出口正确但 DNS 全部泄露。
- `always-ip-address = true` 暂不采纳。
- S0/S1/S1.1/S2 仍是场景验证模板，不是最终配置。
- S0/S1/S1.1/S2 公开模板不能单独代表手机最终测试配置；私有合并版因含节点信息不得进入仓库。
- S1 引入远程 `RULE-SET` 依赖，若手机端无法加载远程规则，不能直接判定底层 DNS 方案失败，应回退 S0 再判断。
- S2 更安全但可能牺牲部分中国 App 速度；如果中国 App 日志显示走代理，优先补种子表。
- 本地 `.git` 已重新初始化为 `main`，远端 GitHub 仓库已重新创建并推送。
- GitHub Actions 已启用：Pages 发布、每周规则源监控、Issue 通知、人工确认后 PR 更新已在线验证。
- 当前存在一组线上模拟验证材料：Issue #1 和 PR #2，用于证明 hash 变化会通知、评论指令会开 PR、主分支不会被 Actions 直接改写。
- 私有完整配置统一放在项目内 `local/private-configs/`，不再放桌面；`local/` 已被忽略，不得公开。
