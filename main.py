import feedparser
import datetime
import os
import requests
from openai import OpenAI

# ========= 環境変数 =========
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
WP_URL            = os.getenv("WP_URL")
WP_USER           = os.getenv("WP_USER")
WP_APP_PASSWORD   = os.getenv("WP_APP_PASSWORD")

client = OpenAI(api_key=OPENAI_API_KEY)

# ========= RSS =========
FEEDS = [
    "https://news.google.com/rss/search?q=Bali&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=バリ島&hl=ja&gl=JP&ceid=JP:ja",
    "https://thebalisun.com/feed/"
]

# ========= ニュース取得 =========
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
            if (now - published).total_seconds() <= 86400:
                articles.append({
                    "title": entry.title,
                    "summary": entry.get("summary", "")
                })
    seen, unique = set(), []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    print(f"取得記事数: {len(unique)}件")
    return unique

# ========= AI記事生成 =========
def generate_blog(articles):
    print("🤖 AI記事生成開始")
    if not articles:
        return "本日のバリ島ニュースはありません", "本日は過去24時間以内のニュースは確認されませんでした。"

    text = "\n\n".join([f"{a['title']}\n{a['summary']}" for a in articles])
    prompt = f"""
あなたはプロのSEOブロガーです。
以下のニュースから日本人向けのブログ記事を作成してください。

# 条件
・タイトル付き
・見出し構成（H2, H3）
・PREP法
・観光 / 治安 / 経済で整理
・読みやすく
・最後にまとめ

ニュース:
{text}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "プロのSEOライター"},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.5
        )
        content = res.choices[0].message.content
        title = content.split("\n")[0].replace("#", "").strip()
        print("✅ AI生成成功")
        return title, content
    except Exception as e:
        print("❌ AIエラー:", e)
        return "記事生成エラー", str(e)

# ========= Markdown保存 =========
def save_markdown(title, content):
    print("📝 summary.md作成中")
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    md = f"# {title}\n📅 {date}\n\n---\n\n{content}\n"
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("✅ summary.md保存完了")

# ========= WordPress投稿 =========  ← 追加した関数
def post_to_wordpress(title, content):
    print("🌐 WordPress投稿開始")
    if not all([WP_URL, WP_USER, WP_APP_PASSWORD]):
        print("⚠️ WordPress環境変数が未設定のためスキップします")
        return

    endpoint = f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
    payload = {
        "title":   title,
        "content": content,
        "status":  "publish"   # 下書きにする場合は "draft"
    }
    try:
        response = requests.post(
            endpoint,
            json=payload,
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30
        )
        response.raise_for_status()
        post_id  = response.json().get("id")
        post_url = response.json().get("link")
        print(f"✅ WordPress投稿成功 — ID: {post_id}")
        print(f"   URL: {post_url}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP エラー: {e.response.status_code} {e.response.text}")
    except Exception as e:
        print(f"❌ WordPress投稿エラー: {e}")

# ========= メイン =========
if __name__ == "__main__":
    print("=== バリ島ニュース自動化開始 ===")
    articles          = fetch_articles()
    title, content    = generate_blog(articles)
    save_markdown(title, content)
    post_to_wordpress(title, content)   # ← 修正前は関数未定義でクラッシュしていた
    print("=== 完了 ===")
