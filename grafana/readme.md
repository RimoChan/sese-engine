# 接入Grafana步骤

sese-engine内置了prometheus-client，所以要看监控要用到Grafana和Prometheus服务。

好在我们可以去grafana.net注册一个免费帐号。免费的空间很小，不过对sese-engine来说足够了。

我也是刚学的，不保证包教包会，遇到问题就自己摸索吧。


## 1. 注册grafana帐号

打开grafana.net，注册一个帐号。


## 2. 添加数据源

注册好帐号之后，点击「+ Connect data」添加一个数据源，选择「Hosted Prometheus metrics」。

接下来根据网页上的提示，一步步填写即可。其中有一个它让你复制配置到本地的，那个地方有`- targets: ['localhost:9100']`，得把它换成`- targets: ['localhost:14950', 'localhost:14951']`，这两个是sese-engine的prometheus端口。


## 3. 添加面板

添加好数据源之后，新建一个Dashboard，但不是空白的，而是选择「Import」，然后把`model.json`里的内容粘贴进去，点击「Load」即可。
