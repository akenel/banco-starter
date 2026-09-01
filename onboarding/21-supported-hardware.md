# 21 · Supported hardware — what Banco runs on, and what it does not

*Written 2026-09-01, after a full day lost to a counter tablet that would not raise a keyboard.
This page exists so that day is never repeated, by us or by anyone who clones this repo.*

---

## The one sentence

**Banco is a web app, so it renders on any modern browser. Banco is a point of sale, so it also has
to print, scan and take payments — and that part is hardware, not HTML.** Those are two different
promises and only the first one is universal.

Every POS on the market publishes a supported-hardware list. Square, Lightspeed, Shopify, Orange —
none of them says *"any tablet"*. Neither do we. **"Runs on this documented kit" is a product.
"Runs on anything" is an unbounded support contract.**

---

## The reference kit — this is what is tested

| | what | why it is the one |
|---|---|---|
| **Counter device** | ThinkPad X1 Tablet · Debian 13 · GNOME 48 · Chromium kiosk | a full x86 computer: prints via CUPS, takes the gun's USB dongle, and can run the whole stack locally if the network dies |
| **Scanner** | NETUM NSL8 · **two of them**, one always charging | reads a screen as well as paper, and copes with crumpled and curved labels |
| **Label printer** | Brother QL-820NWB over Bluetooth · `printer-driver-ptouch` | the only path that has actually produced labels — `brother_ql` and `brother_ql_next` printed zero |
| **Browser** | Chromium 84+ | below that, optional chaining is a *syntax* error and a whole `<script>` block silently refuses to parse |

Everything else is unqualified. That is not a judgement about the hardware; it means nobody has
run the sheets on it.

---

## 🔴 THE REQUIREMENT NOBODY KNEW UNTIL 2026-09-01

> ### The counter device must raise its own on-screen keyboard.

Check this **before buying anything**, because it is invisible until a cashier is standing at a
till unable to type, and it cannot be fixed by us on the device's behalf.

**The test takes ten seconds.** Open any web page with a text box on the device, detach or ignore
any physical keyboard, and **tap the box with a finger**. The keyboard must appear **by itself**.
If you have to swipe it up, the device fails.

**What we found on the ThinkPad**, by elimination, all of it measured on the machine:

| | keyboard appears on its own? |
|---|---|
| the GDM login screen | ✅ |
| GNOME Text Editor (a native app) | ✅ |
| Banco in Chromium | ❌ |
| Banco in Firefox | ❌ |
| **a blank HTML file with three plain inputs** | ❌ |

That last row is the one that matters: **no Banco code, no CSS, no JavaScript, same failure.** It is
not our bug and it is not fixable by us at the OS level. Tried and did not work: GNOME's
`screen-keyboard-enabled true` (keep it — it is what makes GNOME's half work), a session restart,
detaching the folio, a full system and Chromium update, and forcing native Wayland with
`--ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3`.

**So Banco draws its own keypad on that device** (`src/static/pos/pos-keypad.js`), and only on that
class of device — a touchscreen running a desktop OS. **Phones and tablets running Android or
iPadOS are deliberately left alone**, because their own keyboards are better than anything we would
write and every job taken from the OS is a job maintained forever.

---

## What a different device would cost

Nothing here is a reason not to change. It is the price list.

| | ThinkPad · Debian | Android tablet | iPad |
|---|---|---|---|
| raises its own keyboard | ❌ *we work around it* | ✅ | ✅ |
| prints to the Brother QL via CUPS | ✅ | ❌ | ❌ |
| takes the scanner's USB dongle | ✅ | ~ needs OTG | ❌ Bluetooth only |
| runs the stack locally when the network dies | ✅ | ❌ | ❌ |
| kiosk lockdown | ✅ `--kiosk` | ~ | ~ Guided Access |
| you own it outright | ✅ | ~ | ❌ |

**A newer tablet does not remove the problems — it swaps them.** The keyboard hole closes and the
printing hole opens, and printing is the harder one: neither Android nor iPadOS has CUPS, so the
label path would have to be rebuilt, possibly around a different printer.

**Qualifying a new device is a piece of work, not a setting.** It means running
`onboarding/testsheets/2026-09-01-keypad-on-the-till.html` and the shelf-intake and label sheets on
the actual machine. Budget a day. **Say so before agreeing to it.**

---

## Scanner guns — buy two of the same one

Full detail, including the keyboard-layout trap and both manuals:
[`testsheets/Scanners/README.md`](testsheets/Scanners/README.md).

- **Two identical guns, one always on charge.** Two *different* guns means two sets of modes,
  pairings, dongles and capabilities — all discovered under pressure, in front of a customer.
  Learned 2026-09-01: swapping to a different spare cost five minutes.
- **A flat gun looks exactly like a software bug.** The tell is a **double beep and no red flash**.
  There is no low-battery warning. It cost twenty minutes on 2026-09-01 and read as a broken screen
  on two unrelated pages. **Charge it and re-test before debugging anything.**
- **A cheap gun cannot read a barcode off a screen.** Any on-screen self-test must *receive* a code,
  not display one.
- **Set the gun's keyboard layout to match the session's**, or every hyphenated SKU silently mutates
  while EAN-13 scanning looks perfect.

---

## What to say when someone brings their own device

> *"Banco runs in a browser, so it will render on almost anything. What it cannot promise is the
> hardware around it — the keyboard, the label printer and the scanner are the operating system's
> job, and every OS does them differently. Here is the kit that is tested. Anything else is a day's
> work to qualify, and I will tell you honestly what it can and cannot do."*

No vendor on earth guarantees arbitrary hardware. The ones that appear to are simply refusing to
sell you the software without their own box.

---

*Related: [`13-tablet-x1-debian.md`](13-tablet-x1-debian.md) · [`08-label-printer.md`](08-label-printer.md) ·
[`10-devices-and-roles.md`](10-devices-and-roles.md) · [`16-bom-artemis-luzern.md`](16-bom-artemis-luzern.md)*
