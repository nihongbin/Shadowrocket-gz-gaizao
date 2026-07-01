# iPhone 14 实机验证步骤

本文件给普通用户使用。目标是验证配置是否能降低常见 DNS 泄露风险，并确认没有明显影响日常可用性。

## 测试前准备

1. 使用同一台 iPhone 14。
2. 使用同一个 Shadowrocket 节点。
3. 确保三组测试期间不更换节点、不更换订阅、不切换代理策略。
4. 每导入一组配置后，先断开 Shadowrocket，再重新连接。
5. Wi-Fi 和蜂窝网络要分别测试。
6. 不要上传测试截图到公开仓库；截图可能包含 IP、运营商或地理位置。

## 三组配置

- A：`configs/A-johnshall-sr_cnip_ad.conf`
- B：`configs/B-nznl31-a-nomad.conf`
- C：`configs/C-sr_cnip_ad_privacy_hardened_candidate.conf`

## 每组都要做的测试

1. 出口 IP：
   - 打开 `https://ipinfo.io`
   - 记录显示的国家/地区和 IP。
2. DNS 测试：
   - 打开 `https://www.dnsleaktest.com`
   - 先点 Standard test。
   - 再打开 `https://ipleak.net` 复核。
   - 记录是否出现本地运营商 DNS。
3. IPv6 测试：
   - 打开 `https://test-ipv6.com`
   - 记录是否暴露本机真实 IPv6。
4. WebRTC 开关确认：
   - 先确认 Shadowrocket 自带 WebRTC/STUN 防泄露开关已开启。
   - 打开 `https://browserleaks.com/webrtc`
   - 只记录开关是否生效；这不是 C 组配置的验收目标。
5. 硬编码 DNS 观察：
   - 打开 Shadowrocket 日志或连接记录。
   - 观察是否出现 `8.8.8.8:53`、`8.8.4.4:53`、`1.1.1.1:53`、`1.0.0.1:53` 这类明文 DNS 目标。
   - 如果没有应用触发这类请求，记录为“未触发，无法验证”。
6. 可用性检查：
   - 打开一个国内网站。
   - 打开一个国外网站。
   - 打开 App Store 或 Apple 服务。
   - 打开一个支付、银行或地图类 App。
   - 记录是否明显异常。

## 判定方式

- C 组 DNS 结果优于 A 组，且可用性正常：C 组候选项可能进入最终 v1。
- B 组有效但 C 组无效：只记录现象，不直接复制 B 组整套配置。
- 三组都暴露本地 DNS：说明问题可能不在这几个配置项，需要继续调研。
- WebRTC 暴露：优先检查 Shadowrocket 自带开关，不把它算作 C 组配置失败。

## 测试后发给我的信息

按下面格式发，不要发包含敏感信息的截图：

```text
设备：iPhone 14
Shadowrocket 版本：
节点国家/地区：
网络：Wi-Fi / 蜂窝

A 组：
出口 IP 地区：
DNS 结果：
IPv6 结果：
WebRTC 开关：
可用性问题：

B 组：
出口 IP 地区：
DNS 结果：
IPv6 结果：
WebRTC 开关：
可用性问题：

C 组：
出口 IP 地区：
DNS 结果：
IPv6 结果：
WebRTC 开关：
可用性问题：
```
