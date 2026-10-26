# frickey の工房（2026-10-26_portfolio）

ゲームと道具をまとめた作品集のサイト。https://frickey104.github.io/

- 作品の元のファイルは、それぞれのフォルダの `index.html`。このサイトにはその写しを置く
- 作り直し方: `python build.py` で、作品の写し（`<slug>/index.html`）・サムネイル・X のカード画像を作り直し、公開前の点検（個人の情報の言葉・外への読み込み・画像の撮影情報）をする。最後の行が `ok` なら上げてよい
- 公開・非公開の切り替え: `build.py` の `ITEMS`（外のものは `EXTERNAL`）で、その作品の行の `public=True` を `public=False` にして `python build.py` → PC から上げ直す。トップのカード・写し・画像が消え、`links.md` の状態が「非公開」になる。戻すときは `True` にして同じ手順（状態は「公開待ち」になるので、広報部が確かめて「公開中」に戻す）
- 載せる作品と並びは `build.py` の `ITEMS`。トップページの `index.html` は `build.py` が `_top.html`（手で書く元・全作品のカード入り）から作る。トップを直すときは `_top.html` を直す
- 中身:
  - `index.html` — トップページ（`build.py` が `_top.html` から作る）
  - `_top.html` — トップページの元（`_` で始まるので公開されない）
  - `<slug>/index.html` — 作品の写し（`build.py` が作る。手で直さない）
  - `img/` — サムネイルと X のカード画像（`build.py` が作る）
  - `build.py` — 組み立てと点検
