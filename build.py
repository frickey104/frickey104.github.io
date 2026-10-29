"""作品集のサイトを組み立てる。

使い方: python build.py            （サイトを作り直して、公開前の点検をする）
        python build.py --pages    （画像は作らず、ページだけ作る＝画面を撮る前）
        python build.py --check    （作り直さずに点検だけ）

- 作品の元のファイル（works の各フォルダの index.html）を、<slug>/index.html に写す。
  そのとき、スマホ向けの頭（文字コード・画面の幅）と X のカード（OGP）、上の「作品集へ」の帯を足す
- drafts/shots/<slug>.jpg の画面の写真から、サムネイル（img/<slug>.jpg）と X のカード画像（img/og-<slug>.jpg）を作る
- 作品の状態（完成・途中・止めた）は works/README.md の表の「フォルダ」「状態」の列から読む（状態の頭の語）
- トップページ index.html は _top.html（手で書く元・カードは書かない）に、棚とカードを入れて作る
  並び: 自己紹介と今週の変化 → ゲーム → 道具 → 物（棚は作品の種類。完成・途中・止めたは各カードの左上の札で見せる。棚の中は新しく手を入れた順）
- 点検: 公開するファイルすべてで、個人の情報の言葉が0件（HTML のコメントも）・外への読み込みが Google Fonts だけ・
  画像に撮影情報（Exif）や PNG の文字の情報（tEXt/iTXt/zTXt）が無い・drafts/ のファイルや .stl が混じっていない
  （言葉の一覧は .company/pr/links.md の冒頭と同じ。ここには書かない＝このファイルも公開されるため）
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import io
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKS = HERE.parent
SITE = "https://frickey104.github.io"
NAME = "frickey の工房"
FONT = r"C:\Windows\Fonts\YuGothB.ttc"
LINKS_MD = WORKS.parent / ".company" / "pr" / "links.md"  # 読むだけ（個人の情報の言葉）
WORKS_MD = WORKS / "README.md"  # 読むだけ（作品の状態）
TOP = HERE / "_top.html"  # トップページの元（手で書く。_ で始まるので公開されない）
TODAY = dt.date.today()

# 載せる作品（順番＝棚の中での並び）。載せない作品は書かない。
# shelf: 載せる棚（game＝ゲーム／tool＝道具／thing＝物）
ITEMS = [
    dict(slug="chikai", shelf="game", src="2026-10-24_chikai-no-sekai", title="誓いの世界", kind="RPG", ver="試作4版", time="30分",
         crop=(34, 122, 766, 560),
         alt="誓いの世界の場面。夜の書記の部屋で、ろうそくの灯る机と本棚、白いひげの師匠",
         desc="王の書記の見習いが、霧の奥の長へ王の手紙を届ける三日間の旅。剣では戦わず、相手の事情を見抜いて進みます。"),
    dict(slug="shuna", shelf="game", src="2026-10-23_shuna-cards", title="シュナをさがして", kind="カードの RPG・1人", ver="試作3版", time="5分",
         crop=(28, 336, 746, 875),
         alt="シュナをさがしての画面。灯りに照らされた地下室と、4枚のカード",
         desc="迷子の犬シュナを探して、トランプ44枚の地下室を灯りひとつで降りていく。ルールは Scoundrel（Zach Gage・Kurt Bieg）が手本です。"),
    dict(slug="michifusagi", shelf="game", src="2026-10-22_michifusagi", title="みちふさぎ", kind="ボードゲーム・2人", ver="", time="",
         crop=(28, 370, 746, 908),
         alt="みちふさぎの9×9の盤と、向かい合う紅と藍のコマ",
         desc="壁を置いて相手の道をふさぎ、先に向こう側へ着いた方が勝ち。市販の「コリドール」が手本です。CPU とも対戦できます。"),
    dict(slug="yoake", shelf="game", src="2026-10-23_yoake-quest", title="夜明けの塔", kind="RPG", ver="試作1版", time="10〜15分",
         crop=(40, 130, 736, 652),
         alt="夜明けの塔のタイトル画面。主人公と犬のドット絵",
         desc="歩いて、出会って、コマンドで戦う。王道の RPG を小さくした1本道。犬のシュナがついてきます。"),
    dict(slug="kadotsunagi", shelf="game", src="2026-10-22_kadotsunagi", title="かどつなぎ", kind="ボードゲーム・2人", ver="", time="",
         crop=(28, 300, 746, 838),
         alt="かどつなぎの14×14の盤と、紅と藍の開始の印",
         desc="1〜5マスの駒を、自分の駒と角だけでつなげて置いていく陣取り。1回だけ相手の駒を消して置ける「消す権利」つき。市販の「ブロックス」（2人用）が手本です。"),
    dict(slug="stl-viewer", shelf="tool", src="2026-10-23_stl-viewer", title="STL ビューア", kind="道具", ver="", time="",
         crop=(0, 400, 800, 1000),
         alt="STL ビューアに表示したドーナツ形の3Dモデル",
         desc="3D の形のファイル（STL）を回して見るだけの道具。ファイルは端末の中で読むだけで、どこにも送りません。"),
    dict(slug="vcm-calc", shelf="tool", src="2026-10-12_vcm-calc", title="VCM 効き方計算", kind="計算シート", ver="", time="",
         crop=(150, 440, 730, 875),
         alt="VCM 効き方計算の断面図。上下のヨーク、N極とS極の磁石、コイル",
         desc="可動コイル型の VCM で、寸法・磁石・コイルを変えたら推力が何%変わるかを、幅つきで出します。断面図と解説つき。"),
    dict(slug="itazeri", shelf="game", src="2026-10-28_itazeri", title="板ぜり", kind="ボードゲーム・2人", ver="", time="",
         crop=(160, 250, 640, 610),
         alt="板ぜりの盤。1から9の価格の段と、真ん中の株価5",
         desc="株の板取引を参考にした2人対戦。伏せた壁とハッタリ札で、株価という前線を押し合います。CPU とも対戦できます。"),
    dict(slug="oshidashi", shelf="game", src="2026-10-21_board-game", title="おしだし", kind="ボードゲーム・2人", ver="", time="",
         crop=(0, 350, 768, 926),
         alt="おしだしの盤。5×5のマスと、まわりの矢印",
         desc="盤の外から石を入れて、列ごと押し出す。4つ並べるか、相手の石を落としたら勝ち（先手は3つ・後手は2つ）。CPU とも対戦できます。"),
    dict(slug="hex", shelf="game", src="2026-10-23_hex", title="ヘックス", kind="ボードゲーム・2人", ver="", time="",
         crop=(40, 450, 720, 960),
         alt="ヘックスの六角形の盤。上下が藍、左右が山吹の辺",
         desc="六角形の盤で、自分の色の辺と辺を石でつないだら勝ち。昔からある公開のゲームを作ってみました。"),
    dict(slug="tewatashi", shelf="game", src="2026-10-23_tewatashi", title="てわたし", kind="ボードゲーム・2人", ver="", time="",
         crop=(0, 20, 768, 596),
         alt="てわたしの画面。4×4の丸いマスと、相手に渡す駒を選ぶ案内",
         desc="置く駒を相手が選んで渡してくる2人対戦。クアルトと同じ型を、自分なりに作ってみた試しです。"),
    dict(slug="brooch", src="2026-10-27_fashion-items", title="ブローチの見本", kind="3D プリントの小物", ver="", time="",
         crop=(16, 166, 784, 742), shelf="thing",
         alt="ブローチの見本の絵。花のブローチと、白目のシュナウザーの顔",
         desc="3D プリンタで刷るブローチの見本の絵。花と、シュナウザーの顔やへそ天の姿。大きさと材料つき。"),
]
# 外にあるもの（写さない・リンクだけ）
EXTERNAL = [
    dict(slug="experiments", shelf="tool", src="2026-08-18_experiments", title="実験室", kind="アート", url=f"{SITE}/experiments/",
         crop=(0, 100, 800, 700),
         alt="実験室の作品「風の地形」。暗い青の中を流れる細い光の筋",
         desc="触った跡が作品に残り、次の動きを変える。ブラウザで動く実験の記録です。"),
]

STATES = {"完成": "done", "途中": "wip", "止めた": "stop"}
ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "frickey104.github.io", "github.com",
                 "www.w3.org"}  # w3.org は SVG の名前（通信しない）
# 出典として押すと開くリンク（<a href> だけ認める。読み込みには使わせない）
LINK_ONLY_HOSTS = {"www.duramag.com", "product.tdk.com"}
PROBLEMS: list[str] = []  # 組み立て中に見つかった問題（点検で ng にする）

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


def read_states() -> None:
    """works/README.md の表から、各作品の状態（完成・途中・止めた）を it["state"] に入れる。読めない作品は ng。"""
    found = {}
    for line in WORKS_MD.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 7 or not cells[3].startswith("`"):
            continue
        m = re.match(r"(完成|途中|止めた)", cells[5])
        found[cells[3].strip("`")] = m.group(1) if m else None
    for it in ITEMS + EXTERNAL:
        it["state"] = found.get(it["src"])
        if not it["state"]:
            why = "表に無い" if it["src"] not in found else "状態が 完成・途中・止めた のどれでもない"
            PROBLEMS.append(f"works/README.md: {it['title']}（{it['src']}）の状態が読めない（{why}）")


def updated(it: dict) -> dt.date | None:
    """作品フォルダの git の最新 commit の日付（フォルダが自分の git を持たないときは None）。"""
    d = WORKS / it["src"]
    if not (d / ".git").exists():
        return None
    r = subprocess.run(["git", "-C", str(d), "log", "-1", "--format=%cs"], capture_output=True, text=True)
    return dt.date.fromisoformat(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def href(it: dict) -> str:
    """トップページのカードのリンク先"""
    return it.get("url") or f"{it['slug']}/"


def label(it: dict) -> str:
    parts = [it["kind"], it.get("ver", ""), it.get("time", "")]
    return " / ".join(p for p in parts if p)


def md(d: dt.date) -> str:
    return f"{d.month}/{d.day}"


def shelves() -> list[tuple[str, str, list[dict], bool]]:
    """（id, 見出し, 作品, 大きいカードか）の並び。棚は種類で分け、中は新しく手を入れた順。"""
    allw = [i for i in ITEMS + EXTERNAL if i.get("state")]
    def newest(items: list[dict]) -> list[dict]:
        return sorted(items, key=lambda it: updated(it) or dt.date.min, reverse=True)
    return [(sid, head, newest([i for i in allw if i.get("shelf") == sid]), False)
            for sid, head in (("game", "ゲーム"), ("tool", "道具"), ("thing", "物"))]


def ordered() -> list[dict]:
    return [it for _, _, items, _ in shelves() for it in items]


def make_images() -> None:
    from PIL import Image, ImageDraw, ImageFont
    shots = HERE / "drafts" / "shots"
    out = HERE / "img"
    out.mkdir(exist_ok=True)
    big = ImageFont.truetype(FONT, 64)
    mid = ImageFont.truetype(FONT, 30)
    small = ImageFont.truetype(FONT, 24)

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
        if not src.exists():
            PROBLEMS.append(f"drafts/shots/{it['slug']}.jpg: 画面の写真が無い（撮ってから作り直す）")
            continue
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
        d.text((60, 250), label(it), font=small, fill=(160, 190, 220))
        wrap(d, it["desc"].split("。")[0] + "。", (60, 310), 400, small, (215, 228, 240))
        og.save(out / f"og-{it['slug']}.jpg", quality=86, optimize=True)

    # サイト全体の X のカード（トップの並びの最初の4つ）
    og = blueprint(1200, 630)
    d = ImageDraw.Draw(og)
    d.text((60, 70), NAME, font=big, fill=(240, 246, 252))
    d.text((62, 160), "AI の仮想会社『CC カンパニー』で、遊べるものを作っています", font=mid, fill=(170, 200, 228))
    for i, slug in enumerate([it["slug"] for it in ordered() if it["slug"] in thumbs][:4]):
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


def card(it: dict, no: int, big: bool) -> str:
    e = html.escape
    key = STATES[it["state"]]
    tag = [f"No.{no:02d}", it["kind"]]
    upd = ""
    if it["state"] == "途中":
        d = updated(it)
        upd = "・".join(p for p in [it.get("ver", ""), f"{md(d)} 更新" if d else ""] if p)
        upd = f'<span class="upd">{e(upd)}</span>' if upd else ""
    elif it.get("ver"):
        tag.append(it["ver"])
    if it.get("time"):
        tag.append(it["time"])
    ext = ' <span class="ext">↗</span>' if it.get("url") else ""
    go = '<span class="go">遊ぶ →</span>' if big else ""
    lazy = "" if big else ' loading="lazy"'
    return (f'      <a class="card st-{key}" href="{e(href(it))}"><span class="pic"><img src="img/{it["slug"]}.jpg" '
            f'alt="{e(it["alt"])}" width="800" height="600"{lazy}><span class="st">{it["state"]}</span></span>\n'
            f'        <div class="body"><span class="tag">{e(" ／ ".join(tag))}</span>{upd}<h4>{e(it["title"])}{ext}</h4>'
            f'<p>{e(it["desc"])}</p>{go}</div></a>')


def build_top() -> None:
    """トップページ（index.html）を _top.html から作る。棚・カード・点数・日付・今週の変化を入れる。"""
    t = TOP.read_bytes().decode("utf-8")
    n = 0
    parts = []
    for sid, head, items, big in shelves():
        if not items:
            continue
        cards = []
        for it in items:
            n += 1
            cards.append(card(it, n, big))
        parts.append(f'  <section aria-labelledby="{sid}">\n'
                     f'    <div class="shelf-head"><h2 id="{sid}">{head}</h2><span class="tag">{len(items)} 点</span></div>\n'
                     f'    <div class="grid{" big" if big else ""}">\n' + "\n".join(cards) + "\n    </div>\n  </section>\n")
    # 今週の変化: 直近7日に作品フォルダの git が更新された作品（新しい順に最大3つ）
    recent = []
    for it in ordered():
        d = updated(it)
        if d and 0 <= (TODAY - d).days < 7:
            recent.append((d, it))
    recent.sort(key=lambda x: x[0], reverse=True)
    news = ""
    if recent:
        spans = "".join(f"<span>{md(d)} {html.escape(' '.join(p for p in [it['title'], it.get('ver', '')] if p))}</span>"
                        for d, it in recent[:3])
        news = f'    <p class="news"><b>今週の変化</b>{spans}</p>\n'
    t = (t.replace("@@TAG@@", f"WORKS / {n} 点 / {TODAY.isoformat()} 更新")
          .replace("@@NEWS@@", news).replace("@@SHELVES@@", "\n".join(parts)))
    (HERE / "index.html").write_bytes(t.encode("utf-8"))


def png_text_chunks(b: bytes) -> list[str]:
    """PNG の文字の情報（tEXt/iTXt/zTXt）の塊の名前を返す。"""
    if not b.startswith(b"\x89PNG\r\n\x1a\n"):
        return []
    out, i = [], 8
    while i + 8 <= len(b):
        n, kind = int.from_bytes(b[i:i + 4], "big"), b[i + 4:i + 8]
        if kind in (b"tEXt", b"iTXt", b"zTXt"):
            out.append(kind.decode())
        if kind == b"IEND":
            break
        i += 12 + n
    return out


def image_problems(b: bytes, where: str) -> list[str]:
    from PIL import Image
    bad = []
    try:
        if Image.open(io.BytesIO(b)).getexif():
            bad.append(f"{where}: 画像に撮影情報（Exif）が残っている")
    except Exception:
        pass
    if png_text_chunks(b):
        bad.append(f"{where}: PNG に文字の情報（{'・'.join(sorted(set(png_text_chunks(b))))}）が残っている")
    return bad


def check() -> int:
    words = pii_words()

    def has_word(t: str) -> bool:
        for w in words:
            # 英字の言葉は単語として一致したときだけ（canonical などの一部に当たらないように）
            pat = rf"(?<![A-Za-z]){re.escape(w)}(?![A-Za-z])" if w.isascii() else re.escape(w)
            if re.search(pat, t, re.I):
                return True
        return False

    bad = list(PROBLEMS)
    files = [p for p in HERE.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts
             and p.relative_to(HERE).parts[0] != "drafts"]  # 一番上の drafts/ は .gitignore で上がらない
    texts = [p for p in files if p.suffix in {".html", ".md", ".py", ".txt", ".json", ".css", ".js"}]
    for p in files:
        rel = p.relative_to(HERE)
        if "drafts" in rel.parts:
            bad.append(f"{rel}: 写しに drafts/ のファイルが混じっている")
        if p.suffix.lower() == ".stl":
            bad.append(f"{rel}: STL のファイルが混じっている")
    for p in texts:
        rel = p.relative_to(HERE)
        t = p.read_text(encoding="utf-8")
        if has_word(t):
            bad.append(f"{rel}: 個人の情報の言葉が見つかった")
        if p.suffix == ".html":
            if any(has_word(c) for c in re.findall(r"<!--(.*?)-->", t, re.S)):
                bad.append(f"{rel}: HTML のコメントに個人の情報の言葉がある")
            for m in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']*)["']""", t):
                if re.search(r"\.stl(?:[?#]|$)|(?:^|/)drafts/", m.group(1), re.I):
                    bad.append(f"{rel}: drafts/ か .stl へのリンク（{m.group(1)[:60]}）")
            for m in re.finditer(r"data:image/(?:png|jpe?g);base64,([A-Za-z0-9+/=]+)", t):
                bad += image_problems(base64.b64decode(m.group(1)), f"{rel}（埋め込みの画像）")
        for m in re.finditer(r"https?://([a-zA-Z0-9.-]+)", t):
            host = m.group(1)
            if host in ALLOWED_HOSTS:
                continue
            if host in LINK_ONLY_HOSTS and re.search(r'<a href="$', t[max(0, m.start() - 9):m.start()]):
                continue
            bad.append(f"{rel}: 外への読み込み {host}")
    # 画像のファイルに撮影情報（Exif）・PNG の文字の情報が残っていないか
    for p in files:
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            bad += image_problems(p.read_bytes(), str(p.relative_to(HERE)))
    # トップのカードと置いてあるファイルが ITEMS に合っているか（ITEMS から外した作品の写し・画像が残っていないか）
    top = (HERE / "index.html").read_text(encoding="utf-8")
    for it in ITEMS + EXTERNAL:
        if it.get("state") and f'href="{href(it)}"' not in top:
            bad.append(f"index.html: {it['title']} のカードが無い")
    slugs = {it["slug"] for it in ITEMS + EXTERNAL}
    for d in HERE.iterdir():
        if d.is_dir() and d.name not in {".git", "drafts", "img", "__pycache__"} and d.name not in {it["slug"] for it in ITEMS}:
            bad.append(f"{d.name}/: ITEMS に無い作品の写しが残っている（消す）")
    for p in (HERE / "img").glob("*"):
        if p.stem.removeprefix("og-") not in slugs | {"site"}:
            bad.append(f"img/{p.name}: ITEMS に無い作品の画像が残っている（消す）")
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
    read_states()
    if not a.check:
        if not a.pages:
            make_images()
        build_pages()
        build_top()
    by = {}
    for it in ITEMS + EXTERNAL:
        by.setdefault(it.get("state") or "?", []).append(it["title"])
    print("状態: " + " ／ ".join(f"{k} {len(v)}" for k, v in by.items()))
    return check()


if __name__ == "__main__":
    sys.exit(main())
