import feedparser
import datetime
import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

FEEDS = [
    "https://news.google.com/rss/search?q=Bali&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=バリ島&hl=ja&gl=JP&ceid=JP:ja",
    "https://thebalisun.com/feed/"
]


def fetch_articles():
    print("📡 RSS取得開始")
    articles = []
    now = datetime.datetime.utcnow()

    for url in FEEDS:
        print(f"取得中: {url}")
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue

            published = datetime.datetime(*entry.published_parsed[:6])

            if (now - published).total_seconds() <= 259200:
                articles.append({
                    "title": entry.title,
                    "summary": entry.get("summary", "")
                })

    seen = set()
    unique = []

    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    print(f"取得記事数: {len(unique)}件")
    return unique


def generate_blog(articles):
    print("🤖 AI記事生成開始")

    if not articles:
        return (
            "【最新】バリ島の観光・治安・経済まとめ",
            "本日は大きなニュースはありませんが、バリ島の最新動向として観光・治安・経済の基本情報を解説します。"
        )

    text = "\n\n".join([f"{a['title']}\n{a['summary']}" for a in articles])

    prompt = f"""
あなたは月間10万PVを稼ぐプロのSEOブロガーです。

以下のニュースをもとに、
検索上位を狙うブログ記事を作成してください。

【テーマ】
バリ島の治安・観光・経済の最新状況

【必須条件】
・SEOタイトル（32文字前後）
・導入文（検索意図に共感）
・結論を最初に書く（PREP法）
・H2、H3で構成
・ニュース要約＋独自解説
・日本人旅行者向け
・不安を解消する内容
・最後にまとめ

【重要】
・ただの要約は禁止
・「なぜ？どうなる？」を解説する
・以下のキーワードを自然に含める
（バリ島 治安 / バリ島 危険 / バリ島 最新情報）

ニュース:
{text}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "プロのSEOライター"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        content = res.choices[0].message.content

        jst = datetime.timezone(datetime.timedelta(hours=9))
        date = datetime.datetime.now(jst).strftime("%Y年%m月%d日")
        title = f"【{date}最新】バリ島の治安・観光・経済まとめ"

        print("✅ AI生成成功")
        return title, content

  　except Exception as e:
        print("❌ AIエラー:", e)
        return "記事生成エラー", str(e)


def save_markdown(title, content):
    print("📝 summary.md作成中")

    jst = datetime.timezone(datetime.timedelta(hours=9))
    date = datetime.datetime.now(jst).strftime("%Y-%m-%d")

    md = f"# {title}\n📅 {date}\n\n---\n\n{content}\n"
    md += f"\n\n最終更新: {datetime.datetime.now(jst)}\n"

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("✅ summary.md保存完了")


if __name__ == "__main__":
    print("=== バリ島ニュース自動化開始 ===")
    articles = fetch_articles()
    title, content = generate_blog(articles)
    save_markdown(title, content)
    print("=== 完了 ===")
