# DNS 失败现象采集表

本文件用于把手机端失败现象用文字记录下来。不要粘贴含完整 IP、运营商账号、地理位置、节点名称或订阅信息的截图。

## 基本信息

```text
设备：iPhone 14
Shadowrocket 版本：
当前网络：Wi-Fi / 蜂窝
节点国家/地区：
Shadowrocket 模式：配置 / 全局代理 / 全局直连 / 其他
IPv6：已关闭
```

## A/B/C 失败现象

```text
A 组：
出口地区：
DNS 是否显示本地运营商：
WebRTC 开关是否生效：
主要异常：

B 组：
出口地区：
DNS 是否显示本地运营商：
WebRTC 开关是否生效：
主要异常：

C 组：
出口地区：
DNS 是否显示本地运营商：
WebRTC 开关是否生效：
主要异常：
```

## D 组诊断结果

```text
D0：
出口地区：
DNS 服务商/地区/数量：
是否显示本地运营商 DNS：
browserleaks.com/dns 是否显示泄露：
IPPure 是否显示泄露：
Shadowrocket 日志关键词：
可用性问题：

D1：
出口地区：
DNS 服务商/地区/数量：
是否显示本地运营商 DNS：
browserleaks.com/dns 是否显示泄露：
IPPure 是否显示泄露：
Shadowrocket 日志关键词：
可用性问题：

D2：
出口地区：
DNS 服务商/地区/数量：
是否显示本地运营商 DNS：
browserleaks.com/dns 是否显示泄露：
IPPure 是否显示泄露：
Shadowrocket 日志关键词：
可用性问题：

D3：
出口地区：
DNS 服务商/地区/数量：
是否显示本地运营商 DNS：
browserleaks.com/dns 是否显示泄露：
IPPure 是否显示泄露：
Shadowrocket 日志关键词：
可用性问题：
```

## 日志关键词

只记录是否出现，不记录完整地址或截图：

- `system`
- `8.8.8.8:53`
- `8.8.4.4:53`
- `1.1.1.1:53`
- `1.0.0.1:53`
- `doh`
- `dot`
- `doq`
- `cloudflare-dns.com`
- `dns.google`

## 初步归类

把失败归到最接近的一类：

- 配置未生效：出口地区不是代理节点所在地。
- DNS 参数无效：出口地区正常，但 DNS 一直显示本地运营商。
- 测试口径误判：DNS 显示的是配置里的 DoH 服务商，不是本地运营商。
- 进阶参数有效但有副作用：D2 DNS 更好，但国内 App、Apple 服务、支付/银行/地图异常。
- 仍无法判断：三组表现接近，日志也看不出差异。
