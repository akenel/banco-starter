# Go-Live checklist — don't open the doors until every box is green

Print this. Walk it top to bottom on the day before (or morning of) go-live. If any box can't be ticked,
you're not live yet. The order matters — safety net first.

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

## 🖥️ Hardware & money handling (if you use them)
- [ ] **Receipt printer** prints a clean receipt.
- [ ] **Barcode scanner** reads into the search box.
- [ ] **Card / TWINT terminal** is set up and a test payment went through.
- [ ] **Cash drawer / float** — the opening cash amount is entered.

## ✅ Final proof
- [ ] Run the [**Own Your Banco testsheet**](testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html) end-to-end — all green.
- [ ] Do **one full real sale** with a real product, real price, real payment — and refund it.
- [ ] Note **who to call** if something breaks on day one (yourself? your IT person? a support tier?).

---

### The three that actually matter
If you only verify three things before opening: **(1)** a backup ran and you restored it, **(2)** a real sale
rings up with the correct price and VAT, **(3)** your staff can log in and sell. Everything else you can fix
while open. Those three you cannot.

**Signed off by:** ______________________  **Date:** __________  **Shop:** ______________________
