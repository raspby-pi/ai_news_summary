import feedparser
import pandas as pd
from datetime import datetime
import requests
import re
import streamlit as st
import toml

# --- 뉴스 출처를 언론사별로 세분화하여 관리 ---
SOURCES = {
    "KOREA": {
        "한국경제": "https://www.hankyung.com/feed/finance",
        "매일경제": "https://www.mk.co.kr/rss/50200011",
        "연합뉴스": "https://www.yna.co.kr/rss/economy.xml",
        "이데일리": "http://rss.edaily.co.kr/stock_news.xml",
        "뉴스핌": "http://rss.newspim.com/news/category/105",
        "인포맥스": "https://news.einfomax.co.kr/rss/S1N2.xml"
    },
    "USA": {
        "CNBC(속보)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "Yahoo(시장)": "https://finance.yahoo.com/news/rssindex",
        "Investing": "https://www.investing.com/rss/news_25.rss",
        "한경국제": "https://www.hankyung.com/feed/international",
        "매경글로벌": "https://www.mk.co.kr/rss/40300001/"
    }
}

# --- 1. 네이버 뉴스 검색 (국내) ---
def fetch_naver_news(query="증시"):
    # 2. 방어적 로직: secrets에서 안전하게 키 가져오기
    try:
        # st.secrets.get()을 사용하면 키가 없을 때 None을 반환하여 에러를 막을 수 있습니다.
        NAVER_ID = st.secrets.get("NAVER_ID")
        NAVER_SECRET = st.secrets.get("NAVER_SECRET")

        if not NAVER_ID or not NAVER_SECRET:
            st.error("API 키가 설정되지 않았습니다. .streamlit/secrets.toml을 확인하세요.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Secrets 로드 중 오류: {e}")
        return pd.DataFrame()

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    refined_query = f"{query} +(증권|공시|주가|주식)"
    params = {"query": query, "display": 15, "sort": "date"}
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            print(f"✅ Naver API 호출 성공: {query}")
            items = res.json().get('items', [])
            data = []
            for item in items:
                data.append({
                    'title': re.sub('<[^<]+?>', '', item['title']),
                    'link': item['link'],
                    'published': datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900'),
                    'summary': re.sub('<[^<]+?>', '', item['description'])
                })
            return pd.DataFrame(data)
        else:
            print(f"❌ Naver API 오류: {res.status_code} - {res.text}")
            return pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Naver API 연결 실패: {e}")
        return pd.DataFrame()

def fetch_rss_feeds(market_type="KOREA", source_name=None):
    """
    market_type: "KOREA" 또는 "USA"
    source_name: 특정 언론사 선택 (None일 경우 해당 시장 전체 수집)
    """
    market_data = SOURCES.get(market_type, SOURCES["KOREA"])

    if source_name:
        rss_urls = [market_data.get(source_name)]
    else:
        rss_urls = list(market_data.values())

    all_articles = []

    for url in rss_urls:
        if not url: continue
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
                published = dt + timedelta(hours=9)
            else:
                published = datetime.now()
        except Exception:
            published = datetime.now()

        for entry in feed.entries:
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '#')
            published_str = getattr(entry, 'published', None)
            summary = getattr(entry, 'summary', 'No Summary')

            all_articles.append({
                'title': title,
                'link': link,
                'published': published_str,
                'summary': summary
            })

    if not all_articles:
        return pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

    df = pd.DataFrame(all_articles)
    # 날짜 정렬을 위해 datetime 형식 확정
    df['published'] = pd.to_datetime(df['published'])
    # 최신순 정렬
    df = df.sort_values(by='published', ascending=False).reset_index(drop=True)
    return df