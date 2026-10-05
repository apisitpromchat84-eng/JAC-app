# Content audit: ライフライン・設備 実技 practice questions

The user, a Thai civil engineer in Japan, looked at these questions and says that **some of the content seems wrong**. He wants you to decide and fix it yourself. These are practice questions generated from the JAC ライフライン・設備 text. They are not official, so their Japanese stems, options and answers **may themselves be wrong**. This audit is about the **questions**, not only the Thai notes.

First read `/home/claude/xl/INSTRUCTIONS.md` and `/home/claude/ll/INSTRUCTIONS.md`. They hold the rules for notes, readings and format.

Your batches: input `/home/claude/ll/in_NN.json`, current result `/home/claude/ll/out_NN.json`. Each out item has ans, stem_f, opts_f, sth, ath, oth and th.

## For every question, check
1. **Exactly one option is clearly correct.** No second option may also be defensible, and the keyed `ans` must be that option. Solve the question yourself first.
2. **The stem and options are factually right** for Japanese practice, law and the JAC ライフライン・設備 text. Things to check include:
   - 電気: 検電器, 検相器, クランプメーター, 短絡, 地絡, 漏電, 接地
   - 通信: 光ファイバー, コア/クラッド, 同軸, SC, OTDR
   - 電線管: PF/CD, E/C/G管
   - 塩ビ管: VP, VU, HIVP, HT and their colours
   - 消防: 屋内/屋外消火栓, 閉鎖/開放/放水型
   - 安全: 墜落制止用器具 6.75m / 5m guideline, 高所作業車 2m, 酸欠 18%, H2S 10ppm, WBGT
   - 埋設表示シート colours
   - 5M, 施工管理, 築炉, 保温材 and 工具
   Use WebSearch to confirm any fact you are not sure of. Prefer official Japanese sources such as JAC, 厚労省 and JIS.
3. **Photo questions:** open each photo with Read at `/home/claude/build/<img>`. The photo must really show what the answer says. If it doesn't, fix the question so the photo matches, or rewrite it as a text question with no photo (set `"img": null` in your out item).
4. **Wording:** the Japanese must be natural, unambiguous exam Japanese. Odd phrasing such as "テキストでは…求めています" for a guideline that only recommends should be made accurate.
5. **Readings:** every reading in stem_f/opts_f must be correct.

## How to fix
- Edit the out item directly. You may change ans, stem_f, opts_f, or the photo (`"img": null` to drop it).
- Whenever the Japanese text changes, add `"edit_note": "<short Thai explanation of what was wrong and what you changed>"`. Without it, the validator rejects any change to the text.
- Then rewrite sth/ath/oth/th so they match the corrected question.
- Keep 4 options. Do not cite option numbers.
- Run `python3 /home/claude/ll/validate.py NN` until it reports 0 problems.
- Log each change in `/home/claude/ll/audit_NN.md` as `id — problem → fix (source if any)`.

Be decisive but do not invent. Change only what is actually wrong or ambiguous.

## Reply with
- per batch: the validator line and the number of questions changed;
- a list `id: problem → fix`;
- nothing else.
