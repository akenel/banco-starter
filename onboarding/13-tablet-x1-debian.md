# 13 · Putting Debian on the X1 Tablet

*Started 2026-08-04. Felix handed over a detachable ThinkPad running Windows 10 in German. This is
the plan to make it a Banco machine that Angel owns outright — same principle as the stack itself.*

---

## What the machine is

Identified from "Intel Core i5 vPro, 7th gen, detachable touchscreen, has an IMEI":

**ThinkPad X1 Tablet, 2nd Generation (2017)** — Lenovo model `20JB` / `20JC`.

**Read off the machine 2026-08-05** — MTM **`20JCS0WR00`** · BIOS **`N1OET59W` 1.44 (2022-05-23)` ·
CPU **i5-7Y57 @ 1.2 GHz** · **8 GB** · Secure Boot **off**.

| | |
|---|---|
| CPU | **i5-7Y57** — Kaby Lake Y-series, 4.5 W, fanless ✅ confirmed |
| RAM | **8 GB** LPDDR3, **soldered** — not upgradable ✅ confirmed |
| Storage | **NVMe SSD** (M.2 2242), not eMMC — fast install, no space crawl |
| Wi-Fi | Intel Wireless-AC 8265 — **works out of the box**, firmware ships in the Debian 13 installer |
| WWAN | **Sierra EM7455 LTE — WORKING 2026-08-22.** Ships FCC-locked; needs one symlink. See **LTE IS WORKING** below |
| Firmware | **64-bit UEFI** — the 32-bit-EFI trap that kills Debian on cheap Atom tablets does not apply |
| Keyboard | detachable folio over pogo pins — **does not consume a USB port** |

This is one of the better-supported Linux machines Lenovo ever shipped. Nothing here is a gamble.

### 🛑 WRONG — RETRACTED 2026-08-22. There is no second tablet.

*The section below claimed this X1 was a spare and that a separate Win 10 Lenovo was the till.
**Both are the same machine.** Felix handed over this X1 running Windows 10 in German; Angel wiped
it on 2026-08-04. Angel, 2026-08-22: "the single tablet we have now." The distinguishing detail I
invented — "screen that does not detach" — was never read off any machine. The paragraph is kept
because a confident, repeated, unchecked claim is worth seeing.*

### ⚠️ ~~This is NOT the till tablet~~ — WRONG, see above

[`10-devices-and-roles.md`](10-devices-and-roles.md) says of the *other* tablet — the Win 10 Lenovo
with one USB-A port, screen that does not detach — that Windows **should be left alone** because it
works and Linux would hand the staff something new for no gain. That still stands. **Do not confuse
the two machines.** This X1 is a spare; wiping it costs the shop nothing.

---

## Ports — settled 2026-08-04, no hub needed

Angel read them off the machine: **1 × USB-C + 1 × USB-A.** (I had guessed USB-C only. Wrong —
believe the tablet, not the spec sheet.)

That is a clean three-way split with nothing left over:

| Port | Job |
|---|---|
| Folio pogo pins | keyboard — **does not use a USB port** |
| USB-A | scanner gun dongle — **already confirmed working** on this machine |
| USB-C | charger |

So during the install: **stick in USB-A, charger in USB-C, folio attached.** No hub, no adapter,
nothing to buy. The "one USB port is all it takes" line from doc 10 carries over intact.

### 🛑 The WiGig Dock (W123) Felix supplied does NOT work with this tablet — 2026-08-22

A square box with plenty of ports, and useless here. The **ThinkPad WiGig Dock W123** reaches the
machine **only over a 60 GHz 802.11ad radio** — there is no USB or wired host cable, just its own
power brick. It requires an Intel Tri-Band Wireless-AC **18260/17265** card.

```
lspci: 04:00.0 Network controller: Intel Corporation Wireless 8265 / 8275 [8086:24fd]
```

**The 8265 is 802.11ac, 2.4/5 GHz — no 60 GHz radio.** It is the only wireless device on the bus.
And even with the right card, Intel's WiGig docking needed the Windows-only *Intel Wireless Dock
Manager*; there is effectively no Linux support. Wrong radio **and** no driver.

> ⚠️ **BIOS listing a feature is not the machine having it.** `F1 → Security → I/O Port Access`
> shows a **WiGig** toggle set On. Lenovo ships one firmware across a model line and lists options
> for hardware that is not fitted. *Exactly the same trap as the camera switch reading On while the
> sensors cannot be powered.* **Believe `lspci`, not the BIOS menu.**

**What to get instead — CHF 25–40 USB-C dock or hub with Ethernet.** It buys three things at once:

- **Wired Ethernet**, which for a till that sits in one place beats Wi-Fi outright — no association
  drops, no roaming, and no "associated but the uplink is dead". That makes the order
  **Ethernet → Wi-Fi → LTE**, which is where a mobile backup belongs.
- **Several USB-A ports** — gun dongle *and* the USB webcam (see the camera section) at once,
  removing the port clash this section used to have to solve with Bluetooth.
- **Charging pass-through** on the same cable.

Ask Felix for a ThinkPad USB-C dock (`40A9`/`40AS` series) before buying — he has hardware lying
around, and those work natively on Debian. Note the *other* Lenovo square box, the **USB 3.0
Basic/Pro Dock**, is **DisplayLink**: Ethernet and the USB hub work out of the box, video needs a
proprietary driver. For a till that is fine — the dock's HDMI is not needed.

---

## 🔧 BUILD SHEET — doing this again on tablet #2

*Everything below this section is background and history. **This section is the procedure.** Work
top to bottom; the traps are inline where you hit them. Budget ~90 minutes.*

**Target fleet:** two X1 Tablets, two guns, everything on charge all day, the mobile as backup.

### 0 · Before you touch it

- [ ] Confirm with the owner **nothing on it needs saving** — device encryption means no recovery.
- [ ] Have ready: Debian **13 (trixie) amd64 netinst** stick, the folio, the charger, the gun, and
      **a piece of paper** for the password.
- [ ] No hub needed: folio = keyboard (pogo pins), **USB-A = stick**, **USB-C = charger**.

### 1 · Boot the installer

- [ ] **Restart**, not Shut down. Windows Fast Startup hibernates instead of powering off and skips
      straight past the boot menu.
- [ ] Tap **F12** at the ThinkPad logo → pick the USB stick. **Do not edit the boot order** — F12 is
      a one-time menu, nothing to undo afterwards.
- [ ] Secure Boot can stay **on**; Debian's bootloader is signed. Only if the stick refuses to
      appear: `Security → Secure Boot → Disabled`, which also needs
      `Restart → OS Optimized Defaults → Disabled` first or it flips back.
- [ ] Installer finds no disk? Look for a storage controller set to `RST`/`RAID`; change to
      `AHCI`/`NVMe`. It is an explicit error, not a silent one.

### 2 · Installer answers

| Screen | Answer | Why |
|---|---|---|
| Language | **English** | also fixes the German-everything problem |
| Location | anything (Zurich may not be listed) | **timezone is fixed after install, do not fight it** |
| Keyboard | **match the letters printed on the folio keys** | this is what the **scanner gun** types into |
| Hostname | e.g. `banco-tablet-2` | shows up on the network and in CUPS |
| Domain | blank | |
| Root password | **LEAVE EMPTY** | supported path; wires the user into `sudo`. One password, not two |
| User | short, lowercase (`art`) | |
| User password | **lowercase letters + digits ONLY** | see the box below |
| Mirror country | **Switzerland** → `ftp.ch.debian.org` | **separate question from Location** — the default follows Location and will be slow |
| Partitioning | **Guided – use entire disk** | this is the point of no return |
| Encryption / LUKS | **NO** | see the box below |
| Software selection | ✅ Debian desktop environment · ✅ **GNOME** · ✅ standard system utilities · ✅ **SSH server** | uncheck Xfce/KDE/Cinnamon/MATE/LXDE/LXQt |
| GRUB | yes, to the internal disk | |

> 🔴 **The password rule — this cost us a whole reinstall.**
> **No `y`, no `z`, no symbols.** `y`/`z` swap between QWERTY and QWERTZ and every symbol moves, so
> the same keystrokes are a different string on a different layout — and a login screen cannot tell
> you which one you got wrong. Something like `banco1234`. **Write it on paper before typing it.**
> Set a proper password later from inside the desktop, where the layout is known.
> *Diagnostic if it happens anyway: type the password into the **username** field, where it renders
> in the clear, and see which characters the keyboard is actually producing.*

> 🔴 **Say NO to disk encryption.** The passphrase is typed at boot from the initramfs, which has
> **no on-screen keyboard**. On a tablet whose keyboard detaches, a lost or dead folio would mean a
> machine that cannot boot — a shop-can't-open failure, traded for theft protection on a device
> holding no customer data. Banco's data lives on the server.

> 💡 **Tick SSH server.** Missed on both of tonight's runs. It is the difference between driving the
> machine from the ProBook and typing every command on a touchscreen.

### 3 · First boot — the base

```bash
sudo timedatectl set-timezone Europe/Zurich
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y avahi-daemon avahi-utils cups chromium bluez-cups printer-driver-ptouch
sudo systemctl enable --now avahi-daemon cups
sudo usermod -aG lpadmin $USER          # log out and back in for this to take effect
```

> ⏰ **The timezone that looks right until October.** South Africa (or any UTC+2) agrees with
> Switzerland *all summer* and goes an hour wrong at the end of October — silently putting every
> shift time and receipt out. Run the `timedatectl` line even if the clock looks correct.

> 💡 `lpinfo`, `lpadmin`, `rfkill` live in `/usr/sbin`, which is **not** in a normal user's `PATH` on
> Debian. *command not found* on any of them means you need `sudo`, not a missing package.

### 4 · Printer — USB fallback first, then Bluetooth

**Always build the USB queue first.** It gives you a known-good fallback to compare against if the
Bluetooth attempt misbehaves.

```bash
# cable plugged in
sudo lpinfo -v                                    # expect an ipp:// Brother line via ipp-usb
sudo lpadmin -p QL820USB -E -v ipp://localhost:60000/ipp/print -m everywhere
lpstat -v
lp -d QL820USB /usr/share/cups/data/testprint
```

Then Bluetooth — **this is what frees USB-A for the gun**, and it is the whole reason the machine
works as a till:

```bash
# Bluetooth ON + discoverable in the printer's own LCD menu FIRST — it is off out of the box
bluetoothctl devices                              # note the QL's MAC
bluetoothctl trust AA:BB:CC:DD:EE:FF
sudo lpadmin -p QL820BT -E -v "bluetooth://AABBCCDDEEFF" \
     -m ptouch:0/ppd/ptouch-driver/Brother-QL-820NWB-ptouch-ql.ppd
# UNPLUG THE USB CABLE, then:
lp -d QL820BT /usr/share/cups/data/testprint
```

- **Unplug the cable before testing Bluetooth.** With it in, a label proves nothing about which path
  carried it.
- `bluez-cups` only exposes a `bluetooth://` device once the printer is **paired** — an unpaired
  printer looks exactly like a broken backend.
- **Do not pick the driverless/`everywhere` option for the Bluetooth queue** (Bluetooth cannot carry
  IPP) and **do not pick a Brother PPD for the USB queue**. Each transport gets its own driver.
- First job after wake takes **25–30 s** (roll calibration); later ones ~4 s. A slow first label is
  not a stuck queue.
- Queue shows *disabled*? That is a backend failure, not a driver failure — `cupsenable QL820BT`.
- Printing dies for no reason later: `sudo systemctl restart ipp-usb`. **Suspect the daemon before
  the hardware.**

> ### 🔴 The sleeping printer — found 2026-08-04, do BOTH of these on every build
>
> Real Banco labels print from Chromium ✅ (so the `@page` A4-fallback trap is not biting). But
> **take a one-minute break and the next label never comes out.** Everything looks right, the print
> dialog behaves, nothing happens.
>
> Two causes stacked on each other:
>
> **1. Something goes idle.** ~~Set Auto Power Off → Off in the QL's LCD menu.~~ **There is no such
> setting on this printer's panel** — Angel looked, 2026-08-04. Brother exposes it only through
> their Printer Setting Tool, which is Windows/Mac, so it cannot be changed from Linux at all. Left
> on mains the printer stays lit and green, which points at the **Bluetooth link going idle rather
> than the printer sleeping**. Either way the fix is the same and it is fix 2.
>
> **2. CUPS disables the queue after one failure.** Default `printer-error-policy` is
> `stop-printer` — one failed job disables the whole queue and **every job after it is silently
> swallowed.** That is what "I selected everything right and it didn't print" actually is.
>
> ```bash
> sudo lpadmin -p QL820BT -o printer-error-policy=retry-job
> ```
>
> `retry-job` holds the job and retries instead. A cashier should never need to know what
> `cupsenable` is.
>
> **Recovery when it has already happened:** `lpstat -p QL820BT` (look for *disabled*), then
> `cancel -a` and `cupsenable QL820BT`.
>
> **Tell the two apart — they look identical from the front:**
> - ~25–30 s then a label → **normal**, roll calibration on the first job after any wake. Do not
>   cancel it.
> - Nothing ever, and `lpstat -p` says *disabled* → the stuck queue above.
>
> ### ⚠️ Power-cycling the PRINTER does not clear a disabled QUEUE
>
> The obvious recovery — switch the labeller off and on — fixes the printer side and **does nothing
> to CUPS**. The disabled queue lives on the tablet. Power-cycle a printer whose queue CUPS has
> stopped and it still will not print, which reads as "the printer is broken" when it is not.
>
> **`retry-job` is what makes "just turn it off and on again" a valid recovery**, because CUPS then
> never disables the queue: the job sits held, the printer comes back, it prints. Without that
> setting the honest recovery is two steps and one of them is a terminal command:
>
> ```bash
> cancel -a && sudo cupsenable QL820BT
> ```
>
> **`cupsenable` needs `sudo`** — it lives in `/usr/sbin`, same as `lpinfo`, `lpadmin` and `rfkill`.
> Without it you get *command not found*, which reads like a missing package and is not.
>
> Set `retry-job` and the printer's own power button becomes the whole procedure — which is the only
> version a cashier can be expected to run.
>
> **✅ Verified 2026-08-04.** With `retry-job` set, a label printed straight out of a genuinely
> asleep printer — blank LCD, green LED pulsing every 5 s, no wake-up first. That is the exact state
> that swallowed the job before.
>
> **Still to prove: the lunch-break gap.** Twenty minutes dead — no sales, no touch, tablet awake —
> then fire a label. A few minutes passing is not the same test as a real quiet hour in a shop.

### 5 · Make it a till, not a laptop

```bash
mkdir -p ~/.local/share/applications ~/.config/autostart
cat > ~/.local/share/applications/banco.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Banco
Exec=/usr/bin/chromium --kiosk --app=https://banco.wolfhold.app --noerrdialogs --disable-session-crashed-bubble
Icon=chromium
Terminal=false
Categories=Network;
EOF
cp ~/.local/share/applications/banco.desktop ~/.config/autostart/

gsettings set org.gnome.desktop.session idle-delay 900
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
```

- Activities → search "Banco" → right-click → **Pin to Dash**. (GNOME has no desktop icons.)
- Settings → Users → **Automatic Login** on — safe, the tablet holds nothing.
- **Rotation lock** in the top-right quick settings. Pick one orientation and lock it so it cannot
  spin while someone holds it over a shelf.
- **Blank the screen, never suspend on mains.** Suspend **drops the Bluetooth link to the printer**,
  so waking costs a reconnect on top of the 25–30 s calibration.

### 6 · Network — save both while nothing is broken

```bash
# connect to the shop Wi-Fi AND the phone hotspot once each, then:
nmcli connection show
nmcli connection modify "Shop-SSID"        connection.autoconnect-priority 10
nmcli connection modify "Phone Hotspot"    connection.autoconnect-priority 5

cat > ~/.local/share/applications/net-hotspot.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Switch to Hotspot
Exec=nmcli connection up "Phone Hotspot"
Icon=network-wireless
Terminal=false
EOF
cat > ~/.local/share/applications/net-wifi.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Switch to Shop WiFi
Exec=nmcli connection up "Shop-SSID"
Icon=network-wireless
Terminal=false
EOF
```

Pin both to the dash. **Do not expect the priorities to save you** — see the measured findings
below. Failover is a human action either way; the launchers just remove the picker and the password.

### 7 · Prove it — human-green, not machine-green

None of the above counts until a person confirms it:

- [ ] **`/pos/hardware` — scan a HYPHENATED test code.** Not a plain EAN: digits sit in the same
      place on every layout, so a numeric code passes happily and proves nothing.
- [ ] **Print a real Banco label from Chromium** and hold it against a shelf. The CUPS test page
      proves the *transport*; the browser is a different rendering path, and it is where the
      `@page { size: 62mm auto }` A4-fallback trap lives.
- [ ] **Gun and printer at the same time** — dongle/Bluetooth gun, printer on Bluetooth, charger on
      USB-C. Scan something and print its label in one go.
- [ ] **Reboot, then repeat all three with nothing re-paired and nothing re-typed.**
- [ ] Detach the folio and confirm the on-screen keyboard appears.
- [ ] `free -h` — record 8 or 16 GB for this unit.
- [ ] BIOS via `fwupdmgr` (charger in, battery >30%) — see below.

---

## Before you wipe — four things, in order

1. ~~**Ask Felix what is on it.**~~ ✅ **Answered 2026-08-04: wipe it, nothing to save.** That was
   the only genuinely irreversible thing here — Windows 10 on a TPM machine usually has device
   encryption on, so nothing is recoverable after. Cleared.
2. **Do not worry about the Windows key.** It is burned into the firmware. If this ever needs to go
   back to Windows, it reactivates itself. Scrapping Windows is reversible.
3. **Let any running update finish.** Never pull power mid-update — that is the reliable way to turn
   a working tablet into a recovery loop you have to fight *before* you can wipe it.

### BIOS: do it AFTER, with `fwupd` — not from Windows

*Reversed 2026-08-04. The first draft said update the BIOS from Lenovo Vantage while Windows was
still there. With nothing to save, the reason to linger in Windows evaporated — and Vantage in
German, which typically wants to update itself first, is an hour-shaped detour in front of a job
that is otherwise ready to run.*

Lenovo publishes ThinkPad BIOS to **LVFS**, and `fwupd` installs from it. No Windows needed:

```bash
sudo fwupdmgr refresh
sudo fwupdmgr get-devices      # BIOS, Thunderbolt controller, SSD firmware
sudo fwupdmgr get-updates
sudo fwupdmgr update           # stages to the ESP, reboots into firmware update mode
```

Charger plugged in and battery above ~30%, or Lenovo's firmware refuses. A 2017 machine that has
been sitting is likely several versions behind — worth doing for Kaby Lake microcode and USB-C
fixes — but it is a next-week job, not a blocker.

---

## Making the stick

Grab the current **Debian 13 (trixie) amd64 netinst** from `debian.org`. Since Debian 12 the
non-free Wi-Fi firmware is included in the official image — there is no separate "unofficial
firmware" image to hunt for any more, and the AC 8265 is covered.

Write it with `dd` on the ProBook:

```bash
lsblk                              # find the stick — get this right
sudo dd if=debian-13.x.0-amd64-netinst.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

---

## Firmware settings

**Getting in** — from Windows, so the German menus are only in your way once:

> Einstellungen → Update und Sicherheit → Wiederherstellung → *Erweiterter Start* →
> **Jetzt neu starten** → Problembehandlung → Erweiterte Optionen → **UEFI-Firmwareeinstellungen**

After the wipe, it is **F1** at the ThinkPad logo with the folio attached, or **F12** for a one-off
boot menu. ThinkPad firmware menus are in **English** regardless of the Windows language.

**What to change:**

- **Secure Boot — you can leave it ON.** Debian's bootloader is signed and boots fine under Secure
  Boot. Only if the stick refuses to appear should you go `Security → Secure Boot → Disabled`, and
  on ThinkPads that also needs `Restart → OS Optimized Defaults → Disabled` first or it flips back.
- **Boot order** — USB above the internal drive, or just use F12 each time.

**If the installer says it cannot find a disk:** look for a storage controller mode set to
`RST`/`RAID` and change it to `AHCI`/`NVMe`. Classic Lenovo trap. It will not be silent — you will
get an explicit "no disks found", so you will know.

---

## Install choices that actually matter

**Language: English.** This alone fixes the "it is all in German" problem you started with.

**⚠️ Keyboard layout — this is the trap.** The installer asks for a keyboard layout. Whatever you
pick here is what the **scanner gun** speaks to, because the gun types its barcode as keystrokes. A
gun emitting US scancodes into a Swiss-German layout produces the wrong characters and the scan
silently fails. See the layout trap in [`testsheets/Scanners/README.md`](testsheets/Scanners/README.md)
and **match this to the gun, not to the folio's printed keys.**

**Desktop: GNOME.** Not the usual "lighter is better" advice, and here is why: **you detach the
keyboard.** GNOME has the only genuinely usable on-screen keyboard and touch handling on Linux.
XFCE and LXQt are lighter and will leave you with a tablet you cannot type on. The i5 with 8 GB
runs GNOME comfortably.

**Disk: use the whole disk, wipe Windows.** That is the job.

---

## After the install — what Banco needs

The tablet is a **client**, not a host. It does not run the stack. It needs:

1. **Chromium**, pointed at the Banco address — kiosk mode once it settles.
2. **CUPS**, printing to the QL-820NWB **over Wi-Fi. Not Bluetooth, and not USB.** Doc 10's last
   open item is *"Networking the QL-820NWB over Wi-Fi would let any till print — it is a `NWB`, the
   hardware is already there."* This tablet is the reason to finally do it.

   > ### ✅ RESOLVED 2026-08-04 — Bluetooth works. The warning below was wrong.
   >
   > **`printer-driver-ptouch` 1.7.1 prints over Bluetooth on the QL-820NWB.** First try, a full
   > test page. The 07-28 verdict below was measured against **1.6**, and the blocker was fixed
   > upstream in the months since. Read the box below as history, not as advice.
   >
   > Working setup on `art@art`:
   >
   > ```bash
   > sudo apt install -y bluez-cups printer-driver-ptouch
   > bluetoothctl trust 3C:EF:A5:17:6F:82        # QL-820NWB2376
   > sudo lpadmin -p QL820BT -E -v "bluetooth://3CEFA5176F82" \
   >      -m ptouch:0/ppd/ptouch-driver/Brother-QL-820NWB-ptouch-ql.ppd
   > ```
   >
   > Bluetooth must be switched **on and discoverable in the printer's own LCD menu** first — it is
   > off out of the box, and `bluez-cups` only exposes a `bluetooth://` device once the printer is
   > *paired*, so an unpaired printer looks exactly like a broken backend.
   >
   > **Why this matters more than one label:** the tablet has **one USB-A port and the scanner gun
   > needs it.** Bluetooth for the printer is what makes this machine a till at all.
   >
   > There is also a permanent USB fallback, `QL820USB`, on the driverless path — see below. Keep it.
   >
   > ### ⚠️ History — why we expected Bluetooth to fail
   >
   > On Windows the tablet found the QL over Bluetooth and even recognised the label — which reads
   > like the easy path. It is not, and the reason is already written down in the 2026-07-28
   > lessons.
   >
   > Bluetooth to a QL is **Serial Port Profile carrying raw Brother raster**. That is the exact
   > path where `printer-driver-ptouch`, `brother_ql` and `brother_ql_next` printed **zero labels**
   > between them — every job rejected as "wrong roll type". The path that *did* produce paper was
   > generic CUPS **IPP / `everywhere`**, and IPP needs the network, not Bluetooth.
   >
   > Going Bluetooth here means volunteering for the three-hour hunt again, on a fresh OS, with no
   > known-good path to fall back to. Put the printer on Wi-Fi.

   Use the generic **IPP / `everywhere`** driver. And per the 2026-07-28 lesson: a clean `lpstat`
   proves nothing — the printer accepts data in ~3 s and rejects it *after*. The only proof is a
   human holding a label.

   > ### Wireless Direct is also a trap — and address the printer by NAME, not IP
   >
   > *Settled 2026-08-04. Angel has the Wi-Fi password but no admin access to the router — it is
   > the neighbour's — and reasoned that meant Wireless Direct.*
   >
   > **The password alone is enough to join the printer to the network.** Router admin is not
   > needed to put a client on Wi-Fi. Infrastructure mode is available.
   >
   > **Wireless Direct cannot work for a till.** It makes the printer its own access point, and the
   > tablet has one Wi-Fi radio — joining the printer's AP drops it off the network Banco lives on.
   > The whole till goes dark to print one label. (The LTE modem is a genuine exception: printer on
   > Wireless Direct, internet over WWAN. Needs a SIM. Fallback, not plan A.)
   >
   > **What router admin would buy is a DHCP reservation** — a fixed IP so a CUPS queue does not go
   > dead when the address moves. Do not chase it. Point CUPS at the **mDNS name** instead:
   >
   > ```
   > ipp://BRW<nodename>.local/ipp/print      # + apt install avahi-daemon
   > ```
   >
   > The name never changes, so DHCP can do what it likes. **And it survives the move**: this is
   > being set up at Angel's house, but the till runs in the shop — different router, different
   > subnet. Anything pinned to an IP tonight gets redone on site. The mDNS name does not.
3. **`/pos/hardware`** — scan a hyphenated test code on this machine before trusting it. Per doc 10,
   that check is per-machine, every time a gun moves. **Use a hyphenated code, not a plain EAN** —
   digits sit in the same place on every layout, so a numeric code passes happily and proves
   nothing. The hyphen is what exposes a layout mismatch. Same trap that cost the reinstall.

### Kiosk mode — make fullscreen a setting, not a habit

Chromium being fullscreen because someone pressed F11 is not the same as Chromium *launching*
fullscreen. For a till it has to be the second one.

```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/banco.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Banco
Exec=/usr/bin/chromium --kiosk --app=https://banco.wolfhold.app --noerrdialogs --disable-session-crashed-bubble
Icon=chromium
Terminal=false
Categories=Network;
EOF
```

Activities → search "Banco" → right-click → **Pin to Dash**. (GNOME has no desktop icons; the dash
is the equivalent.) To open it at boot, copy the same file into `~/.config/autostart/` and turn on
Settings → Users → **Automatic Login** — safe here, the tablet holds nothing.

`--kiosk` leaves no address bar and nothing for a cashier to wander into.
`--disable-session-crashed-bubble` suppresses the "restore pages?" banner that would otherwise sit
across the top of the till after every power cut.

**Three settings a till needs and a laptop does not:**

- Power → **Screen Blank: Never**, **Automatic Suspend: Off** on mains. A till that dims mid-sale is
  a till the cashier is fighting.
- **Rotation lock** (top-right quick settings). The X1 flips landscape↔portrait freely; pick one and
  lock it so it cannot spin while someone holds it over a shelf.
- Dim-on-battery turned down — it lives on the charger anyway.

---

## The actual sequence, once Windows finishes updating

No admin commands. No boot-order editing. The `msinfo32` / `mountvol` checks from the first pass are
**dead** — they existed to identify the machine and find the firmware bitness, and the model number
answered both.

1. ~~Let Windows settle~~ ✅ done — update finished 2026-08-04.
2. ~~Check with Felix~~ ✅ done — wipe it.
3. ~~BIOS update from Windows~~ — **dropped**, doing it with `fwupd` after. See above.
4. **Write the stick** on the ProBook — Debian 13 amd64 netinst. *Confirm what is actually on any
   stick you already have before trusting it; an old or 32-bit image is the classic wasted evening.*
5. Stick → **USB-A**. Charger → **USB-C**. Folio attached.
6. **Neu starten** — *Restart*, not *Shut down*. Windows Fast Startup (`Schnellstart`) makes a
   shutdown not a real shutdown, and a hibernated machine skips straight past the boot menu.
7. At the ThinkPad logo, **tap F12 repeatedly** → one-time boot menu → pick the USB stick.

> **F12 is the answer to "do we configure the boot sequence?" — you don't.** The one-time boot menu
> picks the stick for a single boot and changes nothing permanent. Nothing to set, nothing to undo
> afterwards, and no way to leave the machine preferring USB forever. Only bother with the boot
> order if F12 turns out to be disabled.

---

## What is genuinely likely to go wrong

Honestly, not much — ports and Wi-Fi and the gun are all confirmed working on this machine already.
In rough order of odds:

- **The label printer**, which is the one thing that did not work under Windows either. Wi-Fi + IPP,
  per the box above.
- **Screen rotation** may need a nudge. Cosmetic for a till that sits in a stand.
- **The LTE modem** needs ModemManager fiddling if you ever want it. You probably do not.
- Wi-Fi, touchscreen, audio, sleep, battery: expected to just work on this generation.

---

## What actually happened — 2026-08-04, and what it cost

The install ran twice. Everything hardware-related worked first time: F12 found the stick, the
AC 8265 joined Wi-Fi during setup, the NVMe was seen, no firmware trouble at all. **The reinstall
was caused entirely by a password nobody could type.**

### 🔴 The lesson: a password is only as portable as the KEYBOARD LAYOUT it was typed on

Angel set a simple password at install time and could not log in with it minutes later. Not a typo
— the same keystrokes produce different characters depending on the active layout:

- **`y` and `z` swap** between QWERTY (US) and QWERTZ (Swiss/German)
- **every symbol moves** — `-` `_` `/` `!` `@` `#` `?` are all in different places

This is the same trap as the scanner gun in
[`testsheets/Scanners/README.md`](testsheets/Scanners/README.md), and it is worse at a login prompt
because **the login screen tells you nothing** — wrong layout and wrong password fail identically.

**So, whenever a password will be typed before the desktop exists:**

- Use **lowercase letters and digits only. No `y`, no `z`, no symbols.** Ugly, and it works on every
  layout. Set a proper one later from inside the desktop, where the layout is known.
- **Write it on paper before typing it.** Not on the machine you are about to lock yourself out of.
- **Leave the root password EMPTY.** That is the supported path — the installer wires the user into
  `sudo` instead. One password to get wrong instead of two.
- Diagnostic if it happens anyway: **type the password into the *username* field**, where it is
  displayed in the clear. That shows you which characters the keyboard is actually producing.

### The recovery path, for next time

A lost password never needs a reinstall on an unencrypted disk. Attach the folio (GRUB has no
on-screen keyboard), tap `Esc` during boot for the menu, `e` to edit the Debian entry, change `ro`
to `rw`, append `init=/bin/bash`, Ctrl+X.

**Gotcha that stopped us:** that shell starts with almost no `PATH`, so `passwd` returns *command
not found*. Fix with `export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`, or
call `/usr/bin/passwd` directly.

**And the trap inside the trap:** that rescue shell uses the **US layout** no matter what the
installed system uses. A password typed perfectly there can fail at the GNOME login screen and put
you straight back in GRUB. Same rule applies — letters and digits only.

We abandoned this anyway, and that was the right call: a fresh machine with nothing on it, a 6-point
console, and a touchscreen. **Reinstalling an empty machine beats debugging one.** The recovery path
is worth knowing for a machine that has something on it.

### Smaller things worth remembering

- **`Debian desktop environment` is an umbrella, not a competing choice.** Keep it checked *and*
  GNOME beneath it. Only the siblings — Xfce, KDE, Cinnamon, MATE, LXDE, LXQt — get unchecked.
- **Tick `SSH server` in the tasksel list.** Missed on both runs. It is the difference between
  driving the machine from the ProBook and typing commands on a touchscreen.
- **Location and mirror are separate questions.** Angel picked South Africa for location (Zurich was
  not offered), which makes the installer default to South African mirrors — slow from Switzerland.
  Scroll and pick Switzerland at the mirror screen regardless of the location answer.
- **The timezone that looks right until October.** South Africa is UTC+2 year-round; Switzerland is
  UTC+2 *in summer* and UTC+1 from the end of October. So it agrees perfectly today and silently
  puts every shift time and receipt an hour out later. One command, no reinstall:
  `sudo timedatectl set-timezone Europe/Zurich`.
- Username on the working install is **`art`**, root password empty, `sudo` via that user.

---

## When the Wi-Fi drops — decided 2026-08-04

Angel's flaky neighbour Wi-Fi died mid-test and gave us the failure mode for free. The offline
banner behaved correctly. Question raised: run all day on the shop mobile hotspot with shop Wi-Fi
as backup, or the reverse?

**Shop Wi-Fi primary, hotspot as backup — Angel's instinct, and it is right.**

- The phone **has a job already**: doc 10 makes it the emergency backup *and the camera*, the only
  one of the three machines that can photograph a packet. A phone that has been a hotspot since 9am
  is flat when someone needs it.
- Data cost is real for a POS pulling product images all day.
- Hotspots are flaky too — thermal throttling, and they leave when the phone walks to the stockroom.
- Mobile coverage inside a shop (concrete, basement) is often worse than the guess.

**The weak point is the procedure, not the choice.** "Grab the mobile and turn on the hotspot" puts
a network picker and a typed password in front of a cashier with a customer waiting — nowhere near
doc 10's *2 seconds, or it is broken*.

**Fix: pre-save the hotspot while nothing is broken, and set priorities.**

```bash
nmcli connection show
nmcli connection modify "<shop-wifi>"     connection.autoconnect-priority 10
nmcli connection modify "<phone-hotspot>" connection.autoconnect-priority 5
```

Failover is then **one action, on the phone** — turn the hotspot on. The tablet moves by itself and
moves back when shop Wi-Fi returns. Nothing is done on the till.

### Measured 2026-08-04 — what the priorities actually buy you

Tested with Angel's Fairphone hotspot as primary (the one he controls) and the neighbour's Wi-Fi as
fallback. Two findings, both worth knowing before anyone relies on this:

**1. `autoconnect-priority` is a *choosing* rule, not a *leaving* rule.** NetworkManager fails over
on **link loss** — the AP physically disappearing. It does **not** fail over on **internet loss**.
Kill the hotspot and it moves in about **20 seconds**. Leave the AP up with dead internet behind it
and it sits there forever, because NM sees a healthy connection and never re-chooses.

> ⚠️ **That is the shop's likely failure.** Router up, internet down — exactly what the flaky
> neighbour Wi-Fi does. **No priority tuning will ever switch anything automatically in that case.**
> A human has to act. Plan for it rather than trusting the failover.

**2. It does not switch back.** Once on the fallback, NM stays there even after the primary returns
— same reason: it has a working connection and does not care that a better one exists. Coming home
is manual too. **This is why there are two launchers, not one.**

### One tap each way — the launchers

Since a human triggers it regardless, remove the network picker rather than the human:

```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/net-hotspot.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Switch to Hotspot
Exec=nmcli connection up "Fairphone Hotspot"
Icon=network-wireless
Terminal=false
EOF
cat > ~/.local/share/applications/net-wifi.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Switch to Shop WiFi
Exec=nmcli connection up "Shop-SSID"
Icon=network-wireless
Terminal=false
EOF
```

Names must match `nmcli connection show` exactly, quotes included. Pin both to the dash.

Outage procedure becomes: turn on the phone hotspot, tap **Switch to Hotspot**. Tap **Switch to Shop
WiFi** when it is back. No settings, no picker, no password, nothing typed.

### 📶 The LTE modem — the best answer available, and it is already fitted

*Corrected 2026-08-04. An earlier note here said the LTE modem "has the same blind spot" as the
hotspot. Half right, and the wrong half matters.*

**The tablet has a WWAN modem and a nano-SIM slot, confirmed.** The proof was in hand from the
first hour: **the IMEI on the sticker.** An IMEI is a modem's identity — a machine without one does
not have an IMEI to print. The nano-SIM tray sits with the microSD **under the kickstand** on the
back.

Settle it on the machine rather than hunting for the slot:

```bash
sudo apt install -y modemmanager
mmcli -L
nmcli device          # a device of type `gsm` = modem present and NetworkManager can drive it
```

**What LTE does not do:** switch by itself when the router is up and the internet behind it is dead.
Same as the hotspot — NetworkManager will not leave a working link. That limit is real and applies
to every option.

**What LTE does, and the hotspot cannot:** give a genuinely independent path to the internet **with
no phone involved.** No hotspot to enable, no second device's battery to burn, no shop phone that
walked off in someone's pocket. Add a third launcher beside the other two and the entire outage
procedure is **one tap, on the tablet itself**:

```bash
cat > ~/.local/share/applications/net-mobile.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Switch to Mobile
Exec=nmcli connection up "Mobile Data"
Icon=network-cellular
Terminal=false
EOF
```

**And it compounds with the second tablet.** Two tablets, each with its own SIM, is *two independent
internet paths sitting on the counter* — not two copies of the same single point of failure. A gun
each, a data path each. A till doesn't move much data; a pair of cheap Swiss data-only SIMs only
have to earn their keep on the days the Wi-Fi is out.

> **Provenance, worth knowing for tablet #2:** Felix picked this specific unit to hand over, and
> Angel's read is that he knew it had the WWAN feature. He has connections and more units like it —
> so the second tablet most likely comes from the same source, same spec, and this build sheet
> applies unchanged.

> **The thing none of this solves.** Banco lives at `banco.wolfhold.app`, in a data centre. **No
> internet means no selling**, whatever happens with Wi-Fi — a hotspot buys a second path to the
> same remote server, not independence from it. A Banco running *in the shop* would keep selling
> through a WAN outage. That cuts against the "own it outright" premise and is worth a real
> decision someday; noted here, not scheduled.

### 📶 LTE IS WORKING — 2026-08-22 · and the whole problem was **one line in a log**

*The plan above was written 2026-08-04 and is unchanged and correct. This is the build: Felix's
nano-SIM in the slot, Debian 13, `banco.wolfhold.app` loading with Wi-Fi switched off.*

**Human-green — Angel, 2026-08-22:** *"i turned off wifi and i can still run banco on the web."*

> ⚠️ **Proved at Angel's flat, NOT in the shop.** The Wi-Fi in this test was **`Init7_1A34`**
> (home). Luzern has a different SSID, different concrete, and — the part that actually matters —
> possibly different LTE coverage. **Everything below has to be re-run on the counter.** See
> *"What to redo in Luzern"* at the end of this section.

#### What the machine is

| | |
|---|---|
| Modem | **Sierra Wireless EM7455**, USB `1199:9079`, firmware `SWI9X30C_02.33.03.00` |
| Driver | `cdc_mbim` — MBIM, QMI-capable. Loads by itself, no firmware package needed |
| SIM | Sunrise — `operator id 22802`, so the APN is **`internet`** |
| APN | `internet` (Sunrise/Salt). Swisscom + its resellers use `gprs.swisscom.ch` |

Nothing had to be installed for the hardware. `modemmanager`, `libqmi-utils` and `libmbim-utils`
were already present on Debian 13.

#### The actual blocker: the modem ships **FCC-locked**

Qualcomm-based Sierra modems come up after **every power cycle** with the radio disabled and
refuse to turn it on until the host sends a vendor unlock command. ModemManager knows how — but
since MM 1.18.4 the unlock scripts ship **disabled**, and Debian enables none of them. So MM tried,
found nothing, and reported a generic error.

What that looks like from the outside — three different lies, none of them the cause:

| What it said | What it actually meant |
|---|---|
| `nmcli`: `cdc-wdm0  gsm  unavailable` | nothing |
| `mmcli`: `state: failed / sim-missing` | the radio is off, so the slot was never energised |
| `mmcli -m any -e`: `Core.Retry: Invalid transition` | the modem refused `RadioState=on` |

Only `-G DEBUG` names it, and it names it exactly:

```
<<<<<<   RadioState = 'on'            MM asks
>>>>>>   status error = 'Failure'     the modem refuses
>>>>>>   HwRadioState = 'on'
>>>>>>   SwRadioState = 'off'         and stays off
[modem0] attempting FCC unlock...
[fcc unlock dispatcher] Cannot run fcc unlock operation from
  /usr/lib/x86_64-linux-gnu/ModemManager/fcc-unlock.d/1199:9079: file doesn't exist
```

#### 🔧 THE SEQUENCE — do this on tablet #2 and skip the whole afternoon

```bash
# 1 · WWAN radio is soft-blocked out of the box. Do this through NM, not rfkill alone —
#     NM persists it in /var/lib/NetworkManager/NetworkManager.state and re-asserts otherwise.
sudo rfkill unblock wwan
nmcli radio wwan on
sudo rfkill list wwan                 # must read: Soft blocked: no

# 2 · Enable the FCC-unlock script. THIS IS THE ONE THAT MATTERS.
sudo mkdir -p /etc/ModemManager/fcc-unlock.d
sudo ln -s /usr/share/ModemManager/fcc-unlock.available.d/1199 \
           /etc/ModemManager/fcc-unlock.d/1199
sudo ln -s /usr/share/ModemManager/fcc-unlock.available.d/1199:9079 \
           /etc/ModemManager/fcc-unlock.d/1199:9079
sudo systemctl restart ModemManager

# 3 · Confirm. Want: registered / on / attached.
mmcli -m any | grep -E 'state:|power state:'

# 4 · Ask the SIM which network it is on — do not guess the APN.
mmcli -i 0                            # operator id: 22801 Swisscom · 22802 Sunrise · 22803 Salt

# 5 · The connection. ifname '*' on purpose — see the trap below.
nmcli con add type gsm ifname '*' con-name shop-lte apn internet
nmcli con mod shop-lte connection.autoconnect yes
nmcli con mod shop-lte ipv6.method ignore
nmcli con mod shop-lte   ipv4.route-metric 700
nmcli con mod "<shop-wifi>" ipv4.route-metric 100
nmcli con up "<shop-wifi>"            # metric only applies on reconnect
nmcli con up shop-lte
```

Both links then stay up and the **route metric** decides which carries traffic — failover is
instant, with no reconnect and no tap. This supersedes the third launcher sketched above: the
launcher is still worth keeping as a manual override, but nobody has to press it.

#### Traps, each one paid for

- **`cdc-wdm0` became `cdc-wdm2` across a reboot.** The port name is *not* stable. A profile
  pinned to `ifname cdc-wdm0` works until the boot where it doesn't. Use `ifname '*'`.
- **`sim-missing` while the radio is blocked means nothing.** Re-seating the card proves nothing
  until `rfkill` reads `Soft blocked: no` and `power state: on`. Two of those re-seats were wasted.
- **`Busy`, repeatedly, on first connect.** Three bearers racing — `nmcli con up` run by hand while
  NM's own autoconnect was also trying. It is self-inflicted and it clears. NM succeeded on its own
  retry **five minutes later**. Do not keep hammering `con up`.
- **`retrieving IP configuration failed: modem IP method unsupported`** is the IPv6 half; the
  bearer is IPv4-only. `ipv6.method ignore` silences it. The connection activates either way.
- **`mmcli -s` is SMS. The SIM is `mmcli -i`.**
- **`journalctl` shows nothing without `sudo`** unless the user is in `adm`/`systemd-journal`.
- **A manual `qmicli --dms-set-fcc-authentication` survives until the modem loses power.** So does
  everything you test afterwards. `systemctl restart ModemManager` does **not** power-cycle it —
  which means *a restart proves nothing about the symlink.* Only a cold boot does.

Manual one-shot, for proving the diagnosis before wiring the symlink in (needs the proxy, because
ModemManager holds the port):

```bash
sudo qmicli -d /dev/cdc-wdm2 --device-open-mbim --device-open-proxy --dms-set-fcc-authentication
```

#### ⬜ What to redo in Luzern — this is not done until these are ticked

- [x] ~~**Cold boot**~~ — ✅ **DONE 2026-08-22 20:24. The FCC symlink works.** Verified the
      mechanism, not just the outcome: ModemManager's log level was raised via a systemd drop-in
      (`ExecStart=/usr/sbin/ModemManager --log-level=DEBUG`) so the unlock would be *visible* on the
      next boot, then a real power cut — `systemctl poweroff`, mains unplugged.
      ```
      [modem0] attempting FCC unlock...
      [fcc unlock dispatcher] singleton created      ← found it and RAN it
      ```
      Against the afternoon's `Cannot run fcc unlock operation … file doesn't exist`. Same boot:
      `cdc-wdm2  gsm  connected  shop-lte`, no intervention. Drop-in removed afterwards.
      **Nothing to redo here — this is machine behaviour, not shop behaviour.**
- [ ] **Set the shop Wi-Fi metric.** `ipv4.route-metric 100` was set on `Init7_1A34` (Angel's home
      AP). The shop profile is a different connection and starts at the default 600.
- [ ] **Check signal in the shop.** Home measured **29 %**. Concrete and a basement will be worse;
      the till needs a usable link where the till actually stands, not by the window.
- [ ] **Pull the Fritzbox WAN cable with the till open and ring a real sale.** Link-loss failover
      is what the metrics buy. It is not the same test as switching Wi-Fi off on the tablet.
- [ ] **Ask Felix what that SIM is.** Data-only, a spare voice line, or bundled with something —
      it connects identically and bills very differently. IMSI/ICCID are on the card; keep them off
      any forum post.

> **Still true, and no amount of LTE fixes it:** Banco lives at `banco.wolfhold.app`. LTE buys a
> second path to the same remote server, not independence from it. See the note above.

---

**Sleep settings, same session:** blank the screen, never suspend. **Suspend drops the Bluetooth
link to the printer**, so waking costs a reconnect on top of the QL's 25–30 s calibration. Screen
blank costs nothing and wakes instantly.

```bash
gsettings set org.gnome.desktop.session idle-delay 900        # 15 min
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
```

---

## 📷 The camera — read this before debugging it

*Opened 2026-08-05. Angel wants snap-and-fill and EAN capture on the tablet, not the phone: Felix
wants tablets, training happens on tablets, and the screen is **six times** the phone's. Doc 10's
line "the tablet has no camera" is about the **old Win 10 tablet** — the X1 has a front camera, a
rear camera and an IR sensor for Windows Hello. The glass you can see may be any of the three.*

**Symptom:** GNOME **Snapshot** (`gnome-snapshot 48.0.1-1`, already installed) reports *no cameras
found*.

> ✅ **RESOLVED 2026-08-22 — a USB webcam, and it works.** Angel plugged one into the USB-A port:
> *"i just plugged it in and it just works"*, and after one code fix (below) **the 📷 Webcam button
> is live on the tablet and capturing.** The internal cameras remain dead; they are not needed.
>
> ⚠️ **The webcam working was NOT the same as Banco working.** `posIsTouchDevice()` treated any
> touchscreen as a phone, so on this tablet the 📷 Webcam button was **hidden** and ✨ Snap & fill
> fell through to a file picker — on the one machine in the shop that had just grown a camera.
> Fixed in `4206246`: the axis is the OS, not the glass. `scripts/prove-webcam-button-shows.js`.
>
> 🛑 **The internal cameras: settled on kernel `6.12.101` — do not debug them.** Two real
> sensors (OV2740 + OV5670) are fitted and enabled; the TPS68470 camera PMIC that powers **both**
> has no board data for this model, so Linux cannot switch them on. Fixing it is a kernel patch.
> The one-line re-check after a kernel jump is at the end of *RE-MEASURED 2026-08-22*.

### ✅ Ruled out first — BIOS. Everything is ON.

Read off the machine 2026-08-05, `F1` → `Security` → `I/O Port Access`:

| Setting | State |
|---|---|
| Integrated camera | **On** ✅ |
| Microphone | On |
| Wireless LAN · Wireless WAN · Bluetooth | On |
| USB port · Memory card slot | On |
| Fingerprint reader · WiGig | On |

**Check this before touching a single package.** A ThinkPad can disable the camera at the hardware
level, and Linux then correctly reports no camera — no driver work will ever fix it. Corporate fleets
often ship this way.

### The diagnostic that decides everything

```bash
{ echo "== video devices =="; ls -l /dev/video* 2>&1
  echo "== USB =="; lsusb
  echo "== PCI imaging =="; lspci -nn | grep -iE 'imaging|multimedia|camera'
  echo "== modules =="; lsmod | grep -iE 'uvc|ipu|ov[0-9]|videodev'
  echo "== kernel messages =="; sudo dmesg | grep -iE 'ipu|uvc|camera|ov[0-9]{4}|cio2' | tail -20
  echo "== kernel =="; uname -r; } 2>&1 | tee ~/cam.txt
```

| What comes back | What it is | Effort |
|---|---|---|
| `/dev/video0` exists | app or permissions | minutes |
| `lsusb` shows a camera, no `/dev/video` | UVC module | minutes |
| `lspci` shows an **Imaging Unit**, USB shows nothing | **Intel IPU3** | an afternoon — `libcamera` + software ISP, and Chromium must be told to use it |

### ⚠️ SUPERSEDED — the 2026-08-05 measurement, kept because it was WRONG

*What was recorded on 2026-08-05, on the kernel of the day:*

```
lspci | grep -i imaging     → Imaging Unit           (IPU3 present)
dmesg | grep -iE 'int3472|ov[0-9]{4}|cio2'
                            → no sensor named, no int3472
```

> **The kernel sees the imaging unit on the PCI bus and nothing attached to the other end.**

**That conclusion was wrong, and the way it was wrong is the lesson.** It inferred *absent hardware*
from *absent log lines* — which is equally what you see when the drivers never load. Nobody asked
ACPI. The note did at least date itself and say "re-check after a major kernel jump", which is why
it got re-opened rather than believed.

### 🛑 RE-MEASURED 2026-08-22 · kernel `6.12.101+deb13-amd64` — a dead end, but a DIFFERENT one

The drivers are all present and loaded now — `ipu3_cio2`, `ipu3_imgu`, `ipu_bridge`, `ov2740`,
`intel_skl_int3472_{discrete,tps68470,common}` — and `/dev/video0…13` + `/dev/media0,1` exist. The
kernel even announces a camera:

```
ipu3-cio2 0000:00:14.3: Found supported sensor INT3474:01
ipu3-cio2 0000:00:14.3: Connected 1 cameras
```

**There is real hardware here.** Exactly three camera ACPI devices report present (`status=15`):

| ACPI id | What it is | Bound? |
|---|---|---|
| `INT3472:05` | **TPS68470** camera PMIC | bound — **and then failed** |
| `INT3474:01` | **OV2740** image sensor | unbound |
| `INT3477:00` | **OV5670** image sensor | unbound |
| `INT33BE:00/01`, `INT3470`, `INT3471`, `INT3472:00–04,06–08`, `INT3474:00` | declared but `status=0` | not fitted |

And the single line that ends it:

```
int3472-tps68470 i2c-INT3472:05: TPS68470 REVID: 0x21
int3472-tps68470 i2c-INT3472:05: error -ENODEV: No board-data found for this model
```

**Both fitted sensors are powered by that one PMIC, and no other power provider is present.** With
the PMIC unconfigured, the sensors' regulators/clocks/GPIOs never come up, so their I²C clients are
never instantiated — `/sys/bus/i2c/devices/` has no `i2c-INT3474:01` — so no sensor subdev appears
in the media graph, so `libcamera` finds nothing:

```
media-ctl -p -d /dev/media0    → only ipu3-csi2 0-3 and ipu3-cio2 0-3. No sensor entity.
cam -l                         → "Available cameras:"  (empty)
```

**Why no amount of userspace work fixes this.** `tps68470_board_data.c` is a **DMI-matched table
compiled into the kernel** giving each specific machine's GPIO / regulator / clock mapping. The
ThinkPad X1 Tablet Gen 2 is not in it. The fix is a kernel patch, carried and rebuilt at every
kernel update, on a machine a shop depends on. **No.**

> **The re-check rule, updated.** Do not re-run the *driver* hunt — drivers are fine. The single
> thing to re-test after a kernel jump is one line:
> ```bash
> sudo dmesg | grep -i tps68470
> ```
> If `No board-data found for this model` is gone, board data landed upstream and the cameras may
> come up on their own. If it is still there, nothing has changed. **That is a ten-second check;
> everything else in this section is settled.**

### ✅ The answer instead: a USB webcam

**CHF ~20, works instantly, zero driver work**, and Chromium sees it as an ordinary camera.

Two reasons it is genuinely better rather than a consolation prize:

- **The gun already scans EANs far better than any camera** — faster, fine in bad light, no focus
  hunting. So the camera's only real job is **photographing packets**, not scanning.
- Doc 10 already names the ProBook as the **photo booth**. A webcam on a stand is a *better* photo
  booth than a tablet held at an angle over a packet.

**Until it arrives:** gun for EANs, phone for photos. Nothing is blocked — snap-and-fill is a
convenience, and file upload from disk works on the tablet today with no camera at all.

#### ❌ Not Bluetooth — and the port problem has a free fix

**Bluetooth webcams are not a real category.** Bluetooth tops out around 2–3 Mbps in practice, video
needs far more, and there is no standard profile for it. Anything sold as one is Wi-Fi underneath or
badly compromised.

**The clip-on part is right though** — that *is* a normal USB webcam. Nearly all of them ship with a
hinged clip for the top edge of a laptop or monitor, and a tablet edge grips the same way.

**The port clash and its fix:** USB-A holds the gun's dongle. But **put the Inateck on Bluetooth** —
it is the gun that has it — and USB-A is free for the webcam, with the charger still on USB-C.
Everything runs at once and there is nothing extra to buy. (A USB-C hub with power pass-through also
works, but it is one more thing to carry and lose.)

> ⚠️ **Ergonomics, honestly.** A webcam clipped to the tablet means carrying a 12-inch screen *to*
> the packet at the right angle and distance — worse than a phone, which is already camera-shaped.
> Where the webcam genuinely wins is **fixed on a stand at the back office**: packet down, both hands
> free, consistent light and framing every time. **Realistic split — webcam on a stand for catalogue
> photos, phone for grab shots at the shelf, tablet for scanning and intake.**
>
> Third option if the lens matters: **the phone can act as the tablet's webcam** over USB or Wi-Fi,
> and it has the best sensor in the kit. More moving parts than a CHF 20 camera, so only worth it for
> photo quality.

> ⚠️ **Two things are being tested, not one.** GNOME seeing a camera and **Chromium** getting a frame
> are separate questions. Banco's 📷 snap-and-fill needs the browser to get it, and the page must be a
> **secure context** — HTTPS is fine, a bare `http://192.168…` is not. Finish by testing snap-and-fill
> on a real product, not by celebrating a picture in Snapshot.

---

## Idea parked 2026-08-04 — gun battery on `/pos/hardware`

The cheap Bluetooth gun **does** publish the standard BLE Battery Service; `upower -d` read it as
81% on the tablet. `upower -e` gives a stable device path for scripting, `upower -i <path>` the
level. `bluetoothctl info <MAC>` shows more (UUIDs, services) but `upower` is enough.

**The constraint that decides the design:** `/pos/hardware` is a web page in a browser sandbox. It
cannot run `upower` or see the host Bluetooth stack. Something on the tablet has to *tell* Banco.

- **A — small agent (preferred).** Shell script reading `upower -i`, systemd timer every few
  minutes, POSTs `{device, percent}` to a new endpoint. `/pos/hardware` shows last level + staleness.
  Works for any gun `upower` sees, same on the ProBook. Cost: endpoint, storage, per-machine install.
- **B — Web Bluetooth.** `navigator.bluetooth` reads the Battery Service with no agent, but needs a
  user gesture and device-picker every session and only sees BLE, not classic HID. Wrong for a till.
- **C — nearly free, do regardless.** `navigator.getBattery()` gives the **tablet's own** charge from
  JS, no agent, no prompt. Arguably the more important number: a flat till is worse than a flat gun,
  because the gun has a spare and the tablet does not.

**Value, honestly:** doc 10 already carries the real fix — two guns, one always on charge. The
reading only adds catching a gun at 15% *before* a shift instead of mid-sale. Nice, not urgent.
Not promoted to `WORKLIST.md`; item 3 (the bulk catalogue scripts on prod) is still next.

---

## Open items

- [x] ~~Read the port layout~~ — 1 × USB-C + 1 × USB-A, no hub needed (2026-08-04)
- [x] ~~Confirm 8 vs 16 GB RAM~~ — **8 GB**, MTM `20JCS0WR00`, i5-7Y57 (2026-08-05)
- [ ] **BIOS is 1.44, dated 2022-05-23** — over three years old. Check `fwupdmgr` for a newer one
- [x] ~~📷 **Camera**~~ — **closed 2026-08-22, kernel `6.12.101`.** Two sensors fitted (OV2740,
      OV5670); the TPS68470 PMIC that powers both has no board data for this model → kernel
      patch territory. **Buy the CHF 20 USB webcam.** Ten-second re-check after a kernel jump:
      `sudo dmesg | grep -i tps68470`
- [x] ~~📷 USB webcam~~ — **found one, plugged into USB-A, works.** Needed one code fix
      (`4206246`) because Banco hid the live-camera button on touchscreens. **Human-green on the
      tablet in Chromium over HTTPS, 2026-08-22:** *"the webcam button is there and it works"*
- [ ] 📷 A small stand for the back office — packet down, both hands free, consistent light
- [ ] Confirm with Felix that nothing on it needs saving
### 🔴 A GUN WITH A FLAT BATTERY LOOKS EXACTLY LIKE A SOFTWARE BUG

**2026-09-01, and it cost about twenty minutes.** The gun stopped scanning into Shelf Intake.
It had worked for days. Nothing in `shelf_intake.html` or `pos-scanner.js` had changed since
22 August, and a Playwright burst at 0ms delay — as fast as key events can be delivered, which
is what a gun is — landed cleanly in the box on the live build. The page was innocent.

**The gun was going flat.** The tell is a **double beep on scan and no red flash.** There is no
low-battery warning anywhere, and the failure is silent enough to read as "the screen is broken".
Angel found it by noticing the gun had *also* stopped working on New Sale — a screen that had
worked an hour before. **One symptom on two unrelated screens means the thing they share is what
changed.**

- **Charge it and re-test before debugging anything else.** Ten minutes is enough to tell.
- Angel's read, and it is the right one: *"the user just needs to know the gun is not scanning —
  plug it in and start charging."* That belongs on the shop's day-one card, not in a runbook
  nobody opens at the counter.
- ⚠️ Worth deciding: should `/pos/hardware` show **when Banco last saw a scan**? A screen that
  says "no scan in 3 minutes" turns a silent hardware failure into a visible one — and this is
  the second time a hardware fault has been read as a Banco fault (the camera, 2026-08-22).

- [ ] Decide the gun's keyboard layout *before* the installer asks
- [ ] Network the QL-820NWB over **Wi-Fi** so this machine can print at all
- [ ] Once it runs: update the device table in [`10-devices-and-roles.md`](10-devices-and-roles.md)
      — it currently describes three machines and this is a fourth
- [x] ~~LTE modem~~ — **working 2026-08-22**, Sunrise SIM, FCC-unlock symlink. Angel: *"i turned off
      wifi and i can still run banco on the web"*
- [ ] ⚠️ **Re-prove the LTE in Luzern** — the test above was at Angel's flat on `Init7_1A34`. Five
      items to redo on the counter, listed at the end of the LTE section. **Cold boot is the only
      test of the FCC symlink**; a `systemctl restart` proves nothing
