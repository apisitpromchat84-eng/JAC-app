# ライフライン ver.2: write a SMALL, focused set from the user's highlights

The user is a Thai civil engineer in Japan. He has **already sat the real JAC 特定技能2号 ライフライン・設備 実技 exam**. He then marked in his official textbook the points that actually appeared on the exam, using green/yellow highlighter, red underlines, circles, and Thai handwriting. He wants a **small, efficient** practice set built **only from those highlighted points**. He does NOT want the whole book covered; an earlier 418-question attempt was rejected as too many.

## Read first
1. `/home/claude/xl/INSTRUCTIONS.md`: the rules for the Thai notes. They are binding:
   - site-context Thai that is easy to understand, not a literal translation;
   - a `漢字{かな}` reading on every kanji, including inside the Thai notes;
   - never cite option numbers;
   - only `<b>` and `<br>` as markup;
   - correct facts only.
2. `/home/claude/l2/INSTRUCTIONS.md`: the question format, JAC 実技 question styles, photo/crop rules, src format and cat list.
3. `/home/claude/l2/hl/highlights.md`: the log of what the user highlighted. Work only on the section(s) listed in your task.
4. **The user's photos** `/home/claude/l2/hl/b*_NN.jpg` for your range. Open each with Read, because the image itself is the truth.
   - The log's page numbers may be wrong. Check each page against `/home/claude/l2/pages/text5l_pNNN.txt` and the printed page number in the photo; `grep` helps.
   - Everything highlighted, underlined, circled or boxed is a target.
   - The user's Thai handwriting shows the angle the exam took, for example "what does this mean", "which is wrong", or "the colour is …".

## What to produce
For **each highlighted point**, write **1 question**. Write **2** only when the point clearly has two different exam angles, for example the name from a photo **and** the use from a description, or a number **and** a definition. Do not pad.

Use the exam angles that real JAC 実技 uses:
- 写真の〜の名称は何ですか
- 〜の用途/説明として正しいもの
- 誤っているもの
- 〜は（　　）です

When a page lists parallel items, such as VP/HIVP/HT, 短絡/地絡/漏電, the colours of 表示シート, or QCDSE, the siblings make excellent distractors for each other.

### Reuse the reserve first
`/home/claude/l2/reserve_418.json` holds 418 questions that were already written and reviewed from the same textbook, each with a `src` page.
- For each highlighted point, look for reserve items on that page that test exactly the highlighted fact.
- If one fits, **copy it**: keep its id in a new field `"from":"5a-12"`. Improve it if needed, for example to match the highlighted angle or to fix anything wrong.
- If nothing fits, write a new item.
- Never copy reserve items about non-highlighted content.

### Photos
- Use a textbook figure from `/home/claude/l2/fig/` (`/home/claude/l2/index.json` maps pages to figures) when the user highlighted the photo or its label, or when the item is a tool or part best recognised visually.
- Hide the printed label with `crop`, and check the result by viewing it. A quick way to check is to crop with PIL to `/tmp/claude-0/chk_*.jpg` and Read it.
- Reserve items with images already have a reviewed crop; keep it.

### Facts
Facts must match the textbook page exactly, including numbers, colours and wording. Copy the Japanese terms exactly from the .txt page.

## Output
Write `/home/claude/l2/out_hX.json` (X is given in your task), in the same item format as `/home/claude/l2/INSTRUCTIONS.md`, with these differences:
- `id`: `"hX-01"` and so on.
- Add `"hl":"b6_03"`, naming the user photo the point came from.
- Keep `dup_of` when it applies: compare against `/home/claude/l2/existing_110.json`, or carry the reserve item's `dup_of` over.

Run `python3 /home/claude/l2/validate.py hX` until it reports 0 problems.

## Reply with
- the validator line;
- the number of questions (how many reused / new / with photo);
- a list of `highlight point → question id(s)`;
- any highlighted point you deliberately skipped, and why;
- nothing else.
