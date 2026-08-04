# 14 · When it goes down — what actually breaks, and what is worth building

*Design note, 2026-08-04. Written after an evening that started with "should the shop run its own
server?" and ended with Angel arguing the other way and winning. Kept because the reasoning is more
useful than the conclusion.*

---

## The question

Banco runs at `banco.wolfhold.app`, on one box in a data centre. So **no internet means no selling.**
The tablet build gave the shop four network paths — shop Wi-Fi, phone hotspot, and two tablet SIMs
on two genuinely different Swiss networks — but every one of them reaches the same server.

That looked like an argument for running Banco **in the shop**. It mostly is not, and the reason is
worth writing down before someone re-derives it.

---

## What actually breaks — and what each option covers

| What fails | How often | Can the shop sell? | Does on-prem help? |
|---|---|---|---|
| **Power out** | rare, hours | ❌ card terminal dead, printer dead, lights out | **Barely.** Laptop and tablets have batteries — the *system* survives. The shop mostly does not. |
| **Internet out, power fine** | occasional, usually same-day | ❌ today | ✅ **Yes. This is the only case it genuinely fixes.** |
| **Bad deploy / app bug** | most likely of all | ❌ | ❌ **No.** The bad code follows you on-prem. |
| **Hetzner outage** | rare | ❌ | ✅ yes |
| **Shop server dies** | — | ❌ | 🆕 **a failure you did not have before** |

---

## The trade nobody mentions

> *Angel:* **"You're trading either your laptop is gonna save the day, or Hetzner is gonna save the
> day. And the Hetzner servers are extremely good — probably more reliable than some laptop."**

He is right, and it is the strongest point in the whole discussion.

A Hetzner box has redundant power, N+1 cooling, ECC memory, monitored hardware and staff on site
around the clock. The proposed shop server is a **2015 laptop found in the rubbish** with a consumer
SSD, no ECC, and a shop's worth of dust, heat and people who might need that socket.

**On-prem does not buy reliability. It buys independence from the WAN.** Those are different goods,
and it is easy to sell the second while implying the first. The honest expectation is that a shop
laptop has **more** downtime than Hetzner — just downtime you can walk over to and reboot.

---

## The realism argument

> *Angel:* **"Are we planning for something realistic here? Power comes back within four hours. If
> it's out for three days you've got bigger fish to fry than selling some papers. The question is: is
> the internet down and do we have a new internet connection? That's usually solvable the same day —
> a reboot in most cases."**

This is the part that settles it.

The scenario on-prem uniquely fixes is **internet down, power up, for longer than a shop can absorb.**
Against that we have already spent the money that matters: four independent paths, two of them on
separate mobile networks. For all four to fail at once *and* stay failed long enough to hurt is not
where the next franc of effort belongs.

And in the case that *is* common — a bad deploy, an app bug — on-prem does nothing at all. The bug
travels with you.

---

## Verdict: not now

**Do not build it.** Revisit only if one of these becomes true:

- The shop's internet proves genuinely unreliable **in practice, measured** — not feared. If the till
  logs outages over a few months, that is evidence. Until then it is a hunch.
- The shop grows past the point where a lost hour is absorbable.
- The on-prem hardware and someone to look after it are free anyway, *and* the HTTPS and remote-access
  problems below are already solved for other reasons.

**If it is ever built, the costs are not the app.** `docker compose up` is the easy half. The real
work is:

- **Keycloak signs its hostname into every token.** New hostname means `KC_HOSTNAME`, the realm
  issuer and every client redirect URI change together, or logins fail in ways that read like the app
  broke.
- **HTTPS on a LAN.** Plain `http://192.168.x.x` is **not a secure context**, so the phone's camera
  snap-fill stops working and it looks like a regression. Caddy handles it — **DNS-01 needs only a
  TXT record**, so a real Let's Encrypt cert is possible without publishing the shop's internal IP.
  Caddy also ships an internal CA as a fallback. **Traefik is not needed**; Caddy already does both,
  and swapping would mean rewriting `compose.prod.yml`, `Caddyfile.example` and `go-live.py` for zero
  gain.
- **Never use `.local`** — mDNS owns it and no public cert can be issued for it. Use subdomains of a
  domain we own.
- ⚠️ **Resolution must be local or the whole thing defeats itself.** A till resolving through public
  DNS cannot resolve anything when the WAN drops — the exact outage on-prem exists to survive.
  `/etc/hosts` on each machine is three files and zero infrastructure; `dnsmasq` on the shop box if
  the device list grows or phones need it (`/etc/hosts` cannot be edited on Android or iOS).
- **Tailscale for Angel's remote access, never as the shop's local path.** New Tailscale connections
  lean on its coordination servers, which is the one thing you do not want in the critical path of
  "the internet is down."

---

## What to do instead — all three already filed

The cheap things cover more of the real failure surface than the expensive thing does:

1. **Watch prod from outside it.** Right now the monitoring is Felix phoning. An external check on
   `/health/healthz` costs ten minutes and covers *every* server failure, including the bad deploy
   that on-prem would not have helped with.
2. **Restore a backup for real.** Never done. A backup looks identical whether it works or not, right
   up to the day it matters.
3. **Make the cart survive a crash.** The likeliest failure of all — one tablet, one dropped sale —
   and the one a cashier meets in person.

---

## And the answer that covers everything: paper

> *Angel:* **"You're gonna have to write it down and take the cash. That's all you can do."**

Every branch of the table above ends in the same place when it gets bad enough, and it costs nothing
to be ready for it. **The gap is not the paper — it is coming back from it.** See the backlog item on
re-entering offline sales.

**Angel's read on the price of getting that slightly wrong is worth recording**, because it changes
how much the fix is worth building:

> *"It would be the wrong time, when the sale didn't happen — but it wouldn't really be that bad,
> because it doesn't ever happen."*

So the expensive version — true backdating, shift reattribution, reopening a closed shift, a
permission story for editing money — is **not** justified by an event this rare. The cheap version
probably is: type the sales in when the system is back, and **use the cash box's existing note
mechanism to say why the drawer and the shift disagree.** Named cash reasons and notes already exist
from the 2026-08-03 work. An explained discrepancy is not a discrepancy; an unexplained one costs
somebody an evening.

That is the whole plan, and it fits on a line: **four ways onto the internet, paper when they all
fail, and a documented way back in.**
