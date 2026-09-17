# Go-Live checklist — don't open the doors until every box is green

Print this. Walk it top to bottom on the day before (or morning of) go-live. If any box can't be ticked,
you're not live yet. The order matters — safety net first.

## 🌐 Public shop? (if Banco is on the internet, not just your laptop)
- [ ] **HTTPS + a real domain are set up** ([guide 7](07-going-to-production.md)) — the localhost demo is plain HTTP and NOT safe to expose.
- [ ] **Keycloak is in production mode** (`start`, not `start-dev`) and its redirect URIs use your real domain.

## 🛟 Safety net (do these FIRST)
- [ ] **Backups are ON** — a scheduled encrypted backup runs automatically (see [guide 6](06-own-your-data-backups.md)).
- [ ] **Backups reach your own B2 bucket** — you've seen at least one backup file land in Backblaze.
- [ ] **You have practiced a restore** — pulled a backup back and watched the data return. (Don't trust a backup you've never restored.)
- [ ] **Your keys + passwords are saved** in a password manager ([worksheet](04-master-passwords.worksheet.md)) — NOT only in your head, NOT in this repo.

## 🏪 Identity & money
- [ ] Shop **name, address, VAT number** are correct ([guide 1](01-shop-profile.md)) — check them on a printed receipt.
- [ ] **Currency** is right ([guide 2](02-settings-currency-vat.md)) — prices show in your currency, not the demo default.
- [ ] **VAT rates** are right for your country — ring one item and check the tax line on the receipt.
- [ ] If you sell **food/coffee**: dine-in vs takeaway VAT behaves correctly.
- [ ] **Receipt footer** (thank-you line, legal text) reads the way you want.
- [ ] **Pay one sale in CASH and check the change**, on the screen, on the receipt and in the
      drawer — all three, same number. *Added 2026-09-10: the five-rappen rounding had never once
      run in a browser, and the checkout offered CHF 2.04 while the drawer and the receipt said
      2.05. Two thousand passing tests never saw it; one basket did.*
- [ ] **Print a receipt with the wifi OFF.** *Added 2026-09-07: the receipt fetched its QR image and
      its typeface from the internet AT PRINT TIME, so the one document a customer takes home broke
      exactly when the network did. Fixed — and this is how you know it stayed fixed.*

## 👥 People
- [ ] Every real staff member has their **own login** with the **right role** ([guide 3](03-users-and-roles.md)).
- [ ] The **demo users** (pam, ralph, michael, felix) are disabled or their passwords changed.
- [ ] **Master/admin passwords have been changed** from the starter defaults (the `.env` and Keycloak admin).
- [ ] Each cashier has done a **practice sale, a cash payment, and a return** — for real, on the till.
- [ ] The manager knows where the **daily report** and the **🕵️ audit log** live.

## 📦 Catalog
- [ ] Your **top sellers are in** with correct **prices** and **VAT category** ([guide 5](05-catalog-loading.md)).
- [ ] **Age-restricted items** (tobacco / alcohol / 18+) are flagged.
- [ ] A **barcode scan** of a real product finds the right item (if you use a scanner).
- [ ] The **demo/sample products** are cleared out (no leftover "Artemis" demo catalog).
- [ ] **Nothing is stuck on the placeholder price.** `/pos/cleanup` → **The Bench** → 🚫 **Can't be
      sold**. Every row in that list is a product on your shelf that the till will **refuse in front
      of a customer**. Either price them now, or make sure every cashier knows the move
      ([guide 11](11-cashier-shift.md) C3b — she can set it once). *A count of zero is not required.
      Knowing the number is.*

## 🖥️ Hardware & money handling (if you use them)
- [ ] **Receipt printer** prints a clean receipt.
- [ ] **Barcode scanner** reads into the search box.
- [ ] **Card / TWINT terminal** is set up and a test payment went through.
- [ ] **Cash drawer / float** — the opening cash amount is entered.

### 🔴 The one that is not on any vendor's checklist — **cold-boot the till and WATCH IT**

- [ ] **Power the till right off, turn it on, and stand in front of the screen with a watch.**
      Not a reboot over SSH — *the screen*. Time how long until a cashier could ring a sale.
      *Added 2026-09-05, and it is the most expensive thing on this page: on a cold boot the till
      came up to a **white window with no page for thirteen minutes**, while `systemctl` said
      `active (running)` and the machine's own `curl` answered **200 in 86 ms**. Autologin left the
      login keyring locked, Chromium blocked on it and never navigated. Four months of boot proofs
      missed it because every one was a reboot over SSH with nobody looking.* Fixed
      (`--password-store=basic` in `banco-till.service`) — this box is how you know it is still fixed
      on YOUR machine.
- [ ] **Do it a second time with the wifi router off**, and know what the cashier sees.

## ✅ Final proof
- [ ] **`python3 scripts/banco-doctor.py` shows 0 blockers** (❌) — the automated version of this whole list.
- [ ] Run the [**Own Your Banco testsheet**](testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html) end-to-end — all green.
- [ ] Do **one full real sale** with a real product, real price, real payment — and refund it.
- [ ] Note **who to call** if something breaks on day one (yourself? your IT person? a support tier?).

---

### The three that actually matter
If you only verify three things before opening: **(1)** a backup ran and you restored it, **(2)** a real sale
rings up with the correct price and VAT — **paid in cash, with the change checked against the drawer** —
and **(3)** your staff can log in and sell **on a machine you have watched boot from cold**. Everything
else you can fix while open. Those three you cannot.

> **Why the additions on this page all look oddly specific:** every one of them was found by a person
> standing at a counter, and *none* of them could be found by a test. They are here in the shape they
> bit in. Add yours the same way.

**Signed off by:** ______________________  **Date:** __________  **Shop:** ______________________
