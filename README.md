# NogizakaBlog
想下载乃团成员的博客(日语)就写了这个脚本，__并没有字幕组的翻译文本__
大部分博客因为超过20天的原因无法下载原图，因此只有略缩图，大概从2013年6月份开始，2011年11月份到2013年6月的原图还是有的

## 使用方法
首先clone本项目 python版本为3.5.1</br>
确认安装了beautifulsoup和requests,然后根据需求运行下列命令之一</br>
1. `` python nogizakablog.py`` 下载全员至今的博客
2. ``pyhon nogizakablog.py mai.shiraishi`` 下载白石麻衣至今的博客
3. `` python nogizakablog.py update`` 下载全员本月的博客</br>
4. `` python nogizakablog.py mai.shiraishi,misa.eto -m 201708,201503`` 下载白石麻衣和卫藤美彩2017/08和2015/03的博客 至于成员的罗马名就请自己去找了
成员名称与下载日期之间必须加上逗号</br>
5. `` python nogizakablog.py mai.shiraishi,misa.eto -y 2017,2016`` 下载白石麻衣和卫藤美彩2016年和2017年的博客
