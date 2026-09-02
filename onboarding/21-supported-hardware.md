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
- ⚠️ **THE GOOD GUN IS DONGLE-ONLY, AND THAT DECIDES THE COUNTER DEVICE.** The NETUM has no
  Bluetooth — it needs a USB-A port. The Bluetooth gun that *would* work on an iPad is the cheap
  one, and it reads **about 90%** of real stock: small EAN codes and curved packaging defeat it
  repeatedly. **A till that fails one scan in ten is not a till.** So the device must have USB-A,
  which rules out every iPad regardless of price, and rules out most Android tablets without a hub.
  This is a harder constraint than printing and it is worth stating first.
- **Set the gun's keyboard layout to match the session's**, or every hyphenated SKU silently mutates
  while EAN-13 scanning looks perfect.

---

## A tablet is not a setup machine, and that is not a Banco limitation

**Product setup is laptop work.** Typing names, prices, costs, categories and descriptions for
hundreds of items is a keyboard job, on any system, with any software. A tablet is for *walking the
shop* — shelf intake, price checks, a sale at the counter.

This matters for expectations more than for engineering: **the first weeks of a shop going live are
almost entirely setup**, and doing that on a tablet is choosing the wrong tool and then blaming the
software. No POS on the market is different. Orange, Shopify and Lightspeed all assume a keyboard
for catalogue work.

## The next x86 machine will arrive with Windows on it. Wipe it.

*Asked 2026-09-02. The answer is yes — with one gate before you erase anything.*

**Wipe to Debian 13, the same as the X1 Tablet, and follow the same runbook**
([`13-tablet-x1-debian.md`](13-tablet-x1-debian.md)). Not because Linux is better in the abstract —
because **one image, one runbook, one thing to support**. The counter machine is something you will
be SSH-ing into at 16:40 on a Saturday with a queue at the till, and at that moment the only thing
that matters is that it is identical to the one you already know.

**⛔ The gate, before you erase a single byte: boot a Debian live USB and check the hardware.**
Wifi, touch, sleep/resume, sound, the LTE modem if it has one, and the trackpad. Twenty minutes. If
any of it is broken on the live USB it will still be broken after the install, and *then* you own it.
This is the whole risk of the choice, and it is entirely knowable in advance for free.

**Do not dual-boot.** A counter machine that can boot into the wrong operating system will, on the
morning nobody has time.

### SWOT

| | |
|---|---|
| **Strengths** | One image and one runbook across every counter. No licence, no activation, no forced reboot mid-shift, no update at 14:00 on a Saturday. SSH support from anywhere — the thing the monthly service fee is actually made of. Runs light on used hardware, which is the whole reason x86 is the leverage. Kiosk mode is deterministic. Full disk encryption and backups are already scripted. |
| **Weaknesses** | Drivers are a real risk on unknown hardware — wifi chipsets, sleep/resume, LTE modems, fingerprint readers. Windows would have given a working on-screen keyboard for free. Nobody else in the shop can fix a Linux box, which makes the bus factor exactly one. Resale value of a wiped machine is lower. |
| **Opportunities** | *"Buy a used ThinkPad, wipe it, own it"* is a far better story for a self-hoster than *"buy our terminal"* — it is the ownership thesis expressed in hardware. It also makes a spare counter machine a €200 decision instead of a €900 one, and a shop with a cold spare on the shelf is a shop that cannot be taken down by a dead laptop. |
| **Threats** | A machine that qualifies on the live USB and then breaks on a kernel update six months later. Vendor firmware that fights Linux (some 2-in-1s). And the honest one: every hour spent qualifying hardware is an hour not spent on the catalogue, which is the actual business. |

**The weakness that used to be decisive is gone.** Until 2026-09-01, *"Windows has a working
on-screen keyboard and Debian on this tablet does not"* was a genuine reason to think twice.
**Banco now draws its own keypad**, so the operating system no longer has to provide one — which is
exactly what makes wiping to Debian the safe answer rather than the brave one. That is the second
time this week the keypad has paid for itself.

**One distinction, and keep it straight:** Banco does **not** require Linux. It is a web app and it
runs perfectly well in a browser on Windows. This section is about the **counter appliance** — the
machine you support, image and replace — not about what a customer is allowed to use.

## 🔴 TURN THESE OFF ON EVERY COUNTER MACHINE — they break the scanner gun

*Found 2026-09-02, on the till, with a gun about to be tested. Two of them were already ON.*

A barcode gun **is a keyboard**. It types thirteen digits in about fifty milliseconds and it sends a
SHIFT with them. GNOME's accessibility toggles sit one tap away in the top bar — behind the little
person icon — and three of them are, precisely, *"ignore keys typed quickly"*:

| setting | what it does to a scan |
|---|---|
| **Slow keys** | a key must be **held** before it registers → most of the barcode is dropped |
| **Bounce keys** | ignores fast repeats → `4455` arrives as `45`, silently, and the wrong product rings up |
| **Sticky keys** | latches modifiers → the gun's SHIFT lands on the wrong character (this shop already has `sKU-`, LESSON #1) |
| **Mouse keys** | the number pad moves the **pointer** instead of typing → no digits at all |
| **Zoom / magnifier** | one tap, magnifies everything, **no obvious way back** on a touchscreen |

Angel hit the magnifier by accident and could not undo it: *"now it's impossible to set it back — I
think I need to reboot."* A reboot does not help; it is a saved setting.

**Set them, and hide the menu that offers them:**

```bash
for k in slowkeys-enable bouncekeys-enable stickykeys-enable mousekeys-enable togglekeys-enable; do
  gsettings set org.gnome.desktop.a11y.keyboard $k false
done
gsettings set org.gnome.desktop.a11y.applications screen-magnifier-enabled false
gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled false
gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled false
gsettings set org.gnome.desktop.a11y always-show-universal-access-status false
```

The icon disappears once every one of them is off — it is shown whenever any is on.

⚠️ **This is a diagnosis trap, not just a config trap.** A gun with slow keys on looks like a
**broken gun**: it beeps, and half the code arrives. The shop buys a second gun. Check this before
believing any scanner fault — same family as the flat battery that cost an hour on 2026-09-01.

### The other touch settings, and what they are actually worth

| setting | verdict |
|---|---|
| **Large text** | scales GNOME's own UI, **not** the browser — it does nothing to Banco. If the till's own text is too small that is a Banco CSS job, not an OS one. |
| **High contrast** | restyles GTK apps; the till is a web page, so again no effect on Banco. |
| **Screen reader** | off. It reads the desktop aloud at a counter. |
| **On-screen keyboard** | off, and it has never worked in any browser on this machine — that is the whole reason Banco draws its own keypad. |
| **Display scaling ×1.25** | this one WOULD make every Banco target bigger, and it is `gsettings set org.gnome.desktop.interface text-scaling-factor 1.15`. It changes the layout, so it is a decision, not a default. |

### And on the browser itself

```
--overscroll-history-navigation=0   # a horizontal swipe was browser BACK — mid-sale
--disable-pinch                     # no accidental pinch-zoom on a till
--force-device-scale-factor=1       # start at 100%, always
--start-maximized                   # NOT --kiosk: see the section above
```

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
