# 【sese-engine】新时代的搜索引擎！

大家平时都会用百度和谷歌来搜索资料吧。不过大家有没有怀疑过，也许它们不那么可信？

百度很坏，之前也有和竞价排名相关的丑闻。谷歌好一点，它说它不作恶，但我也不完全相信它，毕竟每个人的善恶观本身就不同。我想，它们或多或少都藏起了一些什么。

那怎么办呢？

我发明了强大并且安全的sese-engine。它是一个轻量级的搜索引擎，可以快速部署在个人电脑上。

sese-engine通过爬取互联网上的数据，在本地建立各个网页的索引。这样一来，你就有了自己的搜索引擎，可以在本地直接搜索互联网上的信息。你也可以修改你的爬取和搜索配置，让搜索的结果能满足个性化的需求。

数据即未来，我们的未来要掌握在自己手中。

<img align='right' src='https://upyun.yunyoujun.cn/images/sese-rimo-and-xiao-yun.png' width='320px'>


## 测试环境

一起来玩吧: https://sese.yyj.moe

对了，服务器是1年70元租的机器，配置很低。所以第一次查询可能会卡几秒，这是正常现象，大概率是服务进程被交换到硬盘里了。


## 部署

只需要1个Python3.8。数据库什么的都不用装，配环境很方便，好耶！

具体步骤是这些: 

1. 安装1个Python3.8

    Python版本太高的话，下一步会有依赖装不上。

2. 用pip安装依赖

    ```sh
    pip install -r requirements.txt
    ```

3. 运行启动脚本
    
    搜索引擎在windows和linux上都可以运行，所以有两个可选的启动脚本 `启动.cmd` 和 `启动.sh`。


这样你的搜索引擎服务应该就可以用了，你可以 `curl http://127.0.0.1/search?q=test` 试一下。

然后前端的仓库在这里: [YunYouJun/sese-engine-ui](https://github.com/YunYouJun/sese-engine-ui)。前端怎么部署呢，去看看云游君怎么说吧。

如果你想用docker部署的话，也可以参照: [xiongnemo/sese-engine-docker](https://github.com/xiongnemo/sese-engine-docker)。


## 代价

sese-engine的消耗不大，一个便宜的服务器或者树莓派就够用了。

默认配置下，sese-engine的爬虫大约需要1\~2个CPU和1\~2G的内存，搜索服务几乎没有消耗。如果你不想占用太多服务器资源，也可以根据 `配置.py` 里的注释调整各种类资源的使用量。

如果你需要使用代理，可以根据`启动.cmd`或`启动.sh`里的注释调整代理

推荐的服务器配置如下: 

- 2核CPU

- 4G内存

- 128G硬盘

- 5Mbps带宽


## 设计文档

设计文档在这里: [设计文档](./doc/readme.md)


## 赞助

如果你觉得sese-engine对你的工作或学习有帮助，欢迎来当我的女朋友。

要可爱的，最好是白发贫乳傲娇双马尾。
