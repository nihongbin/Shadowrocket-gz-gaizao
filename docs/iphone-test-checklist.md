# iPhone 14 实测清单

当前状态：老倪已反馈 A/B/C 三组全部失效，当前进入 D0/D1/D2 DNS 诊断。不要把 C 组或 D 组当作最终配置发布。

D 组测试请优先使用：

- `docs/dns-diagnostic-matrix.md`
- `docs/dns-failure-intake.md`

## 测试前固定条件

- 设备固定为同一台 iPhone 14。
- Shadowrocket 固定为同一个版本。
- 三组都使用同一个代理节点。
- Wi-Fi 测试固定同一个 Wi-Fi。
- 蜂窝测试固定同一张 SIM 和同一位置。
- 每组测试前都先断开 Shadowrocket，再重新连接。
- 不上传含 IP、运营商、地理位置或账号信息的截图。

## Wi-Fi 测试

1. 导入 `configs/A-johnshall-sr_cnip_ad.conf`。
2. 选择同一个节点，断开并重新连接 Shadowrocket。
3. 测 `ipinfo.io` 或 `ip.sb`，记录出口 IP 地区。
4. 测 `dnsleaktest.com` 和 `ipleak.net`，记录 DNS 服务商和地区。
5. 测 `test-ipv6.com`，记录是否暴露 IPv6。
6. 确认 Shadowrocket 自带 WebRTC/STUN 防泄露开关已开启，再测 `browserleaks.com/webrtc`。
7. 打开 Shadowrocket 日志，观察是否出现 `8.8.8.8:53`、`8.8.4.4:53`、`1.1.1.1:53`、`1.0.0.1:53`。
8. 测国内网站、国外网站、App Store、支付/银行/地图类 App 是否明显异常。
9. 对 B 组和 C 组重复 1-8。

## 蜂窝网络测试

1. 关闭 Wi-Fi，切到蜂窝网络。
2. 对 A/B/C 三组完整重复 Wi-Fi 测试步骤。
3. 记录蜂窝结果是否和 Wi-Fi 有明显差异。

## 测完后发回的信息

```text
设备：iPhone 14
Shadowrocket 版本：
节点国家/地区：

Wi-Fi：
A 组 DNS / IPv6 / 可用性：
B 组 DNS / IPv6 / 可用性：
C 组 DNS / IPv6 / 可用性：

蜂窝：
A 组 DNS / IPv6 / 可用性：
B 组 DNS / IPv6 / 可用性：
C 组 DNS / IPv6 / 可用性：

是否看到硬编码 DNS 目标：
WebRTC/STUN 开关是否生效：
```

## 进入最终 v1 的判断

- C 组优于 A 组，且没有明显可用性问题：候选项可考虑进入最终 v1。
- B 组优于 C 组：继续拆解 B 组有效原因，不直接照搬整套 B。
- 无法触发硬编码 DNS：该项记录为未验证，不作为通过项。
- WebRTC 暴露：先检查 Shadowrocket 自带开关，不算 C 组配置失败。
