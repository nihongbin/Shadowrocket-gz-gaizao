# V5 MVP 用户测试与反馈模板

本文用于 S5 V5 MVP 公开模板的用户导入、测试和反馈。不要上传节点、订阅、账号、完整 IP、截图或任何可识别个人身份的信息。

## 当前版本

- 公开模板：`configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- 本地生成脚本：`scripts/build-v5-mvp-template.py`
- 私有合并脚本：`scripts/merge-s0-private-config.py --v5-mvp`
- 当前 V5 基盘 SHA256：`D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD`

S5 公开模板只包含规则、DNS 和 Host 逻辑，不包含节点、订阅、账号或代理组。用户必须自备 Shadowrocket 节点或订阅。

## 本地生成

生成或检查公开模板：

```powershell
python scripts\build-v5-mvp-template.py --check
python scripts\build-v5-mvp-template.py
```

把用户自己的完整 Shadowrocket 配置和 S5 公开模板合并为本机私有完整配置：

```powershell
python scripts\merge-s0-private-config.py --base local\private-configs\your-complete-shadowrocket.conf --v5-mvp --output local\private-configs\your-v5-mvp-private.conf
```

私有完整配置只能保存在 `local/private-configs/`，不得复制到 `configs/`、`docs/`、`references/` 或 GitHub Pages 公开目录。

## 公开更新

- raw GitHub 链接在提交并推送后可用：
  `https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/configs/S5-scenario-cn-us-v5-mvp-v0.conf`
- GitHub Pages S5 链接需要修改 Pages workflow 后才会发布；本轮未修改 GitHub Actions。
- 任何 GitHub Actions、远程推送或公开发布都按项目红线单独确认。

## 手机测试前提

- Shadowrocket 全局路由选择“配置”。
- 固定同一个节点国家/地区，优先从美国节点开始。
- 同一轮测试不要频繁换节点。
- 切换配置后，先断开 Shadowrocket，再重新连接。
- 先测 Wi-Fi，再测蜂窝；不要混合记录。

## 基础验证

中国 App：

- 微信、支付宝、淘宝、小红书、抖音、B 站、高德、Apple 基础服务。
- 记录是否能打开首页、图片、视频、评论、地图或支付相关页面。
- 日志中中国 App 相关域名应优先命中 `DIRECT`，对应 Host 应走 `223.5.5.5` 或 `119.29.29.29`。

海外 App：

- YouTube、TikTok、X、Instagram、Facebook、ChatGPT、Claude、Gemini。
- 日志中核心域名应命中 `PROXY`。
- 如果首次打开慢、第二次打开快，先记录为冷启动或缓存现象，不直接判定规则错误。

DNS / 测试站：

- `browserleaks.com`
- `dnsleaktest.com`
- `ipleak.net`
- `ippure`

测试站主域名应命中 `PROXY`。中国 App 白名单域名使用中国 DNS 不算失败；海外、未知、AI、测试站出现中国本地运营商 DNS 才算失败。

## 反馈模板

请只填写文字，不上传截图。

```text
使用版本：
网络环境：Wi-Fi / 蜂窝
节点国家/地区：美国 / 其他国家或地区
测试时间段：上午 / 下午 / 晚高峰 / 深夜

出现问题的 App：
具体页面或动作：
问题表现：打不开 / 首次慢第二次快 / 图片慢 / 视频慢 / 评论慢 / 登录慢 / 其他

Shadowrocket 日志相关域名：
- 域名：
- 命中策略：DIRECT / PROXY / FINAL,PROXY
- 如果有 DNS 记录：DNS 国家/地区或服务商，不写完整 IP

是否只在蜂窝出现：
是否换节点后改善：
DNS 测试站主域名是否命中 PROXY：
是否看到中国本地运营商 DNS：

补充说明：
```

## 回滚标准

出现以下任一情况，回滚到当前 V5 私有基准或上一版已验证可用配置：

- YouTube、TikTok、X、ChatGPT 核心域名出现 `DIRECT`。
- 海外 App 大面积打不开。
- 中国 App 大面积打不开。
- 测试站主域名没有命中 `PROXY`。
- 海外、未知、AI 或测试站域名出现中国本地运营商 DNS。
