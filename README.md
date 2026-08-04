# S5 Shadowrocket规则

面向 iPhone + Shadowrocket 的中国本地与代理分流模板。

确认过的中国 App 和中国服务优先直连；海外账号、AI、流媒体、测试站和未知流量交给代理兜底。S5 只表述为“降低常见 DNS 泄露风险，并提供验证流程”。

**[打开下载页面](https://nihongbin.github.io/Shadowrocket-gz-gaizao/)** · **[下载最新版 .conf](https://github.com/nihongbin/Shadowrocket-gz-gaizao/releases/latest/download/S5-scenario-cn-us-v5-mvp-v0.conf)** · **[查看版本记录](https://github.com/nihongbin/Shadowrocket-gz-gaizao/releases)**

## S5 能做什么

- 中国常用 App 使用本地 DNS 和直连规则，减少图片、视频和服务页面绕路。
- 海外账号、AI、流媒体和未知域名默认使用代理。
- 使用经人工确认的规则快照，第三方上游变化不会直接改变手机规则。
- 保留手机验证和问题反馈流程，便于根据真实日志维护。

## 使用前必须知道

S5 是公开规则模板，**不包含节点、订阅、账号或代理组**。使用前需要：

1. iPhone 已安装 Shadowrocket。
2. Shadowrocket 中已有可用节点或订阅。
3. 代理策略名称能够使用 `PROXY`。

## 下载和安装

1. 打开 [S5 下载页面](https://nihongbin.github.io/Shadowrocket-gz-gaizao/)，下载最新版配置，或复制在线配置地址。
2. 在 Shadowrocket 的“配置”页面导入下载的 `.conf` 文件或在线地址。
3. 选择 S5 配置，将首页“全局路由”设为“配置”。
4. 选择固定的美国节点，断开后重新连接 Shadowrocket。
5. 分别打开一个中国 App 和一个海外 App，确认两边都能正常访问。

更新版本时，先下载或更新配置，再断开并重新连接 Shadowrocket。当前配置有异常时，应先切回此前可用版本。

## 验证重点

- 中国 App 代表域名应命中 `DIRECT`。
- YouTube、TikTok、ChatGPT 等海外核心域名应命中 `PROXY` 或 `FINAL,PROXY`。
- 测试站主域名应命中 `PROXY`。
- 中国白名单域名使用中国 DNS 是设计目标，不单独视为泄露。

发现问题时，请使用 [S5 使用反馈](https://github.com/nihongbin/Shadowrocket-gz-gaizao/issues/new?template=s5-user-feedback.yml)。不要上传完整 IP、节点名、订阅、账号或含敏感信息的截图。

## 当前版本

- 版本：`S5 MVP v0.1.0`
- 配置：`S5-scenario-cn-us-v5-mvp-v0.conf`
- SHA256：`80F81FEF8619F4BD995D55C8020E5C0CF2C717DF8487050CDE75812AAE0A732A`
- `manifest_revision`：`00CB8614DD7006F3A8336323C6A14E4DA78E566447552E8D5128D630005DE94E`

<details>
<summary>维护者文档</summary>

- [生成与发布流程](docs/v5-mvp-release-runbook.md)
- [规则源治理](docs/v5-ruleset-governance.md)
- [手机测试与反馈](docs/v5-mvp-user-test-feedback.md)
- [研究和技术判断](docs/research-notes.md)
- [静态检查结果](docs/static-check-report.md)

本地私有 V5 不进入 GitHub。公开 S5 与私有 V5 的路由语义通过脚本逐条核对，公开版本只把远程规则地址替换为本仓库受控快照。

</details>

## 许可

S5 模板按 [CC BY-SA 4.0](LICENSE) 提供。`rulesets/v5/` 中由 blackmatrix7 派生的规则快照按其 GPL-2.0 许可单独保留许可证。
