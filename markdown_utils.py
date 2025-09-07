import re

# Markdown 中の画像リンクに関するユーティリティ関数群
# 目的: 画像リンクでテキストを分割したり、画像リンクを抽出する処理を部品化する

IMAGE_PATTERN = r'!\[.*?\]\((.*?)\)'


def split_by_image_links(text: str):
    """
    Markdown テキストを「画像リンクを単独の要素として残す形」で分割して返す。
    例: 'A ![alt](img.png) B' -> ['A ', '![alt](img.png)', ' B']

    :param text: 分割対象の Markdown テキスト
    :return: 分割済みのパーツ一覧 (list of str)
    """
    # 正規表現で画像リンクをキャプチャして、分割する
    parts = re.split(r'(!\[.*?\]\(.*?\))', text)
    return parts


def extract_image_links(text: str):
    """
    与えられたテキストから画像リンクのパス（丸かっこ内）をすべて抽出して返す。

    :param text: 対象テキスト
    :return: 画像リンクのリスト。見つからなければ空リストを返す。
    """
    return re.findall(IMAGE_PATTERN, text)
