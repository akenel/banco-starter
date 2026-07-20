# 0 · Before you begin — is this machine ready?

**Do this before you clone anything.** Banco runs four programs at once (database, login system, image store,
the app itself), so the machine needs a bit of muscle and a few tools installed. Five minutes here saves you a
wasted afternoon.

## Minimum machine

| | Minimum | Comfortable |
|---|---|---|
| CPU | 2 cores | 4 cores |
| RAM | 8 GB total / ~4 GB free | 16 GB |
| Disk free | 10 GB | 20 GB+ |
| OS | Linux (Debian/Ubuntu), macOS, or Windows 10/11 with WSL2 | — |
| Internet | yes (to download the images) | — |

> 8 GB is the **floor**, not comfort. Keycloak (the login system) is a memory-hog. On 8 GB, close other apps and
> make sure you have swap. It works — it just won't be snappy. A real field test on a fresh 8 GB Debian 13 laptop
> ran fine (4.9 GB free + 7.9 GB swap).

## Step A · Check the machine (no tools needed yet)

You don't have this repo yet, so run this **paste-in** check in a terminal. It reads only — installs nothing:

```
nproc; free -h; df -h /; for t in docker git gpg curl python3 b2 node; do echo "== $t =="; $t --version 2>&1 | head -1; done; echo "== compose =="; docker compose version 2>&1 | head -1
```

> ⚠️ Paste it as **one line**. (Multi-line scripts with `||` in them can get mangled by copy-paste — a real gotcha
> we hit. One line, only `;` separators, is paste-proof.)

Read the results:
- **RAM available** and **disk free** — must clear the minimums above.
- Each tool prints a version (✅ have it) or `command not found` (❌ need to install it).

On a **fresh Debian/Ubuntu box, expect** `gpg` and `python3` to already be there, and `docker`, `git`, `curl`,
`b2` to be **missing**. That's normal — the next step installs them. (`node` is **not needed** — Banco's frontend
is pre-bundled.)

## Step B · Install the missing tools

### 🐧 Debian / Ubuntu

> ⚠️ **Debian gotcha:** on a fresh Debian install, your user is often **not a sudoer** (`sudo` says "user is not
> in the sudoers file"). Ubuntu adds you automatically; Debian doesn't. If `sudo` fails, become root first with
> `su -` (enter the **root** password you set at install), run the commands below **without** `sudo`, and add
> yourself to the groups — then it's fixed for good:
> ```bash
> su -                                  # enter root password; prompt becomes #
> apt update
> apt install -y sudo git curl docker.io docker-compose-v2
> systemctl enable --now docker
> usermod -aG sudo <your-username>      # so sudo works from now on
> usermod -aG docker <your-username>    # so docker runs without sudo
> exit                                  # back to your normal user
> ```
> Then **log out and back in** and skip to the test below.

If your user already has `sudo` (Ubuntu, or after the fix above):
```bash
sudo apt update
sudo apt install -y git curl docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

> ⚠️ **Docker plugin gotcha (Debian 13 "trixie") — you need TWO plugins.** `docker.io` ships **neither** the
> `docker compose` command **nor** `buildx` (which building the app image requires — you'll see
> *"compose build requires buildx 0.17.0 or later"*). Debian 13 also dropped the `docker-compose-v2` apt package.
> Install both official plugins directly (works on any distro). No root needed — user-level plugins:
> ```bash
> mkdir -p ~/.docker/cli-plugins
> # 1) compose v2
> curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
>      -o ~/.docker/cli-plugins/docker-compose && chmod +x ~/.docker/cli-plugins/docker-compose
> # 2) buildx (needed for `docker compose --build`)
> curl -SL https://github.com/docker/buildx/releases/download/v0.35.0/buildx-v0.35.0.linux-amd64 \
>      -o ~/.docker/cli-plugins/docker-buildx && chmod +x ~/.docker/cli-plugins/docker-buildx
> docker compose version   # v2.x
> docker buildx version     # v0.35.x (any ≥ 0.17)
> ```
> Don't use the old `docker-compose` (v1, with a hyphen) — Banco's scripts need `docker compose` (v2, a space).
> (Prefer everything bundled? Install from Docker's official repo — `docker-ce` includes compose + buildx —
> instead of Debian's `docker.io`.)

Then **log out and back in** (so you can run `docker` without `sudo`), and test:
```bash
docker run --rm hello-world
```
A friendly "Hello from Docker!" means you're ready.

### 🍎 macOS
Install **Docker Desktop** (docker.com) and **git** (`xcode-select --install`). Docker Desktop bundles compose.

### 🪟 Windows
Install **WSL2** + **Docker Desktop** (with WSL2 backend), then work inside your WSL Linux terminal and follow
the Debian steps above.

### `b2` (Backblaze CLI) — only for backups, install later
You don't need it to run Banco. When you reach [guide 6](06-own-your-data-backups.md), install it with `pipx`
(`sudo apt install -y pipx && pipx install b2`) — on Debian 13+, `pip install` is blocked system-wide, so use
pipx or a virtual environment.

## Step C · Confirm with the preflight script

Once you've installed the tools **and cloned the repo**, re-check with one command:
```bash
./scripts/preflight.sh
```
It gives a clear ✅ / ⚠️ / ❌ verdict. Green (or amber) → go to [QUICKSTART.md](../QUICKSTART.md). Red → it tells
you what's still missing.

---

### Reality check on timing
A prepared machine (Docker already installed) gets to a running Banco in an hour. **A fresh machine** — installing
Docker, learning the ropes — is realistically **half a day for step 0 alone**, and the whole real go-live (catalog,
staff, backups) is **2–4 weeks part-time**. That's normal for putting in a real till system. Don't let anyone tell
you it's a one-hour job — it isn't, unless you've done it before.
