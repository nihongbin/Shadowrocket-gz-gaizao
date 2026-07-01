# Shadowrocket 隐私增强版 v1 工作规则

## 项目定位

本项目第一阶段只做 Shadowrocket 隐私增强版 v1 的验证准备，不发布最终配置。

当前新增 S0/S1/S1.1/S2 中美双市场场景验证方向：A/B/C/D 保留为 DNS 泄露诊断记录，S0 用于验证“中国本地体验优先保速度、海外账号侧和未知流量走美国代理兜底”的最小闭环；S1 在 S0 逻辑上接入 Johnshall `lazy.conf` 的成熟 `[Rule]` 主体；S1.1 在 S1 上做规则源治理、AI 自维护和 GitHub 通知闭环；S2 只允许本项目确认的中国 App 域名直连，海外 App、AI、流媒体、测试站和未知流量统一走代理。

项目表述统一使用“降低常见 DNS 泄露风险，并提供验证流程”。不要写“彻底解决 DNS 泄露”或类似绝对承诺。

## 目录结构

- `configs/`：A/B/C 三组待测试配置文件。
  - `A-johnshall-sr_cnip_ad.conf`：Johnshall 原版 `sr_cnip_ad.conf`。
  - `B-nznl31-a-nomad.conf`：NZNL31 当前 `a-nomad.conf` 样本。
  - `C-sr_cnip_ad_privacy_hardened_candidate.conf`：本项目候选增强配置。
  - `D*-diagnostic-*.conf`：A/B/C 全部失效后的 DNS 行为诊断配置，只用于定位根因，不作为最终配置候选。
  - `S*-scenario-*.conf`：中美双市场场景验证配置，只用于实测模板，不作为最终配置候选。
- `docs/`：验证矩阵、测试步骤、差异边界、普通用户说明和静态检查报告。
- `references/`：上游来源和许可证摘要等轻量参考材料，不保存节点订阅、账号或密钥。
  - `china-local-domain-seeds.txt`：S0/S1/S1.1/S2 `[Host]` 生成使用的中国本地域名种子表。
  - `ai-proxy-domain-seeds.txt`：S1.1 AI 正式代理清单。
  - `ai-proxy-domain-candidates.txt`：S1.1 AI 候选清单，不自动进入配置。
  - `rule-source-registry.md` / `rule-source-registry.json`：S1.1 外部规则源注册表。
- `scripts/`：本地生成和静态检查脚本，脚本不得把节点、订阅、账号或密钥写入仓库。
- `.github/workflows/`：S1.1 已确认启用，用于上游监控、Issue 通知、确认后 PR 和 GitHub Pages 公开模板发布。新增非 S1.1 自动化仍需单独确认。
- `local/`：本地私有工作区，必须被 `.gitignore` 忽略，不得提交或公开。
  - `local/private-configs/`：原始完整 Shadowrocket 配置、私有合并配置、桌面导入的 `.conf` 测试文件。
  - `local/intake/`：老倪提供的本地分析文档、临时记录、待整理材料。
  - 后续生成的私有完整配置固定放在 `local/private-configs/`，不再输出到桌面。

## 命名约定

- A/B/C 配置文件必须保留组别前缀，避免实机测试时导错文件。
- 候选配置使用 `candidate` 标记；没有完成实机验证前，不得使用 `final`、`release`、`stable` 等命名。
- D 组诊断配置必须使用 `D*-diagnostic-*.conf` 命名，不得使用 `candidate`、`final`、`release`、`stable` 等命名。
- S 组场景配置必须使用 `S*-scenario-*.conf` 命名，不得使用 `candidate`、`final`、`release`、`stable` 等命名。
- 文档文件名使用小写英文和短横线，例如 `verification-matrix.md`。

## 上游来源

- A 组来源：`Johnshall/Shadowrocket-ADBlock-Rules-Forever` 的 `release` 分支 `sr_cnip_ad.conf`。
- B 组来源：`NZNL31/Shadowrocket-Ad-DNS-Leak-Rules` 的 `main` 分支 `a-nomad.conf`。
- 参考来源：NZNL31 README 提到的 `colin-chang` 原版 `a-nomad.conf`。
- S0 来源：`Johnshall/Shadowrocket-ADBlock-Rules-Forever` 的 `release` 分支 `sr_top500_whitelist.conf` 只作为 `[Rule]` 主体来源，不等于纯中国白名单。
- S1 来源：`Johnshall/Shadowrocket-ADBlock-Rules-Forever` 的 `lazy.conf` 只抽取 `[Rule]` 主体；不采用其 `[General]`、`[Host]`、`[URL Rewrite]`、`[MITM]`。
- S1.1 来源：继承 S1 方向；Johnshall `lazy.conf` 只做参考和差异监控，blackmatrix7 Shadowrocket `RULE-SET` 作为暂时运行时远程依赖并纳入注册表，iab0x00 只做 AI 域名参考，不作为运行时依赖。
- S2 来源：`Johnshall/Shadowrocket-ADBlock-Rules-Forever` 的 `lazy.conf` 只抽取 `PROXY` 规则；所有 lazy `DIRECT`、`GEOIP,CN,DIRECT`、`FINAL` 均不得进入 S2。

## 许可证继承

- Johnshall 与 NZNL31 均使用 Creative Commons Attribution-ShareAlike 4.0 International License。
- 任何改编、分发或公开发布都必须保留原作者署名和相同协议说明。
- 第一阶段不对外发布，只在本地准备验证材料。

## 验证流程

- 第一阶段必须先完成 A/B/C 实机验证矩阵，不得直接把候选项写成最终配置。
- 若 A/B/C 三组全部失效，可以新增 D 组诊断配置定位根因；D 组只证明诊断现象，不直接进入最终 v1。
- 若进入 S0 场景验证，必须明确：Johnshall 可用于 `[Rule]` 主体，`[Host]` 只能从中国本地域名池生成，海外账号覆盖规则必须在 Johnshall 规则之前。
- 若进入 S1 场景验证，必须明确：S1 使用 `lazy.conf` 的成熟 `[Rule]` 主体，但仍保留本项目的 `#proxy` DoH、种子表 `[Host]`、前置海外 `PROXY` 和中国 `DIRECT` 保护。
- 若进入 S1.1 场景验证，必须明确：S1.1 不覆盖 S1，只作为增强验证组；上游变化只生成 Issue 和 PR，未人工确认不得改正式模板。
- 若进入 S2 场景验证，必须明确：S2 不信任任何第三方 `DIRECT`，中国直连只来自 `references/china-local-domain-seeds.txt` 过滤后的明确白名单。
- 只有实机验证有效且没有明显可用性问题的配置项，才允许进入最终 v1。
- 无法确认有效、效果不稳定或解释不清的配置项，必须写入调研记录，不得进入正式候选结论。

## v1 范围

v1 只验证以下问题：

- DNS 查询泄露
- IPv6 泄露
- 系统 DNS 回退
- 直连域名是否走系统 DNS
- 常见硬编码明文 DNS 绕过
- 规则合并后的分流可用性

WebRTC/STUN 不作为 v1 配置实现范围。不得默认加入 `stun-response-ip` 或 `stun-response-ipv6`。文档只提醒用户确认 Shadowrocket 自带开关，WebRTC 测试只作为用户端开关确认项。

## S0 范围

- S0 不追求“完全看不到中国 DNS”。
- 中国白名单域名使用中国 DNS 是设计目标，不算失败。
- 海外账号域名、未知域名、DNS 随机测试域名出现中国本地运营商 DNS 才算失败。
- S0 不做 TikTok 专项，TikTok 只作为海外账号侧验证样例。
- `configs/S0-scenario-cn-us-account-aggressive-v0.conf` 是公开规则模板，不含节点和代理组；在 Shadowrocket 只能选一个配置文件的场景下，不能单独作为有效实机配置。
- 手机实测必须先用 `scripts/merge-s0-private-config.py` 将用户本地原始完整配置与 S0 模板合并，生成不进仓库的私有完整配置。
- 私有完整配置默认输出到 `local/private-configs/`；该目录在项目内但被忽略，不能复制到 `configs/`、`docs/`、`references/` 或公开链接目录。
- 公开链接、GitHub Actions、自动写仓库属于红线动作，必须单独确认。

## S1 范围

- S1 是 S0 的增强验证分支，不是最终配置。
- `configs/S1-scenario-cn-us-lazy-rule-v0.conf` 是公开规则模板，不含节点和代理组；不能单独作为有效实机配置。
- S1 只采用 `lazy.conf` 的 `[Rule]` 主体，用于补强流媒体、AI、海外服务和国内 App 分流。
- S1 不采用 `lazy.conf` 的系统 DNS、`server:system` Host、MITM 或 URL Rewrite。
- S1 存在远程 `RULE-SET` 依赖；如果手机端规则集加载失败，回退到 S0 离线规则兜底。

## S1.1 范围

- S1.1 是 S1 的规则源治理增强分支，不是最终配置。
- `configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf` 是公开规则模板，不含节点、订阅、账号、代理组；不能单独作为有效实机配置。
- S1.1 移除 iab0x00 远程 AI `RULE-SET` 运行时依赖，AI 规则只从本项目正式清单生成。
- S1.1 不允许 `rule/QuantumultX/` 路径；已确认可替换的规则源必须使用 blackmatrix7 Shadowrocket 路径。
- S1.1 每周通过 GitHub Actions 监控上游；无变化不通知，有变化或异常创建/更新 Issue。
- 人工确认后 Actions 只能创建 PR，不得直接合并主分支。
- GitHub Pages 只能发布不含节点和代理组的公开模板；`local/private-configs/` 不得进入仓库或公开目录。

## S2 范围

- S2 是严格中国 App 白名单验证分支，不是最终配置。
- `configs/S2-scenario-cn-us-strict-app-whitelist-v0.conf` 是公开规则模板，不含节点和代理组；不能单独作为有效实机配置。
- S2 的中国直连只来自本项目种子表，不从 lazy、GEOIP、`.cn` 或第三方 `DIRECT` 自动扩展。
- S2 不使用 `GEOIP,CN,DIRECT`，未知域名统一由 `FINAL,PROXY` 兜底。
- S2 初始排除 `bytedance.com`、`byteimg.com`、`snssdk.com` 这类模糊跨境域名，避免 TikTok/抖音边界不清。
- 若中国 App 变慢，优先通过日志补充 `references/china-local-domain-seeds.txt`，不得直接恢复 lazy `DIRECT` 或 `GEOIP,CN,DIRECT`。

## 敏感信息边界

禁止提交或记录以下内容：

- 节点订阅链接
- 节点名称中的账号信息
- token、密码、密钥、邮箱验证码
- 个人网络截图中暴露的 IP、运营商、地理位置或账号信息
- 任何可识别个人身份或服务账号的信息

## 红线

以下操作必须单独征得老倪确认：

- `git push` 或任何远程发布
- 公开 GitHub 发布、部署、发文
- 修改 CI/CD 配置
- 删除文件或目录
- 修改系统配置、数据库、密钥或环境变量

## 验收标准

完成第一阶段时，必须具备：

- 项目级规则和目录约定已建立。
- A/B/C 三组测试材料齐全。
- 验证矩阵、测试记录模板、采纳边界和普通用户验证文档齐全。
- 本地静态检查通过。
- 输出可让 iPhone 14 按步骤实测的清单，并停在等待实机测试状态。
