# V5/S5 手机测试与反馈

不要上传节点、订阅、账号、完整 IP、截图或任何可识别个人身份的信息。

## 当前版本

- 私有实测基盘：`S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf`
- 公开模板：`S5-scenario-cn-us-v5-mvp-v0.conf`
- 当前公开模板 `manifest_revision`：`00CB8614DD7006F3A8336323C6A14E4DA78E566447552E8D5128D630005DE94E`。
- 本版本首次把 33 个第三方 `RULE-SET` URL 改为本仓库受控快照；规则策略和顺序未变。
- 公开模板文件头包含 `manifest_revision`，反馈时请一并填写。

## 测试前提

- Shadowrocket 全局路由选择“配置”。
- 固定同一个节点国家/地区，同一轮不要频繁换节点。
- 切换配置后断开 Shadowrocket，再重新连接。
- Wi-Fi 和蜂窝分开记录。
- 首次使用本版本时，在 Shadowrocket 规则集页面确认相关 URL 可加载；红叉或长期加载失败要记录规则集名称和 URL 类型，不上传节点信息。

## 中国 App

测试微信、支付宝、淘宝、小红书、抖音、B 站、高德、美团、华为相关服务等实际使用页面。

通过标准：

- 首页、图片、视频、评论、地图或支付页面正常。
- 新增中国根域应命中 `DIRECT`。
- 对应 Host 使用 `223.5.5.5` 或 `119.29.29.29`。

## 海外 App

测试 YouTube、TikTok、X、Instagram、Facebook、ChatGPT、Claude 和 Gemini。

通过标准：

- 核心域名命中 `PROXY` 或 `FINAL,PROXY`。
- 不出现核心海外域名命中 `DIRECT`。
- 首次慢、第二次快要单独记录，不能直接归因于规则。

## DNS 辅助验证

可使用 `browserleaks.com`、`dnsleaktest.com`、`ipleak.net` 和 `ippure`。

- 测试站主域名必须命中 `PROXY`。
- 中国白名单域名使用中国 DNS 不算失败。
- 海外、未知、AI 或测试站出现中国本地运营商 DNS 才算失败。

## 反馈模板

```text
使用文件名：
manifest_revision：
网络环境：Wi-Fi / 蜂窝
节点国家/地区：
测试时间段：

出现问题的 App：
具体页面或动作：
表现：打不开 / 首次慢第二次快 / 图片慢 / 视频慢 / 登录慢 / 其他

相关域名：
命中策略：DIRECT / PROXY / FINAL,PROXY
DNS 国家/地区或服务商：不写完整 IP
相关 RULE-SET 状态：成功 / 失败 / 未观察

是否只在蜂窝出现：
是否换节点后改善：
测试站主域名是否命中 PROXY：
是否看到中国本地运营商 DNS：
```

## 回滚条件

出现以下任一情况，回滚到已实测 V5：

- YouTube、TikTok、X 或 ChatGPT 核心域名命中 `DIRECT`。
- 海外 App 或中国 App 大面积打不开。
- 测试站主域名未命中 `PROXY`。
- 海外、未知、AI 或测试站出现中国本地运营商 DNS。
