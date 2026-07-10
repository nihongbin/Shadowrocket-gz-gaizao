# V5 试错记录

本文记录 2026-07-02 围绕 V5 私有实测配置做过的短分支试错，避免后续误把未证明有效的测试版当作新基盘。

## 当前基准

- 当前唯一基准：`local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- V5 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`
- V5 仍按本地私有基盘管理；当前文件未检测到 `[Proxy]` 或 `[Proxy Group]`，但仍不得直接上传，公开内容统一由 S5 生成链输出。
- 后续新增测试版必须从 V5 复制生成，不能从 DNS B、QUIC 或旧 S1.1 模板继续派生。
- 2026-07-10 已从当前文件树删除所有旧测试配置；本文件只保留决策证据，不代表旧版本仍可使用。

## 已作废分支

### DNS B Google Fallback

- 测试文件：`S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5-dnsB-google-fallback.conf`
- 唯一变量：把 `fallback-dns-server` 从 Cloudflare-only 改成 Google + Cloudflare。
- 测试结论：日志中没有看到 `https://dns.google/dns-query#proxy` 被触发。
- 判断：本次测试的实际 DNS 路径基本等同 V5，不能把速度变化归因于 Google fallback。
- 状态：老倪已删除该测试文件；后续不作为基盘。

### QUIC Allow

- 测试文件：`S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5-quic-allow.conf`
- 唯一变量：把 `block-quic = all-proxy` 改成允许 QUIC。
- 测试结论：没有看到海外核心域名误走 `DIRECT`，但样本量较小，也没有证明海外 App 速度明显改善。
- 判断：该分支没有暴露明显副作用，但不足以证明值得替代 V5。
- 状态：老倪已删除该测试文件；后续不作为基盘。

## 关键日志判断

- 朋友导出的 V5 配置与本地 V5 规则主体一致；问题不是用错配置。
- V5 蜂窝日志里，TikTok、YouTube/Google、X/Twitter、Meta、OpenAI/ChatGPT、Claude 等海外核心域名都命中 `PROXY`，没有观察到海外主链路直连。
- X/Twitter 相关域名，包括 `x.com`、`api.x.com`、`twitter.com`、`api.twitter.com`、`api-stream.twitter.com`、`pbs.twimg.com`、`video.twimg.com`、`video-s.twimg.com`，均命中 `PROXY`，没有观察到 `DIRECT` 或 `FINAL,PROXY`。
- 朋友反馈“第一次打开页面卡很久，后面再打开很快”，更像首次建链、DNS/连接缓存、媒体缓存、蜂窝链路或节点到平台 CDN 的冷启动问题，不像规则缺失。
- Wi-Fi 快、蜂窝慢时，优先怀疑蜂窝到美国节点链路、节点晚高峰、节点到海外平台 CDN 的质量；不要直接归因到域名规则。
- V5 蜂窝日志里曾出现少量中国服务域名本应 `DIRECT` 但落到 `FINAL,PROXY` 的现象，且部分 DNS 结果为空；这类问题后续应通过真实日志补中国 App 域名或处理 App 自带 HTTPDNS/IP 请求，而不是扩大海外 DNS 或 QUIC 实验。

## 后续决策

- V5 是当前唯一基准。
- DNS B 和 QUIC 两个短分支已作废，只保留试错结论。
- 下一轮不继续围绕 fallback DNS 或 QUIC 做默认分支。
- 后续只有两类情况才改 V5：
  - 中国 App 真实日志显示明确中国服务域名误走代理或缺 `[Host] + DIRECT`。
  - 海外 App、AI、流媒体、测试站真实日志显示核心域名误走 `DIRECT` 或未进入前置 `PROXY`。
- 如果海外 App 只是首次打开慢、第二次明显变快，优先做网络/节点/时段对照，不先改规则。

## 验证建议

- 同一个 V5、同一个网络、同一个美国节点，分别在晚高峰和非晚高峰测试 X/YouTube/TikTok。
- 对 X 重点记录第一次打开媒体页面和第二次打开同一页面的差异。
- 若换节点后明显改善，归因优先指向节点链路或平台 CDN，不改规则。
- 若所有节点在蜂窝都慢但 Wi-Fi 快，归因优先指向蜂窝网络或运营商链路。
- 若日志出现海外核心域名 `DIRECT`，再进入规则修正流程。
