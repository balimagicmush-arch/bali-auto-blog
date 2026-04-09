if __name__ == "__main__":
    print("=== バリ島ニュース自動化開始 ===")
    articles          = fetch_articles()
    title, content    = generate_blog(articles)
    save_markdown(title, content)
    # post_to_wordpress(title, content)
    print("=== 完了 ===")
