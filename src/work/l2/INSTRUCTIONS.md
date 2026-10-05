# ライフライン・設備 ver.2: write exam questions from the official JAC text

You are writing **new practice questions** for a Thai-language study app for the JAC 建設分野 特定技能2号 exam, ライフライン・設備 実技 区分. The user is a Thai civil engineer in Japan.

This is "version 2" of the lifeline set. It must be built **directly from the official JAC 実技試験テキスト** (texts 5, 6 and 7). Every question needs a page reference, so the learner can open the textbook at that page.

**First read `/home/claude/xl/INSTRUCTIONS.md` completely.** All of its rules for the Thai notes apply here:
- site-context Thai, not a literal translation;
- `漢字{かな}` readings on every kanji;
- never cite option numbers;
- only `<b>` and `<br>` as markup;
- correct facts only.

## Sources
- PDFs: `/home/claude/l2/text5l.pdf` (第5章 tools, machines, materials, measuring instruments), `/home/claude/l2/text6l.pdf` (第6章 construction work on site) and `/home/claude/l2/text7l.pdf` (第7章 safety).
- Per-page extracted text, named by **printed page number**: `/home/claude/l2/pages/text5l_p118.txt` and so on. Furigana lines are mixed into the text.
- Figures cropped from each page: `/home/claude/l2/fig/text5_p118_1.jpg` and so on. `/home/claude/l2/index.json` maps every page to its pdf page number and figure files.
- **Read every page in your range visually** with the Read tool on the PDF (the `pages` parameter uses the PDF page number from index.json, at most 20 pages per call). Use the .txt files to copy exact Japanese.

## What to write
Cover **every exam-worthy fact** in your page range:
- each tool, machine, material and instrument: its name, its use, how to use it, and how not to use it;
- every procedure step and its order;
- every number: heights, %, ppm, mm, colours;
- every rule, every safety point, every "do not".

Aim for one question per distinct testable fact, typically **1–3 questions per page**. Skip pure headings and tables of contents.

Question styles must match real JAC 実技 questions:
- 「写真の〜の名称は何ですか。」 / 「写真の〜の用途として、正しいものを選びなさい。」 for photo questions;
- 「〜の説明として、正しいものを選びなさい。」;
- 「〜について、誤っているものを選びなさい。」 / 「〜に含まれないものはどれですか。」 / 「適切でないもの」 for negative questions;
- 「〜は、（　　）です。」 / 「〜を（　　）といいます。」 for blanks.

Also:
- Keep 4 short options that are all plausible. Take distractors from neighbouring items in the same text where possible, for example other tools on the same page.
- Mix the position of the correct answer across 1–4.
- Use natural exam Japanese. Never write 「テキストでは」.
- Mix question types. Do not make every question "which is correct".

### Photo questions
Use a figure only when it clearly shows one identifiable item. Open the figure image first.
- Most figures have the item's **name printed on the photo**. You must hide it by giving `"crop": [x0, y0, x1, y1]`, fractions 0–1 of the image width/height, that keeps the object but cuts the label off. Check where the label is before choosing the crop.
- If the label cannot be removed without losing the object, do not use that figure for a "name" question. Write a text question instead, or a "用途" question whose options don't depend on the label.
- Skip figures that combine several small items.

### Relation to the existing set
`/home/claude/l2/existing_110.json` is the older 110-question practice set. Version 2 is kept **separate**, so overlap is allowed. If one of your questions tests the same fact as an existing one, set `"dup_of": "l0NN"`. The app uses this to avoid showing both in one mock exam.

## Output
Write `/home/claude/l2/out_X.json` (X is given in your task). It is a JSON array of objects:

```json
{"id":"X-01", "cat":"l_denki", "src":"L5 P104",
 "stem_f":"写真{しゃしん}の工具{こうぐ}の名称{めいしょう}は何{なん}ですか。",
 "opts_f":["圧着{あっちゃく}ペンチ","ワイヤーストリッパー","パイプカッター","電工{でんこう}ナイフ"],
 "ans":1,
 "img":"fig/text5_p104_3.jpg", "crop":[0,0.15,1,1],
 "sth":"…", "ath":"…", "oth":["","…","…","…"], "th":"…",
 "dup_of":"l0NN or omit"}
```

- `src` is "L5"/"L6"/"L7" followed by the **printed** page number, for example `L6 P142`. Use `L6 P142-143` if a fact spans two pages.
- `cat` is one of:
  - `l_kikai`: machines;
  - `l_denki`: electrical and telecom;
  - `l_kankan`: piping, sanitary, HVAC, fire protection, insulation and sheet metal;
  - `l_dougu`: hand and power tools, processing and measurement;
  - `l_anzen`: safety;
  - `l_kanri`: construction management, buried utilities, roads and general site knowledge;
  - `l_chikuro`: furnace brickwork.
- `img` is optional, given as a path relative to /home/claude/l2. `crop` is optional.
- Every reading in stem_f/opts_f must be correct. The text's own furigana is a good guide, but its line-mixing can mislead.

## When done
Run `python3 /home/claude/l2/validate.py X` until it reports 0 problems.

Reply with:
- the validator line;
- the number of questions, and how many have photos;
- the pages you found nothing testable on;
- nothing else.
