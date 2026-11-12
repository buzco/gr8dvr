"""Windows 95 style widgets for Tkinter (bevels, buttons, tabs, checkboxes, tooltips, progress, trackbar)."""
import tkinter as tk
from tkinter import font as tkfont

# GR8DVR palette: beige + dark grey-blue (from the logo). Text DK on FACE = 10:1, FIELD text on ACC = 10:1.
FACE, HI, LT, SH, DK = '#dcdbe4', '#fbfaff', '#ecebf2', '#8b8aa6', '#0b0f2e'   # pearl (nacre) face
ACC, ACC_HI = '#0b2a9e', '#3d7be0'          # selection, progress, highlights
TIP, LINK, FIELD = '#f4f2ff', '#1f3fc8', '#f7f6f2'
BEIGE, NAVY = '#f0ede6', '#0a1030'          # logo colours
F = {}


def init_fonts(root):
    fams = set(tkfont.families(root))
    ui = next((f for f in ('MS Sans Serif', 'Microsoft Sans Serif', 'Tahoma', 'DejaVu Sans') if f in fams), 'TkDefaultFont')
    mono = next((f for f in ('Fixedsys', 'Lucida Console', 'Courier New', 'DejaVu Sans Mono') if f in fams), 'TkFixedFont')
    F.update(ui=(ui, 9), bold=(ui, 9, 'bold'), small=(ui, 8), title=(ui, 12, 'bold'), big=(ui, 20, 'bold'),
             mono=(mono, 9), link=(ui, 9, 'underline'))
    root.option_add('*Font', F['ui'])
    root.option_add('*Background', FACE)
    root.option_add('*Foreground', DK)
    root.option_add('*selectBackground', ACC)
    root.option_add('*selectForeground', FIELD)
    root.option_add('*Menu.activeBackground', ACC)
    root.option_add('*Menu.activeForeground', HI)
    root.option_add('*Menu.relief', 'raised')
    root.configure(bg=FACE)


RINGS = {'raised': [(HI, DK), (LT, SH)], 'sunken': [(SH, HI), (DK, LT)], 'etched': [(SH, HI), (HI, SH)],
         'thin': [(SH, HI)], 'status': [(SH, HI)]}


def _ring(parent, tl, br, bg):
    for r, c, rs, cs, col, st in ((0, 0, 1, 2, tl, 'ew'), (0, 2, 1, 1, br, 'ew'), (1, 0, 1, 1, tl, 'ns'),
                                  (1, 2, 1, 1, br, 'ns'), (2, 0, 1, 3, br, 'ew')):
        tk.Frame(parent, bg=col, width=1, height=1).grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=st)
    inner = tk.Frame(parent, bg=bg)
    inner.grid(row=1, column=1, sticky='nsew')
    parent.grid_rowconfigure(1, weight=1)
    parent.grid_columnconfigure(1, weight=1)
    return inner


class Bevel(tk.Frame):
    """Two-tone Win95 border. Put children into .inner"""
    def __init__(self, parent, style='raised', bg=FACE, pad=0):
        super().__init__(parent, bg=FACE)
        f = self
        for tl, br in RINGS[style]:
            f = _ring(f, tl, br, bg)
        self.inner = tk.Frame(f, bg=bg)
        self.inner.pack(fill='both', expand=True, padx=pad, pady=pad)


def bevel_lines(c, x0, y0, x1, y1, rings):
    """Draw rings on canvas c around box (x0,y0)-(x1,y1) inclusive."""
    for i, (tl, br) in enumerate(rings):
        a, b, r, d = x0 + i, y0 + i, x1 - i, y1 - i
        c.create_line(a, d, a, b, r, b, fill=tl)
        c.create_line(a, d, r, d, r, b - 1, fill=br)


class Button(tk.Canvas):
    def __init__(self, parent, text, command=None, width=None, height=23, default=False, bold=False):
        self.font = F['bold'] if bold else F['ui']
        tw = tkfont.Font(font=self.font).measure(text)
        w = width or max(75, tw + 24)
        super().__init__(parent, width=w, height=height, bg=FACE, highlightthickness=0, bd=0, takefocus=1,
                         cursor='hand2')
        self.text, self.command, self.default, self.w, self.h = text, command, default, w, height
        self.pressed = self.inside = self.focused = False
        self.enabled = True
        for ev, fn in (('<Enter>', self._enter), ('<Leave>', self._leave), ('<ButtonPress-1>', self._down),
                       ('<ButtonRelease-1>', self._up), ('<FocusIn>', self._fin), ('<FocusOut>', self._fout),
                       ('<space>', self._key), ('<Return>', self._key)):
            self.bind(ev, fn)
        self.draw()

    def set_enabled(self, on):
        self.enabled = on
        self.configure(cursor='hand2' if on else 'arrow')
        self.draw()

    def set_text(self, t):
        self.text = t
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = self.w, self.h
        down = self.pressed and self.inside
        o = 0
        if self.default or self.focused:
            self.create_rectangle(0, 0, w - 1, h - 1, outline=DK)
            o = 1
        rings = [(DK, HI), (SH, LT)] if down else RINGS['raised']
        if down:
            self.create_rectangle(o, o, w - 1 - o, h - 1 - o, outline=SH)
        else:
            bevel_lines(self, o, o, w - 1 - o, h - 1 - o, rings)
        d = 1 if down else 0
        if self.enabled:
            self.create_text(w // 2 + d, h // 2 + d, text=self.text, font=self.font, fill=DK)
        else:
            self.create_text(w // 2 + 1, h // 2 + 1, text=self.text, font=self.font, fill=HI)
            self.create_text(w // 2, h // 2, text=self.text, font=self.font, fill=SH)
        if self.focused and self.enabled:
            self.create_rectangle(4 + d, 4 + d, w - 5 + d, h - 5 + d, outline=DK, dash=(1, 1))

    def _enter(self, _):
        self.inside = True; self.draw()

    def _leave(self, _):
        self.inside = False; self.draw()

    def _down(self, _):
        if self.enabled:
            self.pressed = True; self.focus_set(); self.draw()

    def _up(self, _):
        fire = self.pressed and self.inside and self.enabled
        self.pressed = False; self.draw()
        if fire and self.command:
            self.after(10, self.command)

    def _fin(self, _):
        self.focused = True; self.draw()

    def _fout(self, _):
        self.focused = False; self.draw()

    def _key(self, _):
        if self.enabled and self.command:
            self.pressed = self.inside = True; self.draw()
            self.after(90, lambda: (setattr(self, 'pressed', False), self.draw(), self.command()))


class Check(tk.Frame):
    def __init__(self, parent, text, var, command=None, radio_value=None, bg=FACE):
        super().__init__(parent, bg=bg)
        self.var, self.value, self.command = var, radio_value, command
        self.c = tk.Canvas(self, width=13, height=13, bg=bg, highlightthickness=0, bd=0)
        self.c.pack(side='left', padx=(0, 5))
        self.l = tk.Label(self, text=text, bg=bg, anchor='w', justify='left')
        self.l.pack(side='left')
        for w in (self, self.c, self.l):
            w.bind('<Button-1>', self._click)
        self._tid = var.trace_add('write', lambda *_: self.draw())
        self.bind('<Destroy>', self._gone, add='+')
        self.draw()

    def _gone(self, e):
        if e.widget is self and self._tid:
            self.var.trace_remove('write', self._tid); self._tid = None

    def _click(self, _):
        if self.value is None:
            self.var.set(not self.var.get())
        else:
            self.var.set(self.value)
        if self.command:
            self.command()

    def draw(self):
        c = self.c
        c.delete('all')
        if self.value is None:                        # checkbox
            bevel_lines(c, 0, 0, 12, 12, RINGS['sunken'])
            c.create_rectangle(2, 2, 10, 10, fill=FIELD, outline=FIELD)
            if self.var.get():
                for i, (x, y) in enumerate(((3, 5), (4, 6), (5, 7), (6, 6), (7, 5), (8, 4), (9, 3))):
                    c.create_line(x, y, x, y + 3, fill=DK)
        else:                                         # radio
            c.create_arc(0, 0, 12, 12, start=45, extent=180, style='arc', outline=SH)
            c.create_arc(0, 0, 12, 12, start=225, extent=180, style='arc', outline=HI)
            c.create_arc(1, 1, 11, 11, start=45, extent=180, style='arc', outline=DK)
            c.create_arc(1, 1, 11, 11, start=225, extent=180, style='arc', outline=LT)
            c.create_oval(2, 2, 10, 10, fill=FIELD, outline=FIELD)
            if str(self.var.get()) == str(self.value):
                c.create_oval(4, 4, 8, 8, fill=DK, outline=DK)


class Tooltip:
    def __init__(self, widget, text, delay=250):
        self.w, self.text, self.delay, self.tip, self.job = widget, text, delay, None, None
        widget.bind('<Enter>', self._sched, add='+')
        widget.bind('<Leave>', self._hide, add='+')
        widget.bind('<ButtonPress>', self._hide, add='+')

    def _sched(self, _):
        self.job = self.w.after(self.delay, self._show)

    def _show(self):
        x, y = self.w.winfo_rootx() + 18, self.w.winfo_rooty() + self.w.winfo_height() + 2
        self.tip = t = tk.Toplevel(self.w)
        t.wm_overrideredirect(True)
        t.configure(bg=DK)
        tk.Label(t, text=self.text, bg=TIP, fg=DK, justify='left', wraplength=300, padx=5, pady=3,
                 font=F['ui']).pack(padx=1, pady=1)
        t.wm_geometry(f'+{x}+{y}')

    def _hide(self, _=None):
        if self.job:
            self.w.after_cancel(self.job); self.job = None
        if self.tip:
            self.tip.destroy(); self.tip = None


class Help(tk.Canvas):
    """The little (?) button. Hover = yellow tooltip, click = same text in a message box."""
    def __init__(self, parent, text, bg=FACE):
        super().__init__(parent, width=16, height=16, bg=bg, highlightthickness=0, bd=0, cursor='question_arrow')
        bevel_lines(self, 0, 0, 15, 15, RINGS['raised'])
        self.create_rectangle(2, 2, 13, 13, fill=FACE, outline=FACE)
        self.create_text(8, 8, text='?', font=F['bold'], fill=ACC)
        Tooltip(self, text)


class Progress(tk.Canvas):
    """Segmented Win95 progress bar."""
    def __init__(self, parent, width=300, height=20):
        super().__init__(parent, width=width, height=height, bg=FACE, highlightthickness=0, bd=0)
        self.value = 0.0
        self.bind('<Configure>', lambda e: self.draw())

    def set(self, v):
        self.value = max(0.0, min(1.0, v)); self.draw()

    def draw(self):
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10:
            w, h = int(self['width']), int(self['height'])
        bevel_lines(self, 0, 0, w - 1, h - 1, RINGS['thin'])
        seg, gap = max(6, (h - 6) * 2 // 3), 2
        inner = w - 6
        n = int(inner * self.value) // (seg + gap)
        for i in range(n):
            x = 3 + i * (seg + gap)
            self.create_rectangle(x, 3, x + seg - 1, h - 4, fill=ACC, outline=ACC)


class Slider(tk.Canvas):
    """Win95 trackbar. on_change(value) while dragging, on_release(value) when let go."""
    def __init__(self, parent, width=320, on_change=None, on_release=None):
        super().__init__(parent, width=width, height=26, bg=FACE, highlightthickness=0, bd=0, takefocus=1)
        self.value, self.on_change, self.on_release = 0.0, on_change, on_release
        self.bind('<Configure>', lambda e: self.draw())
        self.bind('<Button-1>', self._drag)
        self.bind('<B1-Motion>', self._drag)
        self.bind('<ButtonRelease-1>', lambda e: self.on_release and self.on_release(self.value))
        self.bind('<Left>', lambda e: self._step(-0.02))
        self.bind('<Right>', lambda e: self._step(0.02))

    def _width(self):
        w = self.winfo_width()
        return w if w > 10 else int(self['width'])

    def _step(self, d):
        self.value = max(0, min(1, self.value + d)); self.draw()
        if self.on_release:
            self.on_release(self.value)

    def _drag(self, e):
        self.focus_set()
        self.value = max(0.0, min(1.0, (e.x - 6) / (self._width() - 12))); self.draw()
        if self.on_change:
            self.on_change(self.value)

    def set(self, v):
        self.value = v; self.draw()

    def draw(self):
        self.delete('all')
        w = self._width()
        bevel_lines(self, 4, 8, w - 5, 11, RINGS['sunken'])
        for i in range(11):
            x = 6 + (w - 12) * i / 10
            self.create_line(x, 21, x, 25, fill=DK)
        x = 6 + (w - 12) * self.value
        self.create_polygon(x - 5, 1, x + 5, 1, x + 5, 15, x, 20, x - 5, 15, fill=FACE, outline='')
        self.create_line(x - 5, 15, x - 5, 1, x + 5, 1, fill=HI)
        self.create_line(x + 5, 1, x + 5, 15, x, 20, fill=DK)
        self.create_line(x - 5, 15, x, 20, fill=HI)
        self.create_line(x + 4, 2, x + 4, 15, fill=SH)


class Dropdown(tk.Frame):
    """Win95 combo box (sunken white field + arrow button) with a popup menu."""
    def __init__(self, parent, var, choices, width=34, command=None):
        super().__init__(parent, bg=FACE)
        self.var, self.choices, self.command = var, list(choices), command
        b = Bevel(self, 'sunken', bg=FIELD)
        b.pack(fill='x')
        self.lab = tk.Label(b.inner, textvariable=var, bg=FIELD, anchor='w', width=width, padx=3, cursor='hand2')
        self.lab.pack(side='left', fill='x', expand=True)
        self.btn = Button(b.inner, '▼', self.open, width=17, height=18)
        self.btn.pack(side='right')
        self.lab.bind('<Button-1>', lambda e: self.open())
        self.menu = tk.Menu(self, tearoff=0, bg=FIELD, fg=DK, activebackground=ACC, activeforeground=HI, bd=1)
        for c in self.choices:
            self.menu.add_command(label=c, command=lambda c=c: self._pick(c))

    def _pick(self, c):
        self.var.set(c)
        if self.command:
            self.command()

    def open(self):
        self.menu.post(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())


class Field(tk.Frame):
    """Sunken read-only text field (paths)."""
    def __init__(self, parent, var, width=40):
        super().__init__(parent, bg=FACE)
        b = Bevel(self, 'sunken', bg=FIELD)
        b.pack(fill='x', expand=True)
        tk.Label(b.inner, textvariable=var, bg=FIELD, anchor='w', width=width, padx=3, pady=1).pack(fill='x')


def group(parent, title):
    return tk.LabelFrame(parent, text=f' {title} ', relief='groove', bd=2, bg=FACE, padx=8, pady=6, font=F['ui'])


def hline(parent):
    f = tk.Frame(parent, bg=FACE)
    tk.Frame(f, bg=SH, height=1).pack(fill='x')
    tk.Frame(f, bg=HI, height=1).pack(fill='x')
    return f


class Tabs(tk.Frame):
    """Win95 property-sheet tabs."""
    H = 22

    def __init__(self, parent, on_change=None):
        super().__init__(parent, bg=FACE)
        self.on_change = on_change
        self.strip = tk.Canvas(self, height=self.H, bg=FACE, highlightthickness=0, bd=0)
        self.strip.pack(fill='x')
        body = tk.Frame(self, bg=FACE)
        body.pack(fill='both', expand=True)
        tk.Frame(body, bg=HI, width=1).pack(side='left', fill='y')
        tk.Frame(body, bg=DK, width=1).pack(side='right', fill='y')
        tk.Frame(body, bg=SH, width=1).pack(side='right', fill='y')
        tk.Frame(body, bg=DK, height=1).pack(side='bottom', fill='x')
        tk.Frame(body, bg=SH, height=1).pack(side='bottom', fill='x')
        self.body = tk.Frame(body, bg=FACE)
        self.body.pack(fill='both', expand=True, padx=8, pady=8)
        self.pages, self.cur = [], 0
        self.strip.bind('<Configure>', lambda e: self.draw())
        self.strip.bind('<Button-1>', self._click)
        self.f = tkfont.Font(font=F['ui'])

    def add(self, title):
        page = tk.Frame(self.body, bg=FACE)
        self.pages.append((title, page))
        if len(self.pages) == 1:
            page.pack(fill='both', expand=True)
        self.draw()
        return page

    def _spans(self):
        x, out = 2, []
        for t, _ in self.pages:
            w = self.f.measure(t) + 20
            out.append((x, x + w)); x += w
        return out

    def select(self, i):
        if i == self.cur:
            return
        self.pages[self.cur][1].pack_forget()
        self.cur = i
        self.pages[i][1].pack(fill='both', expand=True)
        self.draw()
        if self.on_change:
            self.on_change(i)

    def _click(self, e):
        for i, (a, b) in enumerate(self._spans()):
            if a <= e.x < b:
                self.select(i)

    def draw(self):
        c, H = self.strip, self.H
        c.delete('all')
        W = c.winfo_width()
        spans = self._spans()
        sa, sb = spans[self.cur][0] - 2, spans[self.cur][1] + 2
        c.create_line(0, H - 1, sa, H - 1, fill=HI)
        c.create_line(sb, H - 1, W, H - 1, fill=HI)
        for i, ((a, b), (t, _)) in enumerate(zip(spans, self.pages)):
            sel = i == self.cur
            if sel:
                a, b, y = a - 2, b + 2, 0
            else:
                y = 2
            c.create_rectangle(a + 1, y + 1, b - 2, H, fill=FACE, outline=FACE)
            c.create_line(a, H, a, y + 2, a + 2, y, b - 2, y, fill=HI)
            c.create_line(b - 2, y + 1, b - 1, y + 2, b - 1, H if sel else H - 1, fill=DK)
            c.create_line(b - 2, y + 2, b - 2, H if sel else H - 1, fill=SH)
            c.create_text((a + b) // 2, y + 10 + (0 if sel else 1), text=t, font=F['ui'], fill=DK)
            if sel:
                c.create_line(a + 1, H - 1, b - 2, H - 1, fill=FACE)


class FlyingPapers(tk.Canvas):
    """The classic Win95 'copying files' animation: a sheet flying from folder to folder."""
    def __init__(self, parent, bg=FACE):
        super().__init__(parent, width=150, height=46, bg=bg, highlightthickness=0, bd=0)
        self.t, self.job = 0, None
        self.draw()

    def _folder(self, x, y, open_=False):
        self.create_polygon(x, y + 4, x + 8, y + 4, x + 10, y + 1, x + 18, y + 1, x + 18, y + 4, x + 26, y + 4,
                            x + 26, y + 22, x, y + 22, fill='#e6c34a', outline=DK)
        if open_:
            self.create_polygon(x + 3, y + 9, x + 29, y + 9, x + 26, y + 22, x, y + 22, fill='#fde27a', outline=DK)

    def draw(self):
        self.delete('all')
        self._folder(6, 18, True)
        self._folder(118, 18, True)
        if self.job:
            import math
            p = (self.t % 24) / 23
            x = 20 + p * 110
            y = 26 - math.sin(p * math.pi) * 22
            sk = math.sin(p * math.pi * 2) * 3
            self.create_polygon(x - 6, y - 7 + sk, x + 6, y - 7 - sk, x + 6, y + 7 - sk, x - 6, y + 7 + sk,
                                fill=FIELD, outline=DK)
            for k in (-3, 0, 3):
                self.create_line(x - 3, y + k, x + 3, y + k, fill=SH)

    def start(self):
        if not self.job:
            self._tick()

    def _tick(self):
        self.t += 1
        self.job = self.after(45, self._tick)
        self.draw()

    def stop(self):
        if self.job:
            self.after_cancel(self.job); self.job = None
        self.draw()


class Backdrop(tk.Canvas):
    """The sky-to-deep-sea gradient (gr8core.scene), re-rendered to fit whenever the widget is resized."""
    def __init__(self, parent, floor=True, stars=1.0, seed=7, **kw):
        kw.setdefault('height', 60)
        super().__init__(parent, bg='#00031a', highlightthickness=0, bd=0, **kw)
        self.floor, self.star_density, self.seed = floor, stars, seed
        self._size, self._job, self.img = None, None, None
        self.bind('<Configure>', lambda e: self._layout(), add='+')
        self._render()

    def _dims(self):
        return (max(self.winfo_width(), int(self.winfo_fpixels(self['width'] or 1)), 2),
                max(self.winfo_height(), int(self.winfo_fpixels(self['height'] or 1)), 2))

    def _layout(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self._render)

    def _render(self):
        from gr8core import scene
        self._job = None
        W, H = self._dims()
        if (W, H) == self._size:
            return
        self._size = (W, H)
        self.img = tk.PhotoImage(data=scene.ppm(W, H, floor=self.floor, stars=self.star_density, seed=self.seed))
        self.delete('sky')
        self.create_image(0, 0, image=self.img, anchor='nw', tags='sky')
        self.tag_lower('sky')
        self.on_resize(W, H)

    def on_resize(self, W, H):
        pass


def _wave_rgb(nm):
    """Visible wavelength (380-700 nm) -> (r, g, b) 0..1, with the usual edge fall-off."""
    if nm < 440:
        r, g, b = -(nm - 440) / 60, 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, -(nm - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    f = 0.35 + 0.65 * (nm - 380) / 40 if nm < 420 else 0.35 + 0.65 * (700 - nm) / 50 if nm > 650 else 1.0
    return tuple(max(0.0, c * f) ** 0.8 for c in (r, g, b))


def _hex(rgb):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(c))) for c in rgb)


class Helix(Backdrop):
    """Data conversion as a soft rainbow beam: white light leaves the camcorder lens and fans out into the
    spectrum (red on top, violet below) like light through a prism, reaching for the nautilus. The beam
    grows left to right with the progress.
    states: idle (faint, breathing), scan (a glint travels along), busy (beam grows with progress),
    ok (full beam flares white, sparkles), error (dims to a flickering red)"""
    BANDS = 16                                               # colour bands across the beam
    SEGS = 32                                                # segments along it

    def __init__(self, parent, cam_png, store_png, height=104, **kw):
        super().__init__(parent, floor=False, stars=1.4, seed=3, height=height, **kw)
        self.cam = tk.PhotoImage(file=cam_png)
        self.store = tk.PhotoImage(file=store_png)
        self.state, self.t, self.until = 'idle', 0, 0
        self.progress, self.shown = 0.0, 0.0
        self.sparks = []
        self.BG = (4, 30, 120)
        self.cols = [_wave_rgb(680 - 290 * (i + .5) / self.BANDS) for i in range(self.BANDS)]   # red -> violet
        self._anim()

    def set_state(self, s, hold=0):
        self.state = s
        self.until = self.t + hold
        if s == 'ok':
            import random
            self.sparks = [(random.uniform(-46, 40), random.uniform(-42, 36), random.randrange(4, 22))
                           for _ in range(16)]

    def _mix(self, rgb, k, white=0.0):
        r, g, b = (c + (1 - c) * white for c in rgb)
        return _hex([bg + (c * 255 - bg) * k for c, bg in zip((r, g, b), self.BG)])

    def _bg_at(self, f_y):
        from gr8core import scene
        st_ = scene.STOPS
        for (a0, c0), (a1, c1) in zip(st_, st_[1:]):
            if a0 <= f_y <= a1:
                u = (f_y - a0) / (a1 - a0)
                return tuple(c0[i] + (c1[i] - c0[i]) * u for i in range(3))
        return st_[-1][1]

    def _anim(self):
        import math
        self.t += 1
        if self.until and self.t >= self.until and self.state in ('ok', 'error'):
            self.state, self.until = 'idle', 0
        st = self.state
        self.after(40, self._anim)
        if not self.winfo_ismapped() and self.t > 2:
            return
        self.delete('dna')
        W = max(self.winfo_width(), 200)
        H = max(self.winfo_height(), int(self.winfo_fpixels(self['height'])))
        cy = H // 2 + 2
        self.BG = self._bg_at(cy / H)
        cw, sw = self.cam.width(), self.store.width()
        x0, x1 = cw + 4, W - sw + 2
        span = max(1, x1 - x0)
        shake = math.sin(self.t * 2.3) * 2 if st == 'error' else 0
        self.create_image(4, cy, image=self.cam, anchor='w', tags='dna')
        target = {'busy': self.progress, 'ok': 1.0}.get(st, 1.0 if st in ('idle', 'scan', 'error') else 0.0)
        if st == 'busy' and self.shown > self.progress + 0.02:              # a new job starts from the lens
            self.shown = 0.0
        self.shown += (target - self.shown) * (0.12 if st == 'busy' else 0.25)
        head = x0 + span * self.shown
        base = {'idle': 0.32 + 0.1 * math.sin(self.t / 14), 'scan': 0.38, 'busy': 1.0, 'ok': 1.0,
                'error': 0.75}.get(st, 0.4)
        flash = max(0.0, (self.until - self.t - 40) / 30) if st == 'ok' else 0.0
        glint = x0 + ((self.t * 7) % int(span + 80)) - 40
        y_lens = cy - 6                                                   # the lens sits a little above centre
        for j in range(self.SEGS):
            fa, fb = j / self.SEGS, (j + 1) / self.SEGS
            xa, xb = x0 + span * fa, x0 + span * fb
            if xa >= head:
                break
            xb = min(xb, head)
            fb = (xb - x0) / span
            # beam geometry: a narrow white ray that opens into a fan
            def edges(f):
                half = 1.5 + 15 * min(1.0, f * 1.6) ** 0.8
                yc = y_lens + (cy + 2 - y_lens) * min(1.0, f * 2)
                return yc - half, yc + half
            ta, ba = edges(fa); tb, bb = edges(fb)
            white = max(0.0, 1 - fa * 3.2) * 0.85                         # white near the lens, rainbow later
            shimmer = 0.88 + 0.12 * math.sin(self.t / 5 - j * 0.7)
            k_seg = base * shimmer
            if st in ('idle', 'scan') and abs((xa + xb) / 2 - glint) < 34:
                k_seg = min(1.0, k_seg + 0.55 * (1 - abs((xa + xb) / 2 - glint) / 34))
            tip = (head - xa) / max(1.0, xb - xa)
            if st == 'busy' and xb >= head - 1:
                k_seg *= 0.75                                             # soft leading edge
            if st == 'error' and (self.t // 3) % 2:
                k_seg *= 0.55
            for i, rgb in enumerate(self.cols):
                if st == 'error':
                    rgb = (0.95, 0.22, 0.18)
                u0, u1 = i / self.BANDS, (i + 1) / self.BANDS
                edge = math.sin(math.pi * (u0 + u1) / 2) ** 0.7             # soft top/bottom edges
                col = self._mix(rgb, k_seg * edge, min(1.0, white + flash * 0.7))
                y0a, y1a = ta + (ba - ta) * u0 + shake, ta + (ba - ta) * u1 + shake
                y0b, y1b = tb + (bb - tb) * u0 + shake, tb + (bb - tb) * u1 + shake
                self.create_polygon(xa, y0a, xb, y0b, xb, y1b + .6, xa, y1a + .6, fill=col, outline='', tags='dna')
        # lens glow
        for r, k in ((9, .22), (5, .55), (2.5, 1)):
            self.create_oval(x0 - r, y_lens - r, x0 + r, y_lens + r, fill=self._mix((1, 1, 1), k), outline='',
                             tags='dna')
        if st == 'busy' and x0 + 4 < head < x1 - 2:                       # a soft star at the growing tip
            hy = y_lens + (cy + 2 - y_lens) * min(1.0, self.shown * 2) + shake
            L = 7 + 3 * math.sin(self.t / 2)
            self.create_line(head - L, hy, head + L, hy, fill=self._mix((1, 1, 1), .9), tags='dna')
            self.create_line(head, hy - L, head, hy + L, fill=self._mix((1, 1, 1), .9), tags='dna')
            self.create_oval(head - 2, hy - 2, head + 2, hy + 2, fill='#ffffff', outline='', tags='dna')
        sx = W - sw - 4
        self.create_image(sx, cy, image=self.store, anchor='w', tags='dna')
        if st == 'ok':
            left = self.until - self.t
            for dx, dy, ph in self.sparks:
                if (self.t + ph) % 8 < 5 and left > 0:
                    x, y = sx + sw / 2 + dx, cy + dy
                    self.create_line(x - 4, y, x + 5, y, fill='#fbfaff', tags='dna')
                    self.create_line(x, y - 4, x, y + 5, fill='#c9d8ff', tags='dna')


def _dim(hexcol, k=0.45):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return f'#{int(r * k):02x}{int(g * k):02x}{int(b * k):02x}'
