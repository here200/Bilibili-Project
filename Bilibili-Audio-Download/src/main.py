import json
import requests
from lxml import etree
import re
import jsonpath
import os


# 打印容器里面的数据
def print_container(container):
    for e in container:
        print(e)
    print()


class Bilibili(object):
    def __init__(self, uid):
        # headers
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32",
            # 防盗链
            "referer": "https://www.bilibili.com/",
            # 如果你的收藏夹权限设置为私密的，那么必须要登录才能获取到收藏夹的数据
            # 这里你直接把cookie复制到这个位置即可。
            "cookie": ""
        }
        # 用户的个人空间地址
        self.user_center = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=' + uid
        # database
        # 收藏夹
        self.fav_data = []
        # 收藏夹列表
        self.fav_list_data = []

    # 发送请求，获取字节数据(可选是否携带请求参数)
    def get_data(self, url, params=None):
        if params is None:
            res = requests.get(url, headers=self.headers)
        else:
            res = requests.get(url, headers=self.headers, params=params)
        return res.content

    # 获取和保存用户的收藏夹
    def fav(self):
        str = self.get_data(url=self.user_center).decode()
        # 提取收藏夹的数据(名字，收藏夹id，收藏夹的视频个数)
        json_data = json.loads(str)
        list = jsonpath.jsonpath(json_data, '$.data.list')[0]
        for i in range(0, len(list)):
            el = list[i]
            tmp = {
                'index': i,
                'fav_name': el['title'],
                'fav_id': el['id'],
                'media_count': el['media_count']
            }
            self.fav_data.append(tmp)

    # 获取收藏夹里的每一条视频数据
    def get_fav_list_data(self, fav_id):
        url = 'https://api.bilibili.com/x/v3/fav/resource/list'
        has_more = True
        page = 1
        while has_more:
            params = {
                'media_id': fav_id,
                'pn': page,
                'ps': 20
            }
            str = self.get_data(url=url, params=params).decode()
            json_data = json.loads(str)
            media_list = jsonpath.jsonpath(json_data, '$..data.medias')[0]
            for i in range(0, len(media_list)):
                el = media_list[i]
                tmp = {
                    'index': len(self.fav_list_data),
                    'title': el['title'],
                    'avid': el['id']
                }
                self.fav_list_data.append(tmp)
            # 查询是否还有更多数据，如果有,让page++
            has_more = jsonpath.jsonpath(json_data, '$..has_more')[0]
            if has_more is True:
                page += 1

    # 解析其中的一条视频数据，获取视频名称，和音频链接
    def parse_title_and_audio(self, avid):
        url = 'https://www.bilibili.com/video/av' + avid
        str = self.get_data(url=url).decode()
        # 1.提取标题
        html = etree.HTML(str)
        title = html.xpath('//title/text()')[0].replace('_哔哩哔哩_bilibili', '') + '.mp3'
        print(title)
        # 2.提取音频
        result = re.findall(r'<script>window.__playinfo__=(.*?)</script>', str)[0]
        json_data = json.loads(result)
        audio = jsonpath.jsonpath(json_data, '$.data.dash.audio..baseUrl')[0]
        # 3.创建数据并返回
        tmp = {'title': title, 'audio_url': audio}
        return tmp

    # 保存音频数据
    def save_data(self, data):
        title = data['title']
        url = data['audio_url']
        # 保存到 ./data/ 中
        audio = self.get_data(url=url)
        with open('./data/' + title, 'wb') as f:
            f.write(audio)
        print('>---  ' + title + ' 已经下载完成 ---<')

    # 一步下载音频文件(主要目的是为了方便操作)
    def download_audio(self, index):
        # 解析视频的标题和音频链接
        data = self.parse_title_and_audio(str(self.fav_list_data[index]['avid']))
        if os.path.exists('./data/' + data['title']):
             print('>---  ' + data['title'] + ' 已经存在，不会进行下载 ---<')
        else:
            # 将音频文件下载到本地
            self.save_data(data)

    # main_process
    def start(self, fav_index, songs_index):
        # 获取用户的收藏夹
        self.fav()
        print('收藏夹：')
        print_container(self.fav_data)
        # 选择某个用户的收藏夹，获取收藏夹列表
        self.get_fav_list_data(self.fav_data[fav_index]['fav_id'])
        print('收藏夹列表：')
        print_container(self.fav_list_data)
        # 通过索引，一步下载音频文件
        for i in songs_index:
            self.download_audio(i)


if __name__ == '__main__':
    # 创建实例时，必须填写用户的UID
    t = Bilibili('user-id')
    # 收藏夹列表索引
    fav_index = 0
    # 收藏夹列表内容索引
    songs_index = [0, 3]
    t.start(fav_index, songs_index)
