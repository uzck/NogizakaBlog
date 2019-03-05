#!/usr/bin/python3
import re
import os
import os.path
import time
import datetime
import threading
import requests
import sys
from bs4 import BeautifulSoup


def download_member_blog(member_name, page, day):
    """下载博客的函数，分为下载图片和下载正文两部分"""
    create_dir(member_name.get('zh'))
    page_link = 'http://blog.nogizaka46.com/' + \
        member_name.get('jp') + arg + str(page) + arg1 + str(day)
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Host':
        'blog.nogizaka46.com',
        'Accept-Language':
        'zh-CH,zh;q=0.8,en-US;q=0.6,en;q=0.4,ja;q=0.2'
    }
    try:
        blog_page = requests.get(
            page_link, headers=headers, allow_redirects=False, timeout=(3, 3))
        print(page_link + ' ' + str(blog_page.status_code))
        if blog_page.status_code != 200:
            return
        result = BeautifulSoup(blog_page.text, 'html.parser')
        entries = result.find_all("div", class_="entrybody")
        heads = result.find_all("h1", class_="clearfix")
        for i in range(len(entries)):
            # 遍历图片url
            duplicate = 0
            blog_title_node = heads[i].find("span", class_="entrytitle")
            blog_title_author = heads[i].find("span", class_="author")
            blog_title = blog_title_node.get_text()  # 博客标题
            ref = blog_title_node.find('a').get('href')
            ref = split_ref(ref)
            blog_author = blog_title_author.get_text()  # 博客作者 区分三期生博客
            yearmonth = heads[i].find(
                "span", class_='yearmonth').get_text()  # 年 月
            daytime = heads[i].find('span', class_='dd1').get_text()  # 日
            image_urls = entries[i].find_all("a")
            image_urls_another_ver = entries[i].find_all("img")
            post_time = get_date(yearmonth)
            # 创建文件夹
            create_dir(member_name.get('zh') + '/' + post_time[0])
            create_dir(member_name.get('zh') + '/' +
                       post_time[0] + '/' + post_time[1])
            create_dir(member_name.get('zh') + '/' + post_time[0] + '/' + post_time[1] + '/' + daytime)
            if ref == '':
                return
            create_dir(member_name.get('zh') + '/' + post_time[0] + '/' + post_time[1] + '/' + daytime + '/' + ref)
            # 找到entries里有文本的div
            final_address = member_name.get('zh') + '/' + post_time[0] + '/' + post_time[1] + '/' + daytime + '/' + ref
            text_dives = entries[i].contents
            text_save_adress = member_name.get('zh') + '/' + post_time[0] + '/' + post_time[1] + '/' + daytime + '/' + ref + '/' + 'content.txt'
            download_text(text_dives, text_save_adress,
                          blog_title + '   ' + blog_author)
            if len(image_urls) > 0:
                # 托管的图片
                if image_urls[0].get('href').startswith(
                        'http://dcimg.awalker.jp'):
                    print("托管图片")    
                    for url in image_urls:
                        title = url.find_all('img')
                        if len(title) > 0:
                            info = get_image_file_name(title[0].get('src'))
                            if info != None:
                                file_name = final_address + '/' + info[3]
                                if not download_pic(url.get('href'), file_name, post_time, daytime):
                                    download_thumbnail(
                                        title[0].get('src'), file_name)
                elif image_urls[0].get('href').startswith(
                        'http://img.nogizaka46.com/blog/'):
                    for url in image_urls:
                        info = get_image_file_name(url.get('href'))
                        if info != None:
                            file_name = final_address + '/' + info[3]
                            download_from_original_site(
                                url.get('href'), file_name)
                else:
                    for url in image_urls:
                        url_string = url.get('href')
                        if url_string.startswith('http://dogatch.weblos.jp'):
                            inner_img = url.find('img').get('src')
                            info = get_image_file_name(inner_img)
                            file_name = final_address + '/' + info[3]
                            download_from_original_site(inner_img, file_name)
                        else:
                            info = get_image_file_name(url_string)
                            if info != None:
                                file_name = final_address + '/' + info[3]
                                download_from_original_site(url_string, file_name)
            if len(image_urls_another_ver) > 0:
                for image in image_urls_another_ver:
                    info = get_image_file_name(image.get('src'))
                    # print(image.get('src'))
                    if info != None:
                        file_name = final_address + '/' + info[3]
                        download_from_original_site(
                            image.get('src'), file_name)
    except:
        print('网络较差，无法获取博客  正在重新尝试')
        download_member_blog(member_name, page, day)


def get_date(yearmonth):
    """获取博客发表的年份与月份"""
    matcher = re.compile(r'(\d{4})/(\d{2})')
    result = matcher.match(yearmonth)
    if result:
        return (result.group(1), result.group(2))

def create_duplicate_dir(dir_name, duplicate):
    if duplicate == 0:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            for file in files:
                test = dir_name + '/' + file + '/content.txt'
                if not os.path.exists(test):
                    duplicate += 1
                    os.mkdir(dir_name + '(' + str(duplicate) + ')')
                else:
                    return 0
        else:
            os.mkdir(dir_name)
    return duplicate

def create_dir(dir_name):
    """创建文件夹"""
    if os.path.exists(dir_name):
        return False
    else:
        os.mkdir(dir_name)
        return True


def is_file_exisst(file_name):
    """判断图片是否已经下载过"""
    if os.path.isfile(file_name):
        return True
    else:
        return False


def download_pic(image_url, image_name, post_time, daytime):
    """从托管服务器下载图片 距离当前日期超过20天的无法下载"""
    if not is_file_exisst(image_name):
        try:
            if image_url.startswith("http://dcimg.awalker.jp/view"):
                result1 = requests.get(image_url)
                cookie = result1.cookies
                if cookie != {}:
                    result2 = requests.get(image_url.replace('http://dcimg.awalker.jp/view/',
                        'http://dcimg.awalker.jp/i/'), cookies=cookie)
                with open(image_name, 'wb') as f:
                    for chunk in result2.iter_content(chunk_size=1024):
                        f.write(chunk)
                return True
            result1 = requests.get(image_url)
            cookie = result1.cookies
            if cookie != {}:
                if int(post_time[0]) >= 2018 and int(post_time[1]) >=8 and int(daytime) >= 31:
                    link = image_url.replace(
                        'http://dcimg.awalker.jp/view/',
                        'http://dcimg.awalker.jp/i/')
                    print(link)
                    result2 = requests.get(link, timeout=5)
                    with open(image_name, 'wb') as f:
                        for chunk in result2.iter_content(chunk_size=1024):
                            f.write(chunk)
                    return True
                else:
                    link = image_url.replace(
                        'http://dcimg.awalker.jp/img1.php?id',
                        'http://dcimg.awalker.jp/img2.php?sec_key')
                # 下载图片前必须先访问img1.php获取cookie
                result2 = requests.get(link, cookies=cookie, timeout=5)
                print(image_name + ' 下载中...')
                with open(image_name, 'wb') as f:
                    for chunk in result2.iter_content(chunk_size=1024):
                        f.write(chunk)
                print(image_name + ' 下载成功')
                return True
        except Exception as e:
            print(image_url + ' 下载失败')
            download_pic(image_url, image_name, post_time, daytime)
    return False


def download_from_original_site(image_url, image_name):
    """从乃团服务器下载图片"""
    if not is_file_exisst(image_name):
        try:
            result = requests.get(image_url)
            if result.status_code == 200:
                print(image_name + ' 下载中')
                with open(image_name, 'wb') as f:
                    for chunk in result.iter_content(chunk_size=1024):
                        f.write(chunk)
                print(image_name + ' 下载完成')
        except:
            print(image_url + ' 下载失败')
            download_from_original_site(image_url, image_name)


def download_text(dives, text_name, title):
    """下载博客正文"""
    if not is_file_exisst(text_name):
        result = title + '\n'
        for div in dives:
            # print(div.name)
            if div.name == 'div':
                result += div.get_text()
                result += '\n'
            if div.name == 'p':
                for child in div.contents:
                    if child.name == 'br':
                        result += '\n'
                    else:
                        if child.string == None:
                            pass
                        else:
                            result += child.string
            if div.name == None:
                result += div.string
            elif div.name == 'br':
                result += '\n'

        with open(text_name, 'wb') as f:
            f.write(result.encode('utf-8'))


def download_thumbnail(image_url, image_name):
    """大图过期的情况下获取略缩图，带水印"""
    download_from_original_site(image_url, image_name)


def get_image_file_name(image_url):
    """通过正则解析图片文件的名称及发布时间"""
    pattern = r'[\w.:/]+/(\d{4})/(\d{2})/(\d{2})/([\w\-_/]+.(JPG|jpeg|PNG|jpg|png)+$)'
    matcher = re.compile(pattern)
    # 可能出现空的img标签
    if image_url == None:
        return
    result = matcher.match(image_url)
    if result != None:
        name = result.group(4)
        if '/' in name:
            index = name.find('/')
            name = name[index + 1:]
        return (result.group(1), result.group(2), result.group(3), name)



def download_main_program(member, days):
    """主循环，根据日期下载"""
    for page_day in days:
        time.sleep(3)
        for i in range(12):
            if i + int(str(page_day)[4:]) > 12:
                break
            else:
                time.sleep(3)
                for j in range(8):
                    download_member_blog(member, j + 1, int(page_day) + i)
                    time.sleep(2)
                i += 1

def get_correct_thumbnail_url(image_url):
    """通过正则解析图片文件的名称及发布时间"""
    pattern = r'([\w.:/]+)/(\d{4}/\d{2}/\d{2}/[\w/]+.(JPG|jpeg|PNG|jpg|png)+$)'
    matcher = re.compile(pattern)
    result = matcher.match(image_url)
    if result != None:
        return result.group(1)


def download_by_month(member, month):
    """下载某个月的博客"""
    for i in range(8):
        download_member_blog(member, i + 1, month)
        time.sleep(2)


def download_by_year(member, years):
    """下载某年的博客"""
    for year in years:
        for month in range(12):
            if len(str(month + 1)) == 1:
                month = '0' + str(month + 1)
            else:
                month = str(month + 1)
            print(str(year) + str(month))
            download_by_month(member, str(year) + str(month))
        time.sleep(5)


def change_input_str_to_member_list(input_name_str):
    """根据命令行输入的内容创建要下载的成员名单"""
    member_list = input_name_str.split(',')
    return member_list


def change_input_str_to_time_list(input_time_str):
    """根据命令行输入的内容创建要下载的时间列表"""
    time_list = input_time_str.split(',')
    return time_list

def split_ref(ref_url):
    pattern = r'[.:/\w]+/([\w]+).php'
    matcher = re.compile(pattern)
    result = matcher.match(ref_url)
    if result != None:
        return result.group(1)
    return ''

def can_find_in_member(name, members):
    for member in members:
        if member.get('jp') == name:
            return True
    return False

def get_member_list_from_file():
    members = []
    with open('input_member', 'r') as f:
        for i in f.readlines():
            split_member = i.split(',')
            en = split_member[0]
            zh = split_member[1]
            if not en.startswith('#'):
                member_struct = {}
                member_struct['jp'] = en
                member_struct['zh'] = zh.replace('\n', '')
                members.append(member_struct)
    return members

if __name__ == '__main__':
    domain = "http://blog.nogizaka46.com/"  # 域
    members = [
        dict(jp='mai.shiraishi', zh='白石麻衣'),
        dict(jp='miona.hori', zh='堀未央奈'),
        dict(jp='asuka.saito', zh='斋藤飞鸟'),
        dict(jp='manatsu.akimoto', zh='秋元真夏'),
        dict(jp='erika.ikuta', zh='生田绘梨花'),
        dict(jp='rina.ikoma', zh='生驹里奈'),
        dict(jp='marika.ito', zh='伊藤万里华'),
        dict(jp='sayuri.inoue', zh='井上小百合'),
        dict(jp='misa.eto', zh='卫藤美彩'),
        dict(jp='reika.sakurai', zh='樱井玲香'),
        dict(jp='yumi.wakatsuki', zh='若月佑美'),
        dict(jp='kazumi.takayama', zh='高山一実'),
        dict(jp='kana.nakada', zh='中田花奈'),
        dict(jp='himeka.nakamoto', zh='中元日芽香'),
        dict(jp='nanase.nishino', zh='西野七濑'),
        dict(jp='minami.hoshino', zh='星野南'),
        dict(jp='sayuri.matsumura', zh='松村沙友理'),
        dict(jp='ranze.terada', zh='寺田兰世'),
        dict(jp='yuuki.yoda', zh='与田祐希'),
	    dict(jp='riria.itou', zh='伊藤理々杏'),
	    dict(jp='renka.iwamoto', zh='岩本蓮加'),
	    dict(jp='minami.umezawa', zh='梅澤美波'),
	    dict(jp='momoko.oozono', zh='大園桃子'),
	    dict(jp='shiori.kubo', zh='久保史緒里'),
	    dict(jp='tamami.sakaguchi', zh='阪口珠美'),
	    dict(jp='kaede.satou', zh='佐藤楓'),
	    dict(jp='reno.nakamura', zh='中村麗乃'),
	    dict(jp='hazuki.mukai', zh='向井 葉月'),
	    dict(jp='mizuki.yamashita', zh='山下美月'),
	    dict(jp='ayanochristie.yoshida', zh='吉田綾乃クリスティー'),
        dict(jp='chiharu.saito', zh='齋藤ちはる'),
        dict(jp='kotoko.sasaki', zh='佐々木琴子'),
        dict(jp='mahiro.kawamura', zh='川村真洋'),
        dict(jp='karin.itou', zh='伊藤卡琳'),
        dict(jp='junna.itou', zh='伊藤純奈'),
        dict(jp='hina.kawago', zh='川後陽菜'),
        dict(jp='yuuri.saito', zh='斉藤優里'),
        dict(jp='iori.sagara', zh='相楽伊織'),
        dict(jp='mai.shinuchi', zh='新内眞衣'),
        dict(jp='ayane.suzuki', zh='鈴木絢音'),
        dict(jp='ami.noujo', zh='能條愛未'),
        dict(jp='hina.higuchi', zh='樋口日奈'),
        dict(jp='rena.yamazaki', zh='山崎怜奈'),
        dict(jp='miria.watanabe', zh='渡辺みり愛'),
        dict(jp='maaya.wada', zh='和田まあや'),
        dict(jp='hinako.kitano', zh='北野日奈子')
    ]
    # get_member_list_from_file()
    arg = '/?p='
    arg1 = '&d='
    current_month = datetime.datetime.today().month
    if len(str(current_month)) == 1:
        current_month = '0' + str(current_month)
    else:
        current_month = str(current_month)
    current_year = datetime.datetime.today().year
    days = [201111, 201201, 201301, 201401, 201501, 201601, 201701]
    #无输入参数，下载全员至今的博客
    if len(sys.argv) == 1:
        for member in members:
            download_main_program(member, days)
            # thread1 = threading.Thread(target=download_main_program, args=(member, days))
            # thread1.start()
    # 输入参数为成员列表，下载某成员至今的博客
    elif len(sys.argv) == 2 and sys.argv[1] != 'update':
        member_name_list = change_input_str_to_member_list(sys.argv[1])
        member_list = []
        for name in member_name_list:
            for member in members:
                if member.get('jp') == name:
                    member_list.append(member)
        for member in member_list:
            # download_main_program(member, days)
            thread1 = threading.Thread(target=download_main_program, args=(member, days))
            thread1.start()
    # 输入参数为update，下载全员本月的博客
    elif len(sys.argv) == 2 and sys.argv[1] == 'update':
        current_time = int(str(current_year) + current_month)
        for member in members:
            # download_by_month(member, current_time)
            thread1 = threading.Thread(
                target=download_by_month, args=(member, current_time))
            thread1.start()
    # 输入一个参数，且为成员列表,默认下载列表内成员本月的博客
    elif len(sys.argv) == 2:
        member_name_list = change_input_str_to_member_list(sys.argv[1])
        member_list = []
        days = [int(str(current_year) + current_month)]
        for member in member_name_list:
            for i in members:
                if i.get('jp') == member:
                    member_list.append(i)
        # download_main_program(member_list, days)
        for i in members:
            # if i.get('jp') == input_member_name:
            thread1 = threading.Thread(target=download_main_program, args=(i, days))
            thread1.start()
            # download_main_program(i, days)
    elif len(sys.argv) == 3 and sys.argv[1] == '-y':
        days = change_input_str_to_time_list(sys.argv[2])
        member_list = get_member_list_from_file()
        for member in member_list:
            download_by_year(member, days)
    elif len(sys.argv) == 3 and sys.argv[1] == '-m':
        days = change_input_str_to_time_list(sys.argv[2])
        member_list = get_member_list_from_file()
        for member in member_list:
            for month in days:
                download_by_month(member, month)
    # 输入三个参数，第一个为成员列表，第二个为-m，第三个为时间列表 如：201708表示2017年8月份
    elif len(sys.argv) == 4 and sys.argv[2] == '-m':
        member_name_list = change_input_str_to_member_list(sys.argv[1])
        days = change_input_str_to_time_list(sys.argv[3])
        member_list = []
        for member in member_name_list:
            for i in members:
                if i.get('jp') == member:
                    member_list.append(i)
        for member in member_list:
            for month in days:
                # thread1 = threading.Thread(target=download_by_month, args=(member, month))
                # thread1.start()
                download_by_month(member, month)
    elif len(sys.argv) == 4 and sys.argv[2] == '-y':
        member_name_list = change_input_str_to_member_list(sys.argv[1])
        days = change_input_str_to_time_list(sys.argv[3])
        member_list = []
        for member in member_name_list:
            for i in members:
                if i.get('jp') == member:
                    member_list.append(i)
        for member in member_list:
            download_by_year(member, days)
            # thread1 = threading.Thread(target=download_by_year, args=(member, days))
            # thread1.start()


