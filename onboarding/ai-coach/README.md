# AI Setup Coach — free help for getting your shop right

You don't have to figure this out alone. `banco-doctor` reads your live install and tells you exactly what's
still unset — and any AI you already have (Claude, ChatGPT, or your own Ollama) can turn that into friendly,
step-by-step coaching. **Facts come from the doctor; the AI just makes them kind.**

## The doctor first (no AI needed, always right)

From the repo root:
```bash
python3 scripts/banco-doctor.py
```
You get a checklist: ✅ done · ⚠️ confirm · ❌ blockers, and a readiness %. It reads the *actual* values
(currency, VAT, passwords, backups, catalog), so it can't be fooled the way a guess can. Run it any time; run it
before go-live (you want **0 blockers**).

## Then let an AI coach you — two free ways

### Way A · Use the AI you already have (zero setup)
1. Get a **safe snapshot** (no passwords or keys are included):
   ```bash
   python3 scripts/banco-doctor.py --dump
   ```
2. Open your AI (claude.ai, ChatGPT, a local Ollama — whatever you use).
3. Paste in the contents of [`BANCO-SETUP-COACH.md`](BANCO-SETUP-COACH.md) **first** (that teaches it the job),
   then paste your snapshot and say: *"Coach me — what do I fix first?"*
4. It will walk you through the blockers in order, in plain language.

### Way B · Wire it to your Ollama Turbo (one command)
If you have an Ollama Turbo key, put `BH_OLLAMA_KEY` and `OLLAMA_TURBO_URL` in your `.env`, then:
```bash
python3 scripts/banco-doctor.py --explain
```
The doctor sends its findings to your model and prints the coaching right in the terminal — no copy-paste.

## Why this is safe
`--dump` shows only *verdicts* (e.g. "the database password is still a starter default") — never the actual
passwords, keys, or the backup passphrase. It's safe to paste into any AI. Your real secrets never leave your
machine.

> The doctor is the ground truth; the coach is the bedside manner. Trust the ❌ blockers — clear those first,
> then the ⚠️ confirmations, and you're ready to open.
