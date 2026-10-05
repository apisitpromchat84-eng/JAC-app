# Make ver.2 questions look like the REAL JAC 実技 exam

The user wants the home-made lifeline set (`out_hX.json`) to resemble the real CBT exam as closely as possible.

**Ground truth:** `/home/claude/l2/real_doboku.json` holds 81 REAL exam questions (土木, verbatim). Read all of them first. Study how the stems are worded and how the options are built.

**Scores:** `/home/claude/l2/realism.json` gives every item `topic` (A/B/C), `format` (1 = already real-like, 2/3 = needs work), `real_match` and `suggest`.

Read `/home/claude/xl/INSTRUCTIONS.md` and `/home/claude/l2/INSTRUCTIONS.md` for the note and reading rules. They still apply in full:
- `漢字{かな}` everywhere;
- site-context Thai;
- full sth / ath / each oth / th;
- no option numbers.

## Real exam style, in brief
- **Name questions (about 64%).** Paste the textbook definition into the stem and ask 「〜はなんですか。」「〜を何と言いますか。」「〜はどれですか。」, or with a photo 「写真の〜の名前を選びなさい。」「写真の正しい用語を選びなさい。」. The options are four short names.
- **Definition questions (about 36%).** 「Xの説明で正しいものを選べ。」「Xの用途で正しいものを選びなさい。」「写真の道具は、何のために使用しますか、正しいものを選びなさい。」. The options are near-verbatim textbook definitions of **sibling items** from the same page.
- **Blanks（　　　）are rare.** Use one only when the blank sits naturally inside a sentence, as in 「コンクリート圧送工事では、生コンを打設する前に、（　　　）を送って…」.
- **Negative questions** are worded 「正しくないものを選べ」「間違いはどれですか」「〜でないものを選べ」「含まれないものはどれですか」「行わないものはどれですか」, **never 誤っている**.
- **Photos** appear in about 1/3 of questions.
- There are **no** combination, ordering or "pick the right pair of numbers" questions.

## What to do in your file
1. **Rewrite every format-2 and format-3 item** toward the real style, following `suggest` and using your own judgement.
   - Typical fix: change 「…は、（　　）です。」 to 「…はなんですか。」, keeping the same 4 name options.
   - Typical fix: rewrite a "mutated statement" item as 「Xの説明で正しいものを選べ。」, with sibling definitions as the options.
   - Keep a blank only where it reads like j005, j011 or j024.
2. **Combination, ordering and number-pair items:** turn each into a single-fact real-style question. For example, 「土被りは車道では（　　）m以下にしてはいけません」 can keep the number fact. If a number fact is truly exam-worthy, one blank-in-sentence question is acceptable.
3. **Change all 「誤っているもの」 wording** to 「正しくないもの／間違いはどれですか」 forms.
4. **Photos:** where the user highlighted a photo, or the item is a tool or part, and a textbook figure exists in `/home/claude/l2/fig/` (`/home/claude/l2/index.json` maps pages to figures), convert the item to a photo question.
   - Use 「写真の〜はなんですか／写真の正しい用語を選びなさい／写真の道具は、何のために使用しますか」.
   - Set `img` and `crop`, and **hide the printed label**. Verify the crop by viewing it: PIL-crop it to `/tmp/claude-0/rf_<id>.jpg` and Read it.
   - Aim for about 30% photo items in your file, but only where a clean figure exists.
5. **Topic-A items** (those with a `real_match`): make the question mirror that real j-item's wording and option style as closely as is factually right for the lifeline textbook.
   - If the real exam asks only one direction, you may add **one** mirror item for the other direction, with a new id `hX-NNm`.
6. **Format-1 items:** leave them alone, apart from fixing 誤っている wording.

## Keep
- Facts must match the textbook page in `src`; check `/home/claude/l2/pages/`.
- Exactly one correct answer.
- Distractors stay plausible: siblings from the same page. Do NOT make them silly.
- Mix 選べ and 選びなさい naturally; both appear in the real exam.
- Keep `hl`, `from` and `dup_of`.
- Rewrite the Thai notes whenever the Japanese changes, so they fully match.

Run `python3 /home/claude/l2/validate.py hX` until it reports 0 problems. Log the changes in `/home/claude/l2/realfix_hX.md`.

## Reply with
- the validator line;
- items changed / added / removed;
- photo count before → after;
- nothing else.
