"""作品集のサイトを組み立てる。

使い方: python build.py            （サイトを作り直して、公開前の点検をする）
        python build.py --check    （作り直さずに点検だけ）

- 作品の元のファイル（works の各フォルダの index.html）を、<slug>/index.html に写す。
  そのとき、スマホ向けの頭（文字コード・画面の幅）と X のカード（OGP）、上の「作品集へ」の帯を足す
- drafts/shots/ の画面の写真から、サムネイル（img/<slug>.jpg）と X のカード画像（img/og-<slug>.jpg）を作る
- 点検: 公開するファイルすべてで、個人の情報の言葉が0件・外への読み込みが Google Fonts だけ
  （言葉の一覧は .company/pr/links.md の冒頭と同じ。ここには書かない＝このファイルも公開されるため）
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKS = HERE.parent
SITE = "https://frickey104.github.io"
NAME = "frickey の工房"
FONT = r"C:\Windows\Fonts\YuGothB.ttc"
LINKS_MD = WORKS.parent / ".company" / "pr" / "links.md"

# 公開する作品（順番＝サイトでの並び。最初が注目作）
ITEMS = [
    dict(slug="chikai", src="2026-10-24_chikai-no-sekai", title="誓いの世界", kind="RPG", ver="試作3版",
         time="30分", crop=(34, 122, 766, 560),
         desc="王の書記の見習いが、霧の奥の長へ王の手紙を届ける三日間の旅。剣では戦わず、相手の事情を見抜いて進む。"),
    dict(slug="oshidashi", src="2026-10-21_board-game", title="おしだし", kind="ボードゲーム・2人", ver="試作2版",
         time="", crop=(0, 350, 768, 926),
         desc="盤の外から石を入れて、列ごと押し出す。4つ並べるか、相手の石を3つ落としたら勝ち。CPU とも対戦できる。"),
    dict(slug="shuna", src="2026-10-23_shuna-cards", title="シュナをさがして", kind="カードの RPG・1人", ver="試作3版",
         time="5分", crop=(28, 336, 746, 875),
         desc="迷子の犬シュナを探して、トランプ44枚の地下室を灯りひとつで降りていく。ルールは Scoundrel（Zach Gage・Kurt Bieg）が手本。"),
    dict(slug="yoake", src="2026-10-23_yoake-quest", title="夜明けの塔", kind="RPG", ver="試作1版",
         time="10〜15分", crop=(40, 130, 736, 652),
         desc="歩いて、出会って、コマンドで戦う。王道の RPG を小さくした1本道。犬のシュナがついてくる。"),
    dict(slug="kadotsunagi", src="2026-10-22_kadotsunagi", title="かどつなぎ", kind="ボードゲーム・2人", ver="",
         time="", crop=(28, 300, 746, 838),
         desc="1〜5マスの駒を、自分の駒と角だけでつなげて置いていく陣取り。市販の「ブロックス」（2人用）が手本。CPU とも対戦できる。"),
    dict(slug="michifusagi", src="2026-10-22_michifusagi", title="みちふさぎ", kind="ボードゲーム・2人", ver="",
         time="", crop=(28, 370, 746, 908),
         desc="壁を置いて相手の道をふさぎ、先に向こう側へ着いた方が勝ち。市販の「コリドール」が手本。CPU とも対戦できる。"),
    dict(slug="hex", src="2026-10-23_hex", title="ヘックス", kind="ボードゲーム・2人", ver="試し",
         time="", crop=(40, 450, 720, 960),
         desc="六角形の盤で、自分の色の辺と辺を石でつないだら勝ち。昔からある公開のゲーム「ヘックス」を作ってみた。"),
    dict(slug="tewatashi", src="2026-10-23_tewatashi", title="てわたし", kind="ボードゲーム・2人", ver="試し",
         time="", crop=(0, 20, 768, 596),
         desc="置く駒を相手が選んで渡してくる2人対戦。クアルトと同じ型を、自分なりに作ってみた試し。"),
    dict(slug="stl-viewer", src="2026-10-23_stl-viewer", title="STL ビューア", kind="道具", ver="",
         time="", crop=(0, 400, 800, 1000),
         desc="3D の形のファイル（STL）を回して見るだけの道具。ファイルは端末の中で読むだけで、どこにも送らない。"),
    dict(slug="vcm-calc", src="2026-10-12_vcm-calc", title="VCM 効き方計算", kind="計算シート", ver="",
         time="", crop=(150, 440, 730, 875),
         desc="可動コイル型の VCM で、寸法・磁石・コイルを変えたら推力が何%変わるかを、幅つきで出す。断面図と解説つき。"),
    dict(slug="force-balance", src="2026-10-12_force-balance", title="力のつり合い計算", kind="計算シート", ver="試作",
         time="", crop=(0, 20, 768, 596), bundle=True,
         desc="部品1つについて、触れているところが受ける力を、つり合いの式から求める。接触の種類を選ぶと力の向きが決まる。"),
]
# 外にあるもの（写さない・リンクだけ）
EXTERNAL = [
    dict(slug="experiments", title="実験室", kind="アート", url=f"{SITE}/experiments/", crop=(0, 100, 800, 700),
         desc="触った跡が作品に残り、次の動きを変える。ブラウザで動く実験の記録。"),
]

ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "frickey104.github.io", "github.com",
                 "www.w3.org"}  # w3.org は SVG の名前（通信しない）
# 出典として押すと開くリンク（<a href> だけ認める。読み込みには使わせない）
LINK_ONLY_HOSTS = {"www.duramag.com", "product.tdk.com"}

SKELETON = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<style>
:root{{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
.fk-bar{{all:initial;display:flex;align-items:center;justify-content:space-between;gap:12px;box-sizing:border-box;width:100%;min-height:34px;padding:6px max(12px,env(safe-area-inset-right,0px)) 6px max(12px,env(safe-area-inset-left,0px));background:#16283c;color:#e9eef4;font:600 13px/1.3 -apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic UI",sans-serif;position:relative;z-index:2147483647}}
.fk-bar a{{all:initial;color:#e9eef4;font:inherit;cursor:pointer;text-decoration:none}}
.fk-bar a:hover,.fk-bar a:focus-visible{{text-decoration:underline;outline:none}}
.fk-bar span{{all:initial;color:#9fb3c8;font:500 12px/1.3 ui-monospace,Consolas,monospace}}
</style>
</head>
<body>
<nav class="fk-bar" aria-label="作品集"><a href="../">← {name}</a><span>{label}</span></nav>
"""


def pii_words() -> list[str]:
    """個人の情報として検索する言葉を、公開しない台帳から読む（ここには書かない）。"""
    t = LINKS_MD.read_text(encoding="utf-8")
    m = re.search(r"個人の情報の検索に使う言葉:\s*(.+)", t)
    if not m:
        sys.exit("ng: links.md に「個人の情報の検索に使う言葉」が無い")
    words = [w.strip() for w in m.group(1).split("・") if w.strip()]
    if len(words) < 5:
        sys.exit(f"ng: 言葉が少なすぎる（{len(words)}個）")
    return words


def label(it: dict) -> str:
    parts = [it["kind"], it.get("ver", ""), it.get("time", "")]
    return " / ".join(p for p in parts if p)


def make_images() -> None:
    from PIL import Image, ImageDraw, ImageFont
    shots = HERE / "drafts" / "shots"
    out = HERE / "img"
    out.mkdir(exist_ok=True)
    big = ImageFont.truetype(FONT, 64)
    mid = ImageFont.truetype(FONT, 30)
    small = ImageFont.truetype(FONT, 24)
    ink, paper, line = (22, 40, 60), (238, 242, 245), (205, 216, 226)

    def blueprint(w, h):
        im = Image.new("RGB", (w, h), (20, 46, 78))
        d = ImageDraw.Draw(im)
        for x in range(0, w, 30):
            d.line([(x, 0), (x, h)], fill=(34, 64, 100) if x % 150 else (52, 88, 130), width=1)
        for y in range(0, h, 30):
            d.line([(0, y), (w, y)], fill=(34, 64, 100) if y % 150 else (52, 88, 130), width=1)
        return im

    thumbs = {}
    for it in ITEMS + EXTERNAL:
        src = shots / f"{it['slug']}.jpg"
        im = Image.open(src).convert("RGB").crop(it["crop"])
        th = im.resize((800, 600), Image.LANCZOS) if abs(im.width / im.height - 4 / 3) < .05 else fit(im, 800, 600)
        th.save(out / f"{it['slug']}.jpg", quality=84, optimize=True)
        thumbs[it["slug"]] = th
        # 作品ごとの X のカード（1200×630）: 青焼きの台紙に画面と題名
        og = blueprint(1200, 630)
        d = ImageDraw.Draw(og)
        pic = th.resize((640, 480), Image.LANCZOS)
        og.paste(pic, (500, 75))
        d.rectangle([500, 75, 1139, 554], outline=(140, 180, 220), width=2)
        d.text((60, 90), NAME, font=small, fill=(160, 190, 220))
        title_font = big if len(it["title"]) <= 6 else mid
        d.text((60, 150), it["title"], font=title_font, fill=(240, 246, 252))
        d.text((60, 250), label(it) if "ver" in it else it["kind"], font=small, fill=(160, 190, 220))
        wrap(d, it["desc"].split("。")[0] + "。", (60, 310), 400, small, (215, 228, 240))
        og.save(out / f"og-{it['slug']}.jpg", quality=86, optimize=True)

    # サイト全体の X のカード
    og = blueprint(1200, 630)
    d = ImageDraw.Draw(og)
    d.text((60, 70), NAME, font=big, fill=(240, 246, 252))
    d.text((62, 160), "仕事のあとに、AI と作っているゲームと道具と計算シート", font=mid, fill=(170, 200, 228))
    for i, slug in enumerate(["chikai", "oshidashi", "shuna", "yoake"]):
        pic = thumbs[slug].resize((256, 192), Image.LANCZOS)
        x = 60 + i * 276
        og.paste(pic, (x, 300))
        d.rectangle([x, 300, x + 255, 491], outline=(140, 180, 220), width=2)
    d.text((60, 530), "frickey104.github.io", font=small, fill=(160, 190, 220))
    og.save(out / "og-site.jpg", quality=86, optimize=True)


def fit(im, w, h):
    """縦横の比が違うときは、真ん中で切って w×h にする。"""
    from PIL import Image
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def wrap(d, text, xy, width, font, fill):
    x, y = xy
    line = ""
    for ch in text:
        if d.textlength(line + ch, font=font) > width:
            d.text((x, y), line, font=font, fill=fill)
            y += 38
            line = ch
        else:
            line += ch
    if line:
        d.text((x, y), line, font=font, fill=fill)


def source(it: dict) -> str:
    """作品の元のファイル。複数のファイルに分かれた作品は、その作品の1ファイル版を作る道具でまとめる。"""
    if not it.get("bundle"):
        return (WORKS / it["src"] / "index.html").read_text(encoding="utf-8")
    import subprocess
    tmp = HERE / "drafts" / f"{it['slug']}.bundled.html"
    subprocess.run([sys.executable, str(WORKS / it["src"] / "build_artifact.py"), str(tmp)], check=True,
                   stdout=subprocess.DEVNULL)
    return tmp.read_text(encoding="utf-8")


def build_pages() -> None:
    for it in ITEMS:
        src = source(it)
        head = SKELETON.format(
            desc=html.escape(it["desc"]), name=html.escape(NAME), title=html.escape(it["title"]),
            url=f"{SITE}/{it['slug']}/", img=f"{SITE}/img/og-{it['slug']}.jpg", label=html.escape(label(it)))
        out = HERE / it["slug"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(head + src.rstrip() + "\n</body>\n</html>\n", encoding="utf-8")


def check() -> int:
    words = pii_words()
    files = [p for p in HERE.rglob("*") if p.is_file() and ".git" not in p.parts and "drafts" not in p.parts]
    texts = [p for p in files if p.suffix in {".html", ".md", ".py", ".txt", ".json", ".css", ".js"}]
    bad = []
    for p in texts:
        t = p.read_text(encoding="utf-8")
        for w in words:
            # 英字の言葉は単語として一致したときだけ（canonical などの一部に当たらないように）
            pat = rf"(?<![A-Za-z]){re.escape(w)}(?![A-Za-z])" if w.isascii() else re.escape(w)
            if re.search(pat, t, re.I):
                bad.append(f"{p.relative_to(HERE)}: 個人の情報の言葉が見つかった")
        for m in re.finditer(r"https?://([a-zA-Z0-9.-]+)", t):
            host = m.group(1)
            if host in ALLOWED_HOSTS:
                continue
            if host in LINK_ONLY_HOSTS and re.search(r'<a href="$', t[max(0, m.start() - 9):m.start()]):
                continue
            bad.append(f"{p.relative_to(HERE)}: 外への読み込み {host}")
    # 画像のファイルに写真の情報（Exif）が残っていないか
    from PIL import Image
    for p in files:
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            if Image.open(p).getexif():
                bad.append(f"{p.relative_to(HERE)}: 画像に Exif が残っている")
    print(f"点検: ファイル {len(files)} 個（文字 {len(texts)}）・言葉 {len(words)} 個")
    for b in bad:
        print("❌", b)
    print("ok" if not bad else "ng")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pages", action="store_true", help="画像は作らず、ページだけ作る（画面を撮る前）")
    a = ap.parse_args()
    if not a.check:
        if not a.pages:
            make_images()
        build_pages()
    return check()


if __name__ == "__main__":
    sys.exit(main())
