# wechat2rss 自建部署（把 13 个公众号变成可抓的 RSS）

> 目标：搭一个自己的 wechat2rss 服务，为每个公众号生成一个 RSS 地址，
> 再填回 `config/sources.yaml`，系统就能像抓普通网站一样抓公众号。

## 原理回顾

微信公众号没有官方对外接口。wechat2rss 用**一个已登录的微信凭证**，定期拉取指定公众号
最新文章，组装成标准 RSS 输出。⚠️ 属非官方方案，**请用专门的微信小号**做抓取端。

## 方案 A：Docker 自建（推荐）

> 下面以社区常见的 wechat2rss 镜像为例。不同项目参数略有差异，以其官方文档为准。

```yaml
# docker-compose.yml
services:
  wechat2rss:
    image: rachelos/wechat2rss:latest      # 以实际可用镜像为准
    container_name: wechat2rss
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data                    # 持久化登录态与缓存
    restart: unless-stopped
```

```bash
docker compose up -d
# 打开 http://<服务器IP>:8080 ，按页面提示扫码登录“抓取用小号”
```

登录后，在后台**添加公众号**（按名称搜索，如「建哥聊安全」），
每个号会得到一个订阅地址，形如：
```
http://<你的IP>:8080/feed/<公众号ID>.xml
```

## 方案 B：用现成的托管服务

网上有第三方托管的 wechat2rss（部分收费或有额度）。拿到每个号的 feed 地址即可，
无需自己部署。稳定性取决于服务方。

## 拿到地址后：回填 sources.yaml

把每个号的 RSS 地址填进 `config/sources.yaml` 对应条目的 `rss_url`：

```yaml
  - id: wx_jiangelaoanquan
    type: wechat_rss
    name: "建哥聊安全"
    rss_url: "http://<你的IP>:8080/feed/xxxx.xml"   # ← 填这里
    weight: 1.3
    enabled: true
```

需要填的 13 个号（当前 `rss_url` 都为空）：

| id | 公众号 | 已知微信号 |
|----|--------|-----------|
| wx_jiangelaoanquan | 建哥聊安全 | — |
| wx_heikechahuahui | 黑客茶话会 | — |
| wx_hackingheibaihong | Hacking 黑白红 | `Hacking012` |
| wx_zhibaishouhei1024 | 知白守黑 1024 | — |
| wx_wangkongxianhua | 网空闲话 plus | — |
| wx_chaojinaodong | 超级脑洞 f | `gh_0c1a1d4be5ef` |
| wx_aweijianggongfang | 阿伟讲攻防 | — |
| wx_hellogithub | HelloGitHub | 官网亦有 RSS |
| wx_githubdaily | GitHubDaily | — |
| wx_guangguangwgithub | 逛逛 GitHub | — |
| wx_githubzhongwen | Github 中文社区 | githubs.cn |
| wx_paddlepaddle | 飞桨 PaddlePaddle | — |
| wx_heibaizhimao | 黑白之猫 | — |

> 已知微信号（`gh_`/微信号）能帮 wechat2rss 更快定位到号。
> 把 13 个地址发我，我可以一次性帮你填好，你就不用手动改 yaml。

## 验证

```bash
PYTHONPATH=src python -m digest sources    # 对应公众号应从 ⏳ 变 ✅
PYTHONPATH=src python -m digest preview    # 预览里能看到公众号文章
```

## 小贴士

- 抓取小号别频繁登录别处，降低风控。
- wechat2rss 拉取频率别太高（默认即可），避免被限。
- HelloGitHub / Github 中文社区 有官网 RSS，可优先用官方源，绕开 wechat2rss。
