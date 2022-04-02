# 【sese-engine】新时代的搜索引擎！

你是否想象过，在未来世界里，巨型企业控制着搜索引擎，它说谎成性，不仅偷取你的隐私，还使用虚假信息来操纵你的生活？

但好在这一切都可以逆转！

我们发明了强大并且安全的sese搜索引擎。它是一个轻量级的搜索引擎，可以轻松地部署在个人电脑上，有了它，你就可以在本地直接搜索互联网上的信息，再也不用担心这些问题啦！

<img align='right' src='https://upyun.yunyoujun.cn/images/sese-rimo-and-xiao-yun.png' width='320px'>


## 测试环境

一起来玩吧: http://sese.yyj.moe

对了，服务器是1年70元租的机器，有时候会卡住是正常现象。


## 部署

只需要1个Python3.8。数据库什么的都不用装，配环境很方便，好耶！

具体步骤是这些: 

1. 安装1个Python3.8

    Python版本太高的话，下一步会有依赖装不上。

2. 用pip安装依赖

    ```sh
    pip install -r requirements.txt
    ```

3. 运行 `启动.cmd`

    你肯定很奇怪为什么不是`.sh`，这是因为我买的服务器是windows的。


这样你的搜索引擎服务应该就可以用了，你可以 `curl http://127.0.0.1:4950/search?q=test` 试一下。

然后前端的仓库在这里: [YunYouJun/sese-engine-ui](https://github.com/YunYouJun/sese-engine-ui)。前端怎么部署呢，去看看云游君怎么说吧。


## 代价

sese-engine的消耗不大，一个便宜的服务器或者树莓派就够用了。

默认配置下，sese-engine的爬虫大约需要1~2个CPU和1~2G的内存，搜索服务几乎没有消耗。

此外，需要的硬盘空间会缓慢增长，尽管它会增长得越来越慢但并没有上界……所以最好给树莓派插一个移动硬盘。


## 赞助

如果你觉得sese-engine对你的工作或学习有帮助，欢迎来当我的女朋友。

要可爱的，最好是白发贫乳傲娇双马尾。
