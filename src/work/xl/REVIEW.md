# Independent review of the Thai study notes

You are a strict second reviewer. Another writer produced Thai study notes for JAC construction exam questions (建設 特定技能2号), following `/home/claude/xl/INSTRUCTIONS.md`. Read that file first. You did not write these notes. Your job is to find and fix mistakes before a real learner studies them.

For each assigned batch NN:
- Input question: `/home/claude/xl/in_NN.json`. `ans` is the 1-based correct option. Look at `img` photos with the Read tool at `/home/claude/build/<img>`.
- Notes: `/home/claude/xl/out_NN.json`.

## Check every item for

1. **Translation accuracy.**
   - `sth` must say what the Japanese question really asks. Pay attention to negatives such as 正しくない, 不適切, 含まない, 誤り: the Thai must make the "choose the wrong one" direction obvious.
   - `ath` and `oth` must match the actual option text.
   - `oth` entries must line up with `opts` in the same order, with `""` at the answer's index.
2. **Facts.**
   - Numbers, laws, distances, heights, machine names and procedures must be right for Japanese construction practice and law.
   - Nothing may contradict the app's answer.
   - If a statement is doubtful, fix it or remove it. Never add guesses.
3. **Readings.**
   - Every `漢字{かな}` reading must be right in context.
   - The reading must also match the reading used in the stem/opts for the same word.
4. **Site context and clarity.** The user asked that the notes not be a literal translation, but explained in the context of real construction work so they are easy to understand. Fix Thai that is stiff, word-for-word, wrong in register, or uses non-construction wording for a site term.
5. **Rules.**
   - No reference to options by number or position.
   - Only `<b>` and `<br>` are allowed as markup.

## How to fix
- Edit the out file directly.
- Keep the JSON valid and the same structure.
- Then run `python3 /home/claude/xl/validate.py NN` until it shows 0 problems.
- Write a short log to `/home/claude/xl/review_NN.md`: one line per change, as `id — what was wrong → what you changed`. If you changed nothing, write "no changes".

## Reply with
- Per batch: the validator's final line and the number of changes.
- Any question where you think the app's answer itself is wrong (id + reason).
- Nothing else.
