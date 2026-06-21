# 出口代理(EGRESS_PROXY)

采集器支持把所有外发请求经一个代理转发,由环境变量 `EGRESS_PROXY` 配置,留空=直连。
代理与厂商无关——你给什么代理就走什么。**建议指向你自己拥有/付费的代理**(可追溯、稳定)。

```bash
# 直连(默认)
python3 run.py

# 走代理
EGRESS_PROXY="http://user:pass@host:port" python3 run.py
EGRESS_PROXY="socks5://127.0.0.1:1080"    python3 run.py   # SOCKS 需 httpx[socks]
```

## 推荐:用你自己的国内服务器当出口

这样拿到的是你**自有、实名、干净**的国内 IP,合规且稳定。两种做法:

**① SSH 动态转发(最省事,服务器零安装)**
```bash
# 本机起一个到国内服务器的 SOCKS5 隧道
ssh -D 1080 -N user@your-china-server
# 另开一个终端
export EGRESS_PROXY="socks5://127.0.0.1:1080"
python3 run.py
```

**② 在国内服务器装 HTTP 代理(tinyproxy / squid,带账号密码)**
```bash
export EGRESS_PROXY="http://user:pass@your-china-server:8888"
python3 run.py
```

## 付费/授权代理服务

```bash
export EGRESS_PROXY="http://user:pass@gateway.provider.com:port"
```

## 验证出口 IP

```bash
EGRESS_PROXY="..." python3 - <<'PY'
import os, httpx
print("出口 IP:", httpx.Client(proxy=os.environ["EGRESS_PROXY"], timeout=15).get("https://api.ipify.org").text)
PY
```

> 提示:免费匿名公共代理多为失效/极慢,且经其中转的流量可被记录或篡改;
> 配上本项目的"礼貌慢爬"只会频繁超时。要稳定免费的国内出口,自有轻量服务器是更好的选择。
