# tools/ — tests and helpers for แอป JAC

Kept here so a new chat/session does not have to rewrite them. Nothing in this folder is deployed (only `public/` is).

Paths assume the app source is at `/home/claude/build` (copy `src/app` there) and this repo at `/home/claude/repo`.
Chromium path: `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` (edit if different).

## Before every deploy
```
cd /home/claude/build && python3 pack.py          # builds dist/
python3 /home/claude/repo/tools/t_smoke.py        # every tab, sheet and mode; must print OK twice
```
Then bump `CACHE` in `sw.js`, add a `WHATS_NEW` entry + guide image, copy `dist` to `public/`, commit, push.

## Tests
| file | checks |
|---|---|
| t_smoke.py | opens every tab / sheet / mode in all parts, fresh and with data — any page error fails |
| t_audit.py | question data: answer in range, translations present, duplicate stems |
| t_slow.py | weak signal: page answers after 10 s, app must still open in ~3 s from the saved copy |
| t_split.py | privacy cover: phone/iPad only on leaving the app, computer also on lost focus |
| t_shield.py | privacy cover + PrintScreen flash, screenshots to `shield/` |
| t_mini.py | ทดสอบย่อย progress (ทำแล้ว / มั่นใจ+ถูก) |
| t_gram.py, t_rz.py, t_wn2.py | grammar helper, readiness card, what's-new popup |
| t_asst.py, t_kb.py, t_kbeval.py | assistant commands and knowledge search accuracy |

## Guide images (every user-visible update)
`python3 guide_render.py <folder with guide.html> <version id> <name1,name2>`
→ 1080×1350 PNG for LINE in the folder + `img/whatsnew/<id>/<i>.webp` for the app.
Start from `guides/template_phone.html` (steps + phone screenshot) or `guides/template_wide.html` (steps + wide crop); put the screenshot next to it.

## Mock server for /stats
`mockserver/server2.mjs` imitates the worker + D1 locally (copy `worker.js` and `stats_page.js` from the repo root into mockserver/ first, then `node server2.mjs`); `seed.mjs` fills demo data;
`t_people.mjs` checks people counting (needs `STATS_KEY` env var = the stats password; never commit the password).

## Grammar PDF
`make_gram_pdf.py` + `gram_items.py` → jac_question_grammar.pdf

## Sync + explainer tests (need the mock server running on :8790)
| file | checks |
|---|---|
| t_sync.py | device A turns ☁️ sync on → fresh device B with the same nickname is offered the pull and pulls → B studies → A is told B is newer and pulls → wrong PIN on device C is refused |
| t_confhelp.py | มั่นใจ / ยังเดาอยู่ explainer: open on the first practice quiz, ? toggles, "เข้าใจแล้ว" closes for good |

## Trap-grammar handout
`make_trap_pdf.py` (+ `rawq.json`, `trap_stats.json`) → jac_trap_grammar.html, print to PDF. Negative / extreme grammar in "choose the WRONG one" questions.
`make_trap_all_pdf.py` (+ `neg_all.json`) → every "choose the WRONG one" question (84): A = answer has trap grammar (26), B = wrong by content (58).
