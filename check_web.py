# check_web.py

import requests

API_URL = "https://api-community.plaync.com/aion2/board/notice_ko/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0"

TARGET = "운영정책 위반 및 임시보호 계정들에 대한 게임 이용제한 안내"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_latest_notice():
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        data = res.json()

        articles = data.get("contentList", [])

        if not articles:
            return None

        top = articles[0]

        return {
            "id": top.get("id"),
            "title": top.get("title"),
            "is_ban": TARGET in top.get("title", ""),
            "url": f"https://aion2.plaync.com/ko-kr/board/notice/view?articleId={top.get('articleId')}"
        }

    except Exception as e:
        print("check_web error:", e)
        return None