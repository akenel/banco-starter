// Keep the till maximised, on Wayland, where nothing outside the compositor can.
//
// WHY THIS EXISTS. Layla, 2026-09-04 21:29: a strip of the till and a field of desktop
// wallpaper. "i will reboot to resolve this issue — only thing a cashier could do."
//
// The cause is narrower than it was written up as, and the narrowing matters: the
// fullscreen toggle shipped 2026-09-02 17:51 and --kiosk was backed out that same
// evening, so her report is from the maximised build WITH the toggle. Kiosk does not
// explain it and the toggle does not fix it. What is left is simply that a title bar is
// a drag handle, and a touchscreen has no way to shove a window back once its edge is
// past the glass.
//
// IT SNAPS BACK, IT DOES NOT REFUSE. Cancelling the grab would be fewer lines and it
// would make the screen feel broken — a cashier pushing something that will not move
// pushes harder. Letting the drag happen and springing the window back afterwards fixes
// the symptom and leaves the machine feeling alive.
//
// DEFENSIVE ON PURPOSE. A throwing extension can take GNOME Shell down with it, and this
// one runs on a shop's till. Every hook is wrapped, the signal handler reads its window
// out of whatever arguments the shell version passes rather than assuming a signature
// (it changed in GNOME 45), and disable() disconnects everything.
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

// MATCH /chrom/, NOT "chromium". First version tested for the literal string
// "chromium" and never fired once: Angel dragged the till half off the screen and had
// to double-click the title bar to get it back, on a build where the extension
// reported State: ACTIVE. Chromium launched with `--app=URL` does not call its window
// "chromium" — it derives an app id from the URL, like
// `chrome-banco.wolfhold.app__pos-Default`. "Loaded" is not "working", and the only
// reason we know is that a person dragged a window and told me what happened.
//
// /chrom/ covers chromium, chromium-browser and chrome-*. On a till the only browser
// window IS the till, and maximising a stray one is harmless.
function isTill(w) {
    try {
        if (!w || typeof w.get_wm_class !== 'function') return false;
        if (w.get_window_type() !== Meta.WindowType.NORMAL) return false;
        return /chrom/.test((w.get_wm_class() || '').toLowerCase());
    } catch (e) {
        return false;
    }
}

// Say what we actually saw, once per window. Guessing at an app id is what produced a
// filter that matched nothing; this puts the real value in `journalctl --user`, so the
// next narrowing is a measurement instead of another guess.
const seen = new Set();
function describe(w) {
    try {
        if (!w || typeof w.get_wm_class !== 'function') return;
        const id = `${w.get_wm_class()}|${w.get_title()}`;
        if (seen.has(id)) return;
        seen.add(id);
        console.log(`banco-till-snapback: window wm_class=${JSON.stringify(w.get_wm_class())} `
                  + `title=${JSON.stringify(w.get_title())} match=${isTill(w)}`);
    } catch (e) {}
}

// The signal signature for grab-op-end changed in GNOME 45. Rather than pick one and be
// wrong on the next release, find the Meta.Window among whatever we were handed.
function windowFrom(args) {
    for (const a of args) {
        if (isTill(a)) return a;
    }
    return null;
}

export default class BancoTillSnapback extends Extension {
    enable() {
        this._handlers = [];
        this._timeouts = new Set();

        const connect = (obj, name, fn) => {
            try {
                this._handlers.push([obj, obj.connect(name, fn)]);
            } catch (e) {
                logError(e, `banco-till-snapback: could not connect ${name}`);
            }
        };

        connect(global.display, 'grab-op-end', (...args) => this._snapSoon(windowFrom(args)));
        connect(global.display, 'window-created', (...args) => this._snapSoon(windowFrom(args)));

        // Whatever is already on screen when the extension starts.
        try {
            for (const actor of global.get_window_actors())
                this._snapSoon(actor.meta_window);
        } catch (e) {
            logError(e, 'banco-till-snapback: initial sweep failed');
        }
    }

    // A short delay, because maximising inside the grab handler fights the drag that is
    // still finishing. 250ms is after the gesture and long before anyone reaches again.
    _snapSoon(win) {
        describe(win);
        if (!isTill(win)) return;
        const id = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 250, () => {
            this._timeouts.delete(id);
            try {
                if (isTill(win) && win.get_maximized() !== Meta.MaximizeFlags.BOTH)
                    win.maximize(Meta.MaximizeFlags.BOTH);
            } catch (e) {
                logError(e, 'banco-till-snapback: maximize failed');
            }
            return GLib.SOURCE_REMOVE;
        });
        this._timeouts.add(id);
    }

    disable() {
        for (const [obj, id] of this._handlers ?? []) {
            try { obj.disconnect(id); } catch (e) {}
        }
        this._handlers = null;
        for (const id of this._timeouts ?? []) {
            try { GLib.source_remove(id); } catch (e) {}
        }
        this._timeouts = null;
    }
}
