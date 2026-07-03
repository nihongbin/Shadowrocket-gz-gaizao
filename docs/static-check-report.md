# 静态检查报告

生成时间：2026-07-01

最后更新：2026-07-03，追加 S5 V5 MVP 本地静态检查结果。

本报告只证明本地材料、自动化脚本和公开模板的静态状态，不证明 Shadowrocket 实机有效性。A/B/C/D 保留为 DNS 泄露诊断记录；S0/S1/S1.1/S2 是中美双市场场景验证模板，不是 final、stable 或 release。

## 仓库状态

- PASS - required directory exists: `configs/`
- PASS - required directory exists: `docs/`
- PASS - required directory exists: `references/`
- PASS - required directory exists: `scripts/`
- PASS - `.git` 已重新初始化为 `main`，远端 `origin` 已绑定并推送到 `https://github.com/nihongbin/Shadowrocket-gz-gaizao`。
- PASS - `local/` 已写入 `.gitignore`，`local/private-configs/` 被确认忽略。
- PASS - S1.1 已新增 GitHub Actions：每周规则源监控、Issue 通知、人工确认后 PR、GitHub Pages 公开模板发布。
- PASS - GitHub Actions workflow permissions 已配置为 write，允许确认后创建 PR，但不自动合并。
- PASS - GitHub Pages 已启用为 workflow 发布源，S1.1 公开模板链接已返回 HTTP 200。

## 文件存在性

- PASS - required file exists: `AGENTS.md`
- PASS - required file exists: `README.md`
- PASS - required file exists: `configs/S0-scenario-cn-us-account-aggressive-v0.conf`
- PASS - required file exists: `configs/S1-scenario-cn-us-lazy-rule-v0.conf`
- PASS - required file exists: `configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`
- PASS - required file exists: `configs/S2-scenario-cn-us-strict-app-whitelist-v0.conf`
- PASS - required file exists: `references/china-local-domain-seeds.txt`
- PASS - required file exists: `references/ai-proxy-domain-seeds.txt`
- PASS - required file exists: `references/ai-proxy-domain-candidates.txt`
- PASS - required file exists: `references/overseas-proxy-domain-seeds.txt`
- PASS - required file exists: `references/s1-1-logfix-candidates.md`
- PASS - required file exists: `references/rule-source-registry.json`
- PASS - required file exists: `references/rule-source-registry.md`
- PASS - required file exists: `references/johnshall-whitelist-sources.md`
- PASS - required file exists: `references/johnshall-lazy-sources.md`
- PASS - required file exists: `references/s2-strict-app-whitelist-sources.md`
- PASS - required file exists: `scripts/build-s0-from-johnshall.py`
- PASS - required file exists: `scripts/build-s1-from-lazy.py`
- PASS - required file exists: `scripts/build-s1-1-stabilized.py`
- PASS - required file exists: `scripts/build-s2-strict-app-whitelist.py`
- PASS - required file exists: `scripts/check-s1-1-static.py`
- PASS - required file exists: `scripts/check-rule-sources.py`
- PASS - required file exists: `scripts/check-ai-domain-health.py`
- PASS - required file exists: `scripts/apply-approved-s1-1-update.py`
- PASS - required file exists: `.github/workflows/s1-1-source-monitor.yml`
- PASS - required file exists: `.github/workflows/s1-1-apply-approved-update.yml`
- PASS - required file exists: `.github/workflows/pages.yml`
- PASS - required file exists: `scripts/merge-s0-private-config.py`
- PASS - required file exists: `docs/scenario-cn-us-account-v0.md`
- PASS - required file exists: `docs/research-notes.md`

## S0 配置结构

- PASS - S0 contains `[General]`
- PASS - S0 contains `[Host]`
- PASS - S0 contains `[Rule]`
- PASS - S0 has no node URI protocol lines: `ss://`, `ssr://`, `vmess://`, `vless://`, `trojan://`, `hysteria://`
- PASS - S0 has no obvious token/password/secret/subscribe patterns
- PASS - S0 does not contain `always-ip-address = true`
- PASS - S0 does not contain `[MITM]`, `[URL Rewrite]`, `URL-REGEX`, rule-body `REJECT`, or rule-body `RULE-SET`
- PASS - S0 final non-empty line is `FINAL,PROXY`
- PASS - account-side guard appears before Johnshall rule body
- PASS - `[Host]` entries are limited to `references/china-local-domain-seeds.txt` or `.cn` domains
- PASS - `[Host]` does not include overseas account guard domains

## S0 生成检查

- PASS - `python scripts\build-s0-from-johnshall.py --check`
- PASS - repeated generation hash unchanged: `4B52BC2D6EFD05EEFB8BE8DE740FAF06EA1C450869E0A6A5BF24D2E2AFD67E4C`
- PASS - local fixture no-change test keeps identical output
- PASS - local fixture changed-upstream test changes output without touching Johnshall remote
- PASS - generated file header uses stable metadata: upstream URL, upstream SHA256, rule counts, license note; no current runtime timestamp

## S1 配置结构

- PASS - S1 contains `[General]`
- PASS - S1 contains `[Host]`
- PASS - S1 contains `[Rule]`
- PASS - S1 has no node URI protocol lines: `ss://`, `ssr://`, `vmess://`, `vless://`, `trojan://`, `hysteria://`
- PASS - S1 has no obvious token/password/secret/subscribe patterns
- PASS - S1 does not contain `always-ip-address = true`
- PASS - S1 does not contain `[MITM]`, `[URL Rewrite]`, `dns-server = system`, `fallback-dns-server = system`, or `server:system`
- PASS - S1 contains proxy DoH: `https://cloudflare-dns.com/dns-query#proxy` and `https://security.cloudflare-dns.com/dns-query#proxy`
- PASS - S1 contains `block-quic = all-proxy`
- PASS - S1 final non-empty line is `FINAL,PROXY`
- PASS - S1 test-site `PROXY` guard includes `browserleaks.com`, `browserleaks.org`, `dnsleaktest.com`, `ipleak.net`, `ippure.com`, `ipinfo.io`, and `ip.sb`
- PASS - S1 test-site `PROXY` guard appears before account/media/AI `PROXY` guard
- PASS - overseas account/media/AI `PROXY` guard appears before China-local `DIRECT` guard
- PASS - China-local `DIRECT` guard appears before Johnshall lazy rule body
- PASS - Johnshall lazy rule body appears before `GEOIP,CN,DIRECT` and `FINAL,PROXY`

## S1 生成检查

- PASS - `python scripts\build-s1-from-lazy.py --check`
- PASS - repeated generation check: `python scripts\build-s1-from-lazy.py --check`
- PASS - local fixture no-change test keeps identical output
- PASS - local fixture changed-upstream test changes output without touching Johnshall remote
- PASS - local fixture confirms lazy `[General]`, `[Host]`, `[URL Rewrite]`, and `[MITM]` are not imported
- PASS - generated file header uses stable metadata: upstream URL, upstream SHA256, rule counts, license note; no current runtime timestamp

## S1.1 配置结构

- PASS - S1.1 contains `[General]`
- PASS - S1.1 contains `[Host]`
- PASS - S1.1 contains `[Rule]`
- PASS - S1.1 has no node URI protocol lines: `ss://`, `ssr://`, `vmess://`, `vless://`, `trojan://`, `hysteria://`
- PASS - S1.1 has no obvious token/password/secret/subscribe patterns
- PASS - S1.1 does not contain `[MITM]`, `[URL Rewrite]`, `dns-server = system`, `fallback-dns-server = system`, or `server:system`
- PASS - S1.1 contains `#proxy` DoH and `block-quic = all-proxy`
- PASS - S1.1 does not contain iab0x00 remote `RULE-SET`
- PASS - S1.1 does not contain `rule/QuantumultX/` paths
- PASS - S1.1 `hijack-dns` does not contain China DNS: `114.114.114.114`, `223.5.5.5`, `223.6.6.6`, `119.29.29.29`
- PASS - S1.1 includes second-round China logfix domains as `[Host] + DIRECT`
- PASS - S1.1 includes second-round overseas SDK/service domains as `PROXY` before China-local `DIRECT`
- PASS - S1.1 does not direct or host-map the whole `insta360.com` domain
- PASS - S1.1 final non-empty line is `FINAL,PROXY`
- PASS - S1.1 keeps DNS/IP test-site `PROXY` guard before China-local `DIRECT`
- PASS - S1.1 keeps overseas account/media `PROXY` and local AI `PROXY` guard before China-local `DIRECT`
- PASS - S1.1 keeps Johnshall `lazy.conf` as reference rule body only; lazy `[General]`, `[Host]`, `[URL Rewrite]`, and `[MITM]` are not imported

## S1.1 规则源治理检查

- PASS - `python scripts\build-s1-1-stabilized.py --check`
- PASS - `python scripts\check-s1-1-static.py`
- PASS - repeated generation hash is stable when inputs do not change
- PASS - `references/rule-source-registry.json` covers all remote URLs used or monitored by S1.1
- PASS - `python scripts\check-rule-sources.py` writes `docs/rule-source-health-report.md` and `docs/lazy-upstream-diff-report.md`
- PASS - rule-source health reports omit runtime timestamps to avoid no-op diffs
- PASS - current source monitor result is `severity=OK`; unchanged Johnshall `lazy.conf` stays reference-only and does not trigger Issue
- PASS - local hash-change fixture produces `severity=P2` and `issue_required=True` without modifying upstream remote sources
- PASS - `.github/workflows/s1-1-source-monitor.yml` includes a manual `simulate_hash_change` input for online Issue-creation testing; scheduled runs do not use this simulation path
- PASS - online normal monitor run completed successfully and created no Issue when source status was OK
- PASS - online simulated hash-change run created Issue #1 with severity `P2`
- PASS - `references/ai-proxy-domain-seeds.txt` enters S1.1 as local AI `PROXY` rules
- PASS - `references/ai-proxy-domain-candidates.txt` is monitored but does not enter S1.1 automatically
- PASS - `references/overseas-proxy-domain-seeds.txt` enters S1.1 Account/media guard as local `PROXY` rules
- PASS - `references/s1-1-logfix-candidates.md` records second-round uncertain domains without adding them to default config
- PASS - `python scripts\check-ai-domain-health.py` writes `docs/ai-domain-health-report.md` for manual review
- PASS - AI domain health report omits runtime timestamps to avoid no-op diffs
- PASS - `scripts/apply-approved-s1-1-update.py` supports `/approve-s1.1-update`, `/approve-ai-domain example.com`, `/approve-source-update source-id`, `/reject-ai-domain example.com`, and `/reject-source-update source-id`
- PASS - simulated reject command leaves the generated S1.1 config hash unchanged; local simulation record is not kept in formal decisions
- PASS - approval workflow writes temporary PR body and static-check output under ignored `local/`, so report artifacts are not included in PR diffs
- PASS - online reject comment created PR #2 with static-check output in the PR body
- PASS - PR #2 only changes `docs/rule-source-decisions.md`; temporary report files, configs, nodes, subscriptions, accounts, and proxy groups are not included
- PASS - `main`, `origin/main`, and remote `main` remained unchanged after the Issue comment workflow; Actions created a PR instead of writing main

## S2 配置结构

- PASS - S2 contains `[General]`
- PASS - S2 contains `[Host]`
- PASS - S2 contains `[Rule]`
- PASS - S2 has no node URI protocol lines: `ss://`, `ssr://`, `vmess://`, `vless://`, `trojan://`, `hysteria://`
- PASS - S2 has no obvious token/password/secret/subscribe patterns
- PASS - S2 does not contain `always-ip-address = true`
- PASS - S2 does not contain `[MITM]`, `[URL Rewrite]`, `dns-server = system`, `fallback-dns-server = system`, or `server:system`
- PASS - S2 contains proxy DoH and `block-quic = all-proxy`
- PASS - S2 does not contain `GEOIP,CN,DIRECT`
- PASS - S2 does not contain `17.0.0.0/8` direct or excluded route
- PASS - S2 final non-empty line is `FINAL,PROXY`
- PASS - S2 order is LAN/private `DIRECT`, test-site `PROXY`, account/media/AI `PROXY`, China app whitelist `DIRECT`, lazy `PROXY` rules, `FINAL,PROXY`
- PASS - S2 keeps `browserleaks.com`, `youtube.com`, `tiktok.com`, `googlevideo.com`, and `openai.com` before China app whitelist
- PASS - S2 keeps `wechat.com`, `taobao.com`, `alipay.com`, `douyin.com`, and `xiaohongshu.com` as China app whitelist `DIRECT`
- PASS - S2 excludes ambiguous domains `bytedance.com`, `byteimg.com`, and `snssdk.com` from `[Host]` and `DIRECT`
- PASS - S2 lazy body keeps only `PROXY` rules and drops lazy `DIRECT`, `GEOIP,CN,DIRECT`, and `FINAL`

## S2 生成检查

- PASS - `python scripts\build-s2-strict-app-whitelist.py --check`
- PASS - generated S2 stats include `dropped-direct=12`, `dropped-final=1`, and `dropped-geoip-cn-direct=1`
- PASS - repeated generation hash unchanged: `137FFB45A222F961F67C5DDEC668DCE4B2D82F903E9688966E9D79BD61A9714F`
- PASS - local fixture no-change test keeps identical output
- PASS - local fixture changed-upstream test changes output without touching Johnshall remote
- PASS - local fixture confirms lazy `DIRECT`, `GEOIP,CN,DIRECT`, and `FINAL` are dropped while lazy `PROXY` is kept
- PASS - generated file header uses stable metadata: upstream URL, upstream SHA256, rule counts, license note; no current runtime timestamp

## S5 V5 MVP 配置结构

- PASS - V5 基盘 hash 已确认：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- PASS - S5 公开模板存在：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- PASS - S5 清单目录存在：`references/v5-mvp/`
- PASS - S5 包含 `[General]`、`[Rule]`、`[Host]`
- PASS - S5 不包含 `[Proxy]`、`[Proxy Group]`、`[MITM]`、`[URL Rewrite]`
- PASS - S5 不包含节点 URI：`ss://`、`ssr://`、`vmess://`、`vless://`、`trojan://`、`hysteria://`
- PASS - S5 不包含明显 token/password/secret/subscribe 字段
- PASS - S5 保留 V5 `dns-server` 与 `fallback-dns-server` 的 Cloudflare `#proxy` DoH，不包含 DNS B 的 Google fallback
- PASS - S5 保留 `block-quic = all-proxy`，不包含 QUIC allow
- PASS - S5 保持测试站 `PROXY` 在中国 `DIRECT` 前
- PASS - S5 保持海外/AI/流媒体 `PROXY` 在中国 `DIRECT` 前
- PASS - S5 保持中国 App `DIRECT` 在远程 `RULE-SET` 和 `FINAL,PROXY` 前
- PASS - S5 `[Rule]` 段内最后有效规则是 `FINAL,PROXY`
- PASS - S5 与 V5 的有效 `[General]`、`[Rule]`、`[Host]` 内容一致：`General=15`、`Rule=351`、`Host=381`

## S5 V5 MVP 生成检查

- PASS - `python scripts\build-v5-mvp-template.py --sync-manifests`
- PASS - `python scripts\build-v5-mvp-template.py --check`
- PASS - S5 输出 hash 稳定：`B1E2FFA0F55E27B2B10A55F2917A2228972619377A3C746D10AC5C11AEBF7712`
- PASS - `references/v5-mvp/china-direct-domains.txt` 与 `references/v5-mvp/china-host-dns.csv` 一一对应：`china_direct=190`、`host_dns=190`
- PASS - S5 清单覆盖：`test_proxy=14`、`overseas_proxy=78`、`ai_proxy=31`、`remote_rulesets=33`、`lazy_body=36`
- PASS - 公开模板文件头只写稳定元数据和计数，不写当前运行时间
- PASS - `scripts/merge-s0-private-config.py --v5-mvp --dry-run` 通过
- PASS - 私有合并测试输出到 `local/private-configs/S5-v5-mvp-private-merged-check.conf`
- PASS - 私有合并测试文件包含 `[Proxy]` 和 `[Proxy Group]`，但不包含原始 `[URL Rewrite]` 或 `[MITM]`
- PASS - 私有合并测试文件 `[Rule]` 段内最后有效规则是 `FINAL,PROXY`
- PASS - `local/private-configs/` 被 `.gitignore` 忽略，私有合并测试文件没有出现在待提交列表
- PASS - S5 用户反馈文档存在：`docs/v5-mvp-user-test-feedback.md`
- PASS - S5 发布 runbook 存在：`docs/v5-mvp-release-runbook.md`
- PASS - 老倪已确认允许执行发布动作，Pages workflow 已加入 S5 模板发布项

## 私有合并检查

- PASS - `scripts/merge-s0-private-config.py` dry-run uses section summary only and does not print node contents
- PASS - local fixture merge preserves only `[Proxy]` and `[Proxy Group]` from the base config
- PASS - local fixture merge replaces old `[General]`, `[Host]`, and `[Rule]` with template sections
- PASS - local fixture merge does not preserve original `[URL Rewrite]` or `[MITM]`
- PASS - local fixture merge removes old `FINAL,DIRECT`
- PASS - local fixture merged final non-empty line is `FINAL,PROXY`
- PASS - script allows private merged config only under ignored `local/private-configs/`
- PASS - no private merged config was written under `configs/`
- PASS - `--preserve-general` mode keeps base `[General]` and replaces only S0 `[Host]` / `[Rule]`
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S0-default-conservative.conf` keeps `dns-server = system` and `fallback-dns-server = system`
- PASS - `local/private-configs/desktop-import-2026-07-01/S0-default-conservative.conf` final non-empty line is `FINAL,PROXY`
- PASS - `--plain-us-dns` mode sets `dns-server = 8.8.8.8, 1.1.1.1`
- PASS - `--plain-us-dns` mode sets `fallback-dns-server = 8.8.8.8, 1.1.1.1`
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S0-default-plain-usdns.conf` contains no Cloudflare/Google DoH URL
- PASS - `local/private-configs/desktop-import-2026-07-01/S0-default-plain-usdns.conf` final non-empty line is `FINAL,PROXY`
- PASS - `--proxy-doh` mode sets `dns-server = https://cloudflare-dns.com/dns-query#proxy, https://security.cloudflare-dns.com/dns-query#proxy`
- PASS - `--proxy-doh` mode sets `fallback-dns-server = https://cloudflare-dns.com/dns-query#proxy, https://security.cloudflare-dns.com/dns-query#proxy`
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh.conf` final non-empty line is `FINAL,PROXY`
- PASS - `--block-quic` mode inserts `AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP` before account guard rules
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh-quic.conf` keeps proxy DoH and final non-empty line is `FINAL,PROXY`
- PASS - S0 generator now creates China-local `DIRECT` guard rules from `references/china-local-domain-seeds.txt`
- PASS - generated S0 stats include `china_direct=98`
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S0-default-proxy-doh-quic-direct.conf` keeps overseas account `PROXY` before China-local `DIRECT`
- PASS - representative China local domains `wechat.com`, `xiaohongshu.com`, `douyin.com`, `bilibili.com`, `taobao.com` appear as `DIRECT` before Johnshall body
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S1-default-lazy-proxy-doh.conf`
- PASS - `local/private-configs/desktop-import-2026-07-01/S1-default-lazy-proxy-doh.conf` contains `[General]`, `[Host]`, `[Rule]`, proxy DoH, `block-quic = all-proxy`, and final non-empty line `FINAL,PROXY`
- PASS - `local/private-configs/desktop-import-2026-07-01/S1-default-lazy-proxy-doh.conf` does not contain `[URL Rewrite]` or `[MITM]`
- PASS - `local/private-configs/desktop-import-2026-07-01/S1-default-lazy-proxy-doh.conf` includes `DOMAIN-SUFFIX,browserleaks.com,PROXY` before China-local `DIRECT` and lazy rule body
- PASS - generated `local/private-configs/desktop-import-2026-07-01/S2-default-strict-app-whitelist.conf`
- PASS - `local/private-configs/desktop-import-2026-07-01/S2-default-strict-app-whitelist.conf` contains `[General]`, `[Host]`, `[Rule]`, proxy DoH, `block-quic = all-proxy`, and final non-empty line `FINAL,PROXY`
- PASS - `local/private-configs/desktop-import-2026-07-01/S2-default-strict-app-whitelist.conf` does not contain `[URL Rewrite]`, `[MITM]`, or `GEOIP,CN,DIRECT`
- PASS - generated `local/private-configs/S1-1-default-lazy-stabilized-logfix.conf`
- PASS - `local/private-configs/S1-1-default-lazy-stabilized-logfix.conf` contains `[General]`, `[Proxy]`, `[Proxy Group]`, `[Host]`, `[Rule]`, proxy DoH, `block-quic = all-proxy`, and final non-empty line `FINAL,PROXY`
- PASS - `local/private-configs/S1-1-default-lazy-stabilized-logfix.conf` is under ignored `local/private-configs/` and is not part of public templates

## 文档规则

- PASS - `AGENTS.md` records S group naming and non-final boundary
- PASS - `README.md` records current state: A/B/C/D retained as diagnostics, S0/S1/S1.1/S2 added as scenario verification
- PASS - `docs/research-notes.md` records that Johnshall is `[Rule]` source, not pure China whitelist
- PASS - `docs/research-notes.md` records S1.1 rule-source governance, AI self-maintained list, and manual Issue/PR confirmation loop
- PASS - `docs/scenario-cn-us-account-v0.md` defines local-file import first and public-link import only after enablement
- PASS - `docs/scenario-cn-us-account-v0.md` clarifies public S0 is a rule template and mobile testing needs a private merged full config
- PASS - `docs/scenario-cn-us-account-v0.md` distinguishes China whitelist DNS from overseas/unknown DNS failure
- PASS - `references/johnshall-whitelist-sources.md` records upstream source, adopted scope, excluded scope, and license
- PASS - `references/johnshall-lazy-sources.md` records S1/S2 lazy source, adopted scope, excluded scope, risk notes, and license
- PASS - `references/rule-source-registry.md` records S1.1 monitored runtime and reference sources
- PASS - `references/s2-strict-app-whitelist-sources.md` records S2 strict whitelist source, adopted scope, excluded scope, risk notes, and license

## 结论

本地静态检查和线上闭环检查通过。S0 公开规则模板、S1 lazy 规则增强模板、S1.1 规则源治理增强模板、S2 严格中国 App 白名单模板、生成脚本、规则源监控脚本、确认后 PR 脚本、GitHub Actions 和私有合并脚本已准备好；私有测试文件已统一收纳到 `local/private-configs/`，不再放桌面。S1 保留为稳定对照组，S2 保留为严格白名单参考，当前主线是 S1.1。私有完整配置、节点、订阅、账号、代理组没有进入仓库或 GitHub Pages；公开链接只发布不含节点和代理组的 S1.1 模板。

S1.1 第二轮日志修正已进入公开模板：删除 `hijack-dns` 中的中国 DNS，新增中国 App 日志域名 `[Host] + DIRECT`，新增海外 SDK/服务域名前置 `PROXY`，并把不确定域名只记录为候选。旧 S1 对照组未覆盖。

- GitHub Pages S1.1 模板：`https://nihongbin.github.io/Shadowrocket-gz-gaizao/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`
- raw GitHub 备用链接：`https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S1-1-scenario-cn-us-lazy-stabilized-v0.conf`
- 线上模拟通知 Issue：`https://github.com/nihongbin/Shadowrocket-gz-gaizao/issues/1`
- 线上模拟确认 PR：`https://github.com/nihongbin/Shadowrocket-gz-gaizao/pull/2`
