# New REAL 土木 実技 questions, taken from screenshots of the official JAC 対策システム 小テスト

The user is a Thai civil engineer preparing for JAC 特定技能2号. He took the official online 小テスト (tokuteiginou2gou.com) and sent 45 screenshots, `/home/claude/jn/shots/a01–a15.png`, `b01–b15.png` and `c01–c15.png`. Read **every** screenshot with the Read tool.

There are two kinds of page:
- **Question pages** show one question with its 4 options. The user's selected option has a filled radio, and that selection may be wrong.
- **Result tables** (10 rows: 問題 / 回答 / 正解 / 正否 / テキスト頁) give the **official correct answer** (正解) and the textbook page (実技_NNN) for each of 10 questions.

These are REAL exam-bank questions, so copy the Japanese **exactly**, keeping the option order and characters as shown, e.g. 「何か。」「なんといいうか」.

## Step 1: build the list of new questions
- Collect every distinct question from both page types. Questions repeat across screenshots, so merge them.
- Compare against the 81 existing real questions in `/home/claude/l2/real_doboku.json`. Skip any question that is the same question as an existing one. A question that asks the same item from the other direction, or with a different stem, is NEW, so keep it.
- The answer:
  - from a result table, use 正解;
  - for a question page with no matching table row, decide the answer yourself with certainty from the JAC 実技 text and real practice; if unsure, use WebSearch.
- The options:
  - use the question page;
  - if a question appears **only** in a result table, its full options are unknown, so build 4 plausible sibling options (the correct one plus 3 related terms) and set `"recon": true`.
- Expected new items, as a guide; verify each one against the screenshots:
  新規入場者教育 / ボーリング孔を泥水で満たす / 布板(photo) / スクレーパー(photo) / 筋交 / Pコンの材料 / 路盤 / 路床 / 死亡事故最多=墜落 / 熱中症対策 / 解体工事 正しくない / ロードローラ / ダンプトラック / トラックアジテータ / コンクリートポンプ / 飛来・落下 / スランプ試験(photo) / フルハーネス / 近道行動(name←definition) / 鉄筋工事 正しくない / ガス圧接 バーナー(photo) / レーキ / 発進立坑 / スペーサー / タイヤローラ / アーク溶接=電気 / 緑十字 / 基層 アスファルトフィニッシャー / 墨出し / 足場板 / ポンプ車 / 圧接器(鉄筋継手 ① machine).
  - Drop 圧接器 if the photo with ① is not in the screenshots.
  - Also check that 地面を固める作業 is really an existing item, j041.

## Step 2: photos
For photo questions, crop the photo area out of the screenshot with PIL and save it as `/home/claude/build/img/jt_NNN.jpg`, quality 85, max side 900. NNN is the question's number. Keep any black box the site placed over the label. View every crop to check it.

## Step 3: output `/home/claude/jn/out.json`
Write an array of items with these fields:
- `id`: "j082", "j083", … in order;
- `cat`: one of j_dougu, j_tekkin, j_anzen, j_kaiyou, j_doko, j_kikai, j_kanri. 足場 items go in j_anzen and 型枠/Pコン in j_tekkin; for other items, see how existing items are categorised in `/home/claude/build/index.html` (const JQ);
- `src`: "実技小テスト P184" with the テキスト頁 number, or "実技小テスト" if no page is known;
- `stem_f`, `opts_f` with `漢字{かな}`: use the site's own furigana as the guide, but make sure every reading is correct;
- `ans`;
- `img` (optional);
- `recon` (optional);
- `life`: true when the item is general **safety (安全) or construction management (施工管理)** that applies equally to the ライフライン・設備 test. Examples: 熱中症, 墜落, 飛来・落下, 新規入場者教育, 近道行動, 緑十字, 死亡事故, QCDSE-type management. Do not set it for 土木-specific items such as 解体工事, 海洋, 舗装 or ボーリング;
- `sth`, `ath`, `oth`, `th`: write these exactly per `/home/claude/xl/INSTRUCTIONS.md` (read it first). They must be site-context Thai that is easy to understand, with `漢字{かな}` on every kanji, no option numbers, only `<b>`/`<br>`, and `oth` has "" at the answer.
  - Where the user's own selection in a screenshot was wrong, the `th` memory hook should target that confusion. For example, he answered 新入者安全衛生教育 instead of 新規入場者教育, 幅木 instead of 筋交, トランシット instead of レベル, コンクリート instead of プラスチック for Pコン, 表層 instead of 路床, コンクリートポンプ車 instead of トラックアジテータ, and ガス instead of 電気.

Also write a second file, `/home/claude/jn/life_existing.json`: a list of the ids of the EXISTING real items (j001–j081) that are general safety or construction management and apply equally to lifeline work. Leave out 土木-specific items such as 河川, 海洋, 圧送, 塗装 and 機械土工. Leave out exact duplicate pairs too, keeping only one of j060 and j073.

## Step 4: validate
Copy `/home/claude/l2/validate.py` to `/home/claude/jn/validate.py`. Change it to read `/home/claude/jn/out.json`, drop the src-format rule, and allow the j_ cats. Run it until it reports 0 problems.

## Reply with
- the validator line;
- the new items as `id — stem (short) — answer — recon? — life?`;
- the skipped duplicates as `screenshot question → existing id`;
- the life_existing list;
- nothing else.
