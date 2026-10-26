# frickey の工房（2026-10-26_portfolio）

ゲームと道具をまとめた作品集のサイト。https://frickey104.github.io/

- 作品の元のファイルは、それぞれのフォルダの `index.html`。このサイトにはその写しを置く
- 作り直し方: `python build.py` で、作品の写し（`<slug>/index.html`）・サムネイル・X のカード画像を作り直し、公開前の点検（個人の情報の言葉・外への読み込み・画像の撮影情報）をする。最後の行が `ok` なら上げてよい
- 載せる作品と並びは `build.py` の `ITEMS`。トップページは `index.html`
- 中身:
  - `index.html` — トップページ
  - `<slug>/index.html` — 作品の写し（`build.py` が作る。手で直さない）
  - `img/` — サムネイルと X のカード画像（`build.py` が作る）
  - `build.py` — 組み立てと点検
