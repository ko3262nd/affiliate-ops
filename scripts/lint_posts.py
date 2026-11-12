#!/usr/bin/env python3
"""投稿案ファイルの機械チェック。

使い方: python3 lint_posts.py <posts.md> [--allow-placeholders]

読み取る形式: 「### 案名」の見出しの下にある ``` で囲んだ本文。
エラーがあれば終了コード1。
"""
import re
import sys

NG_WORDS = [
    "絶対", "必ず", "100%", "１００％", "誰でも", "確実に", "間違いなし",
    "治る", "治療", "予防する", "改善する", "痩せる", "若返る", "シワが消える",
    "副作用なし", "飲むだけで", "貼るだけで", "塗るだけで",
    "業界No.1", "業界NO.1", "日本一", "最安値", "残りわずか", "今だけ",
    "知らないと損", "やらないとヤバい", "後悔する",
    "簡単に稼げる", "放置で収入",
]
# 続報の約束・体験をほのめかす表現
PROMISE_PATTERNS = [
    r"使ってから(正直に)?(書き|お伝え|レポ|報告)",
    r"続き(は|を).{0,10}(書き|お伝え)",
    r"(後日|のちほど|あとで).{0,8}(書き|レポ|報告|お伝え)",
    r"書く予定",
    r"レビュー(します|予定)",
]
ALLOWED_TAGS = {"#PR", "#広告"}
PR_FIRST_LINES = {"【PR】", "【広告】"}
MAX_CHARS = 500
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]"
)


def parse(path):
    posts = []
    title = None
    in_block = False
    buf = []
    for line in open(path, encoding="utf-8"):
        raw = line.rstrip("\n")
        if not in_block:
            if raw.startswith("### "):
                title = raw[4:].strip()
            elif raw.strip().startswith("```"):
                in_block = True
                buf = []
        else:
            if raw.strip().startswith("```"):
                in_block = False
                posts.append((title or "(無題)", "\n".join(buf)))
            else:
                buf.append(raw)
    return posts


def check(title, body, allow_placeholders):
    errors, warns = [], []
    lines = body.split("\n")
    if lines[0].strip() not in PR_FIRST_LINES:
        errors.append("1行目が「【PR】」または「【広告】」だけになっていない")
    elif len(lines) < 2 or not lines[1].strip():
        warns.append("2行目(フック)が無い")
    n = len(body)
    if n > MAX_CHARS:
        errors.append(f"文字数が{MAX_CHARS}字を超えている({n}字)")
    emojis = len(EMOJI_RE.findall(body))
    if emojis > 2:
        errors.append(f"絵文字が3個以上({emojis}個)")
    for w in NG_WORDS:
        if w in body:
            errors.append(f"NG表現「{w}」")
    for p in PROMISE_PATTERNS:
        m = re.search(p, body)
        if m:
            errors.append(f"続報の約束・予告の疑い「{m.group(0)}」")
    for tag in re.findall(r"#\S+", body):
        if tag not in ALLOWED_TAGS:
            warns.append(f"ハッシュタグ {tag}(広告表記以外のタグ)")
    if not allow_placeholders and re.search(r"【ここに|〔|\[ここに|XXX|○○|◯◯", body):
        errors.append("プレースホルダが残っている")
    if re.search(r"公式情報|販売店ページ|商品ページ", body) and not re.search(
        r"20\d\d[-/年]\d{1,2}", body
    ):
        warns.append("出典(公式情報/販売店ページ)の表記があるが確認日が見当たらない")
    if "公式情報によると" in body and re.search(
        r"アスクル|Amazon|アマゾン|楽天|販売店|ショップ", body
    ):
        errors.append("販売店・ECの情報なのに「公式情報によると」と書いている疑い")
    return n, errors, warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow = "--allow-placeholders" in sys.argv
    if not args:
        print(__doc__)
        return 2
    posts = parse(args[0])
    if not posts:
        print("投稿本文(``` で囲んだブロック)が見つかりません")
        return 1
    bad = 0
    for title, body in posts:
        n, errors, warns = check(title, body, allow)
        status = "NG" if errors else "OK"
        print(f"[{status}] {title}  ({n}字)")
        for e in errors:
            print(f"    ERROR: {e}")
        for w in warns:
            print(f"    warn : {w}")
        bad += 1 if errors else 0
    print(f"--- {len(posts)}案中 エラーあり {bad}案")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
