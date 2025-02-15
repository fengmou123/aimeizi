import requests
from bs4 import BeautifulSoup
import re
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# 请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}


def get_max_page_number(url):
    """
    获取网页中 data-page 属性值的最大值
    :param url: 网页的 URL
    :return: data-page 属性值的最大值
    """
    try:
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        page_numbers = []
        # 查找所有带有 data-page 属性的 a 标签
        for a_tag in soup.find_all('a', {'data-page': True}):
            try:
                page_numbers.append(int(a_tag['data-page']))
            except ValueError:
                continue
        if page_numbers:
            return max(page_numbers)
        return 1
    except requests.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return 1


def download_single_image(img_url, img_filename):
    """
    下载单张图片
    :param img_url: 图片的 URL
    :param img_filename: 图片保存的文件名
    """
    try:
        img_response = requests.get(img_url, headers=headers)
        if img_response.status_code == 200:
            with open(img_filename, 'wb') as f:
                f.write(img_response.content)
    except requests.RequestException as img_e:
        print(f"下载图片 {img_url} 时发生错误: {img_e}")


def download_images(url, folder_path, start_index=0):
    """
    从指定 URL 下载图片到指定文件夹
    :param url: 网页的 URL
    :param folder_path: 保存图片的主文件夹路径
    :param start_index: 图片编号的起始值
    :return: 下一次图片编号的起始值
    """
    try:
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        # 提取<title>标签内的内容
        title = soup.find('title').text.strip()
        # 去除标题中的非法字符，用于文件夹命名
        valid_title = re.sub(r'[\\/*?:"<>|]', '', title)
        sub_folder = os.path.join(folder_path, valid_title)
        if not os.path.exists(sub_folder):
            os.makedirs(sub_folder)

        pattern = re.compile(r'data-src="([^"]+)"')
        matches = pattern.findall(html_content)
        base_url = "https://xx.knit.bid"
        print(f"正在下载 {title} 的图片...")

        tasks = []
        for index, match in enumerate(matches):
            img_url = base_url + match
            img_filename = os.path.join(sub_folder, f"image_{start_index + index}.jpg")
            tasks.append((img_url, img_filename))
        #线程数
        with ThreadPoolExecutor(max_workers=1000) as executor:
            list(tqdm(executor.map(lambda x: download_single_image(*x), tasks), total=len(tasks), desc="图片下载进度"))

        return start_index + len(matches)
    except requests.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return start_index


def main():
    # 创建 downloads 文件夹（如果不存在）
    downloads_folder = 'downloads'
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)

    start_article_num = 14452
    end_article_num = 14499
    for article_num in tqdm(range(start_article_num, end_article_num + 1), desc="文章下载进度"):
        article_url = f"https://xx.knit.bid/article/{article_num}/"
        max_page = get_max_page_number(article_url)
        current_index = 0
        for page_num in range(1, max_page + 1):
            if page_num == 1:
                current_url = article_url
            else:
                current_url = f"https://xx.knit.bid/article/{article_num}/page/{page_num}/"
            print(f"正在下载文章 {article_num} 的第 {page_num} 页...")
            current_index = download_images(current_url, downloads_folder, current_index)


if __name__ == "__main__":
    main()