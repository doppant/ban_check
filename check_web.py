import requests
import re

API_URL = "https://api-community.plaync.com/aion2/board/notice_ko/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0"

TARGET = "운영정책 위반 및 임시보호 계정들에 대한 게임 이용제한 안내"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def extract_ban_link(article_id):
    try:
        api_url = f"https://api-community.plaync.com/aion2/board/notice_ko/article/{article_id}"
        res = requests.get(api_url, headers=headers)
        data = res.json()

        content = data.get("article", {}).get("content", {}).get("content", "")

        if not content:
            print("❌ content kosong")
            return None

        if "assets.playnccdn.com" in content:
            start = content.find("https://assets.playnccdn.com")
            end = content.find('"', start)

            return content[start:end]

        print("❌ link CDN tidak ditemukan")

    except Exception as e:
        print("extract error:", e)

    return None


def get_latest_notice():
    try:
        res = requests.get(API_URL, headers=headers)
        data = res.json()

        articles = data.get("contentList", [])

        if not articles:
            return None

        top = articles[0]

        article_id = top.get("id")
        title = top.get("title")

        notice_url = f"https://aion2.plaync.com/ko-kr/board/notice/view?articleId={article_id}"

        is_ban = TARGET in title

        ban_url = None

        if is_ban:
            print("🔍 Extracting ban link from API...")
            ban_url = extract_ban_link(article_id)
            print("Ban URL:", ban_url)

        return {
            "id": article_id,
            "title": title,
            "url": notice_url,
            "is_ban": is_ban,
            "ban_url": ban_url
        }

    except Exception as e:
        print("get_latest_notice error:", e)
        return None