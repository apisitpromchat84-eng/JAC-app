# ライフライン・設備 実技: solve, fix readings, write Thai study notes

First read `/home/claude/xl/INSTRUCTIONS.md` completely. Every rule about the Thai notes applies here unchanged:
- site-context Thai, not a literal translation;
- `漢字{かな}` readings on every kanji;
- never cite option numbers;
- only `<b>` and `<br>` as markup;
- correct facts only.

The user insisted that the notes explain things in the context of real work so they are easy to understand. They are not a literal translation.

The differences for this set are below.

## About the source
These 110 questions are **practice questions for the JAC 建設分野 特定技能2号 ライフライン・設備 実技 test**. They are built from the official JAC text for that category (電気通信, 配管, 空調・衛生, 消防, 築炉, 保温保冷, 板金, 安全, 施工管理, 地下埋設物 …).

**The PDF has no answer key, so you must determine the correct answer yourself.**
- Use your knowledge of Japanese construction practice, Japanese law and the JAC ライフライン・設備 text. Use the photo for photo questions.
- If two options could be defended, or none is clearly right, pick the best one. Also describe the problem in `flag`.

**The furigana extracted from the PDF is unreliable.** It was machine-generated, and many readings are wrong:
- 細い read as こまい instead of ほそい
- 通る read as とうる instead of とおる
- 運搬車 read as うんぱんくるま instead of うんぱんしゃ
- 発注者 read as はっちゅうもの instead of はっちゅうしゃ
- 小さい read as ちーさい instead of ちいさい

So you must re-write the question and options with correct readings.

## Input / output
- Input: `/home/claude/ll/in_NN.json`.
  - Each item has id, cat, src, stem, opts and img.
  - stem and opts show the PDF readings as `漢字(かな)`, and these may be wrong.
  - There is no ans.
  - Photos: Read `/home/claude/build/<img>` before answering.
- Output: `/home/claude/ll/out_NN.json`. It is a JSON array with one object per question, in the same order:

```json
{"id":"l001",
 "ans": 4,
 "stem_f": "写真{しゃしん}の建設{けんせつ}機械{きかい}の名称{めいしょう}は何{なん}ですか。",
 "opts_f": ["タワークレーン", "トラッククレーン", "ホイールローダ", "クローラクレーン"],
 "sth": "...", "ath": "...", "oth": ["...","...","...",""], "th": "...",
 "flag": "optional"}
```

- `ans` is the 1-based index of the correct option, in the input order.
- `stem_f` and `opts_f` are the **exact same Japanese text** as stem/opts with the `(かな)` removed, and every kanji run annotated as `漢字{かな}`.
  - Do not change, add or drop any character of the Japanese. The validator compares them.
  - Keep `（　　）` blanks as they are.
  - Each `{}` must hold a correct hiragana reading for this context.
  - Okurigana stays outside the braces, e.g. `選{えら}び`, `細{ほそ}い`, `締{し}め固{かた}める`.
  - You may split a compound into smaller annotated pieces if that is clearer.
- `oth` has `""` at index ans-1, as in the original instructions.

## When done
Run `python3 /home/claude/ll/validate.py NN` until it reports 0 problems.

Then reply with:
- the final validator line;
- the list of any flags (id + one line);
- a list of questions that duplicate another question in this batch or test exactly the same fact (ids only).
