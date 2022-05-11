import requests
import re
import json
import jsonpath
import subprocess
import os


def printContainerData(container):
    for i in container:
        print(i)
    print()


class Bilibili(object):
    def __init__(self):
        # headers
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32",
            # 防盗链
            "referer": "https://www.bilibili.com/",
            "cookie": ""
        }
        # database, only contain titles
        self.data_base = []

    # 根据url和params，发送请求，获取响应
    def get_data(self, url, params=None):
        if params is None:
            res = requests.get(url, headers=self.headers)
        else:
            res = requests.get(url, headers=self.headers, params=params)
        return res.content

    # 获取视频的标题，包括选集的标题
    def get_video_title(self, url):
        str = self.get_data(url=url).decode()
        result = re.findall(r'<script>window.__INITIAL_STATE__=(.*?);\(function\(\).*?</script>', str)[0]
        json_data = json.loads(result)
        title = jsonpath.jsonpath(json_data, '$..pages..part')
        for t in title:
            tmp = {
                'index': len(self.data_base) + 1,
                'title': t
            }
            self.data_base.append(tmp)

    # 获取音频和视频链接
    def parse_audio_and_video(self, url, index):
        params = {
            'p': index
        }
        str = self.get_data(url=url, params=params).decode()
        # 2.提取音频和视频
        result = re.findall(r'<script>window.__playinfo__=(.*?)</script>', str)[0]
        json_data = json.loads(result)
        audio = jsonpath.jsonpath(json_data, '$.data.dash.audio..baseUrl')[0]
        video = jsonpath.jsonpath(json_data, '$.data.dash.video..baseUrl')[0]
        tmp = {'audio': audio, 'video': video}
        print(tmp)
        return tmp

    # 下载音频和视频
    def save_data(self, tmp):
        audio_url = tmp['audio']
        audio = self.get_data(audio_url)
        with open('./data/tmp.mp3', 'wb') as f:
            f.write(audio)
        print('>--- 音频下载完成 ---<')
        video_url = tmp['video']
        video = self.get_data(video_url)
        with open('./data/tmp.mp4', 'wb') as f:
            f.write(video)
        print('>--- 视频下载完成 ---<')

    # 合并音视频
    def merge_audio_and_video(self, index):
        # 合并音视频
        cmd = f'ffmpeg -i ./data/tmp.mp3 -i ./data/tmp.mp4 -c:v copy -c:a aac -strict experimental ./data/output.mp4'
        print(cmd)
        subprocess.call(cmd, shell=True)
        # 修改文件名
        name = self.data_base[index - 1]['title'] + '.mp4'
        os.rename('./data/output.mp4', './data/'+name)
        print('>--- 音视频合并成功 ---<')
        # 删除下载下来的临时文件
        os.remove('./data/tmp.mp3')
        os.remove('./data/tmp.mp4')

    def download_movie(self, url, index):
        # 判断当前目录是否存在该文件，如果存在，则不进行下载
        title = self.data_base[index-1]['title'] + '.mp4'
        if os.path.exists('./data/' + title):
            print('>--- 该视频已经存在，不进行下载操作 ---<')
            return
        # 获取音频和视频的地址
        tmp = self.parse_audio_and_video(url, index)
        # 下载对应的音视频
        self.save_data(tmp)
        # 通过ffmpeg合并音视频
        self.merge_audio_and_video(index)

    def start(self):
        # 1. 请输入Bilibili的视频url地址：
        url = 'https://www.bilibili.com/video/BV1no4y1974k?spm_id_from=333.337.search-card.all.click'
        # 2. 获取视频的所有标题
        self.get_video_title(url)
        printContainerData(self.data_base)
        # 3. 下载视频
        self.download_movie(url, 3)
        self.download_movie(url, 4)


if __name__ == '__main__':
    t = Bilibili()
    t.start()
