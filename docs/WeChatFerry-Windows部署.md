# WeChatFerry 部署（个人微信群推送 · Windows）

把每日重点发进你**平时用的个人微信群**。这是目前最稳的个人微信自动化方案。

> ⚠️ **非官方 hook，有封号风险**。务必用一个微信**小号**登录电脑版微信当机器人，别用主号。

## 为什么要 Windows

WeChatFerry 通过 hook **Windows 电脑版微信**工作，所以需要一台 Windows：
- 云服务器买 **Windows Server**（2019/2022 均可），2 核 4G 起步够用；或
- 一台自己的 Windows 电脑/常开的小主机。
- ⚠️ Linux 云服务器**跑不了** WeChatFerry。主程序（digest）可以在 Linux，但 WeChatFerry 必须 Windows。

## 部署步骤（Windows 服务器上）

1. **装电脑版微信**：WeChatFerry 对微信版本敏感，装它文档指定的版本（跟随
   [WeChatFerry Releases](https://github.com/lich0821/WeChatFerry) 说明），用**小号**登录。
2. **把小号拉进目标群**（你要接收每日重点的那个微信群）。
3. **装并启动 wcfhttp**（Python 3.x）：
   ```bat
   pip install wcfhttp
   wcfhttp --host 0.0.0.0 --port 9999
   ```
   启动后浏览器打开 `http://localhost:9999/docs` 能看到接口文档（Swagger）。
4. **放行端口 9999**（Windows 防火墙 + 云服务器安全组），让 digest 能访问到。

## 找到目标群的 room id

`WCF_RECEIVER` 需要群的 **room id**（形如 `12345678@chatroom`），不是群名称。
在 Windows 服务器上跑一小段脚本打印所有群：

```python
from wcferry import Wcf
wcf = Wcf()
for c in wcf.get_contacts():
    # 群聊的 wxid 以 @chatroom 结尾
    if str(c.get("wxid", "")).endswith("@chatroom"):
        print(c["wxid"], "->", c.get("name"))
wcf.cleanup()
```

找到你的群名对应的 `xxxxx@chatroom`，就是 `WCF_RECEIVER`。

## 回填 .env

```
WCF_HTTP_ENDPOINT=http://<Windows服务器公网IP>:9999
WCF_RECEIVER=12345678@chatroom
```

digest 主程序（可在任意 Linux/Windows 上）跑 `python -m digest run` 时，
就会把每日重点 POST 到 wcfhttp，由小号发进群。

## 验证

```bash
# 先单独测通 wcfhttp（在能访问到它的机器上）：
curl -X POST http://<IP>:9999/text \
  -H "Content-Type: application/json" \
  -d '{"msg":"测试：每日重点连通","receiver":"12345678@chatroom","aters":""}'
# 群里收到就说明通了，然后：
PYTHONPATH=src python -m digest run
```

## 常见问题

- **发不出去**：确认小号在群里、wcfhttp 正在运行、9999 端口放行、receiver 是 `@chatroom` id。
- **微信版本不对**：装 WeChatFerry 指定版本的电脑微信，别自动升级。
- **封号**：用小号；控制发送频率（每天一两次没问题）；别群发骚扰。
- **不想搞 Windows**：改用 `docs/接入清单.md` 里的 wechaty(web协议，登录不稳) 或 Server酱(推给你自己，不进群)。
