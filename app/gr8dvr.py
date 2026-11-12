"""GR8DVR - MiniDV / Mini DVR toolkit by Buzco (Windows 95 style UI, runs on Windows and macOS)."""
import datetime
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

if getattr(sys, 'frozen', False):                      # bundled ffmpeg/ffprobe/ffplay live in the unpack dir
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

from gr8core import VERSION, convert, firmware, importer, legal, library, looks, sound, vendor  # noqa: E402
import gr8w95 as w
from gr8w95 import ACC, BEIGE, DK, F, FACE, FIELD, HI, LINK, LT, SH
DIM = '#454a66'   # secondary text on the pearl face
OKC = '#1b6b55'   # success text

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gr8core', 'data')
URL_SITE = 'https://gr8success.xyz'
URL_PAGE = 'https://gr8success.xyz/pages/gr8dvr'
URL_DONATE = 'https://gr8success.xyz/products/support-gr8dvr'
URL_SHOP = 'https://gr8success.xyz/collections/all'


def asset(name):
    return os.path.join(DATA, name)


def hms(s):
    s = int(s or 0)
    return f'{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}'


def guess_cards():
    """Removable drives that look like a DVR card (Windows drive letters, macOS /Volumes, Linux /media)."""
    out = []
    for root, _ in library.drives():
        try:
            if os.path.isdir(os.path.join(root, 'DCIM')) or any(
                    n.upper().endswith(('.AVI', '.BIN')) for n in os.listdir(root)):
                out.append(root)
        except OSError:
            pass
    return out


def link(parent, text, url, bg=FACE):
    l = tk.Label(parent, text=text, fg=LINK, bg=bg, cursor='hand2', font=F['link'])
    l.bind('<Button-1>', lambda e: webbrowser.open(url))
    return l


def row_help(parent, widget, text):
    """Pack widget + (?) side by side; returns the row frame."""
    r = tk.Frame(parent, bg=FACE)
    widget(r).pack(side='left')
    w.Help(r, text).pack(side='left', padx=6)
    return r


# ---------------------------------------------------------------- splash
class ArtScene(tk.Canvas):
    """The key illustration (nautilus, prism, chip): a pre-cut PNG kept centred whatever the widget size, with a
    few soft twinkles. `art` is the size of the real picture inside the PNG (the rest is a blurred echo), so
    overlays can be placed in picture coordinates via place(item, x, y)."""
    TWINKLES = [(.05, .07), (.16, .12), (.25, .05), (.34, .2), (.55, .03), (.64, .07), (.71, .44), (.96, .5),
                (.58, .9), (.03, .72), (.44, .62), (.9, .97)]

    def __init__(self, parent, file, art, **kw):
        import random
        super().__init__(parent, bg='#00031a', highlightthickness=0, bd=0, **kw)
        self.img = tk.PhotoImage(file=asset(file))
        self.art, self.ox, self.oy, self.t = art, 0, 0, 0
        self.create_image(0, 0, image=self.img, anchor='center', tags='sky')
        self.placed = []
        rnd = random.Random(4)
        self.tw = [(fx, fy, rnd.randrange(40), self.create_line(0, 0, 0, 0, fill='', tags='tw'),
                    self.create_line(0, 0, 0, 0, fill='', tags='tw')) for fx, fy in self.TWINKLES]
        self.bind('<Configure>', self._fit, add='+')
        self._anim()

    def place(self, item, x, y):
        """Pin a canvas item to picture coordinates (re-applied on resize)."""
        self.placed.append((item, x, y))
        self.coords(item, self.ox + x, self.oy + y)
        return item

    def _fit(self, e):
        self.coords('sky', e.width // 2, e.height // 2)
        self.ox, self.oy = (e.width - self.art[0]) // 2, (e.height - self.art[1]) // 2
        for item, x, y in self.placed:
            self.coords(item, self.ox + x, self.oy + y)
        self.tag_raise('tw'); self.tag_raise('ui')

    def _anim(self):
        self.after(70, self._anim)
        if not self.winfo_ismapped():
            return
        self.t += 1
        for fx, fy, ph, h, v in self.tw:
            k = (self.t + ph) % 40
            r = (0, 1, 2, 3, 2, 1, 0)[k] if k < 7 else 0          # brief, soft sparkle
            x, y = self.ox + fx * self.art[0], self.oy + fy * self.art[1]
            col = ('#8fb4ff', '#c9d8ff', '#fbfaff', '#fbfaff', '#fbfaff', '#c9d8ff', '#8fb4ff')[k] if r else ''
            self.coords(h, x - r - 1, y, x + r + 2, y); self.coords(v, x, y - r - 1, x, y + r + 2)
            self.itemconfigure(h, fill=col); self.itemconfigure(v, fill=col)


class Splash(tk.Toplevel):
    """Boot screen: the key illustration with the GR8DVR and Buzco logos, legal notice and a loading bar."""
    STEPS = ['Waking the nautilus…', 'Loading looks…', 'Checking FFmpeg…', 'Reading firmware patch…',
             'Warming up the tape heads…', 'Ready']

    def __init__(self, root, done):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg=FACE)
        self.done = done
        b = w.Bevel(self, 'raised')
        b.pack()
        W, H = 600, 300
        c = self.c = ArtScene(b.inner, 'splash.png', (W, H), width=W, height=H)
        c.pack(padx=4, pady=(4, 0))
        self.logo = tk.PhotoImage(file=asset('logo.png'))
        self.buzco = tk.PhotoImage(file=asset('buzco_small.png'))
        lx, ly = W // 2, 18
        c.create_rectangle(lx - self.logo.width() // 2 - 3, ly - 3, lx + self.logo.width() // 2 + 2,
                           ly + self.logo.height() + 2, fill=BEIGE, outline=BEIGE, tags='ui')
        c.create_image(lx, ly, image=self.logo, anchor='n', tags='ui')
        for dx, col in ((1, '#000000'), (0, BEIGE)):
            c.create_text(lx + dx, ly + self.logo.height() + 16 + dx, font=F['bold'], fill=col,
                          text=f'Version {VERSION}  ·  MiniDV · Mini DVR · Media Toolkit', tags='ui')
        c.create_image(14, 14, image=self.buzco, anchor='nw', tags='ui')
        c.create_text(14 + self.buzco.width() // 2, 18 + self.buzco.height(), text='presents', fill=BEIGE,
                      font=F['small'], tags='ui')
        info = tk.Frame(b.inner, bg=FACE)
        info.pack(fill='x', padx=10, pady=(8, 8))
        tk.Label(info, text=legal.SPLASH, justify='left', wraplength=W - 16, anchor='w',
                 font=F['small']).pack(fill='x')
        self.msg = tk.Label(info, text='', anchor='w', font=F['small'], fg=DIM)
        self.msg.pack(fill='x', pady=(6, 2))
        self.bar = w.Progress(info, width=W - 16, height=18)
        self.bar.pack(fill='x')
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
        self.geometry(f'+{x}+{y}')
        self.bind('<Button-1>', lambda e: self.finish())
        self.k = 0
        sound.enabled = library.load_settings().get('sounds', True)
        sound.play('boot')
        self.after(160, self.tick)

    def tick(self):
        self.k += 1
        n = 34
        self.bar.set(self.k / n)
        self.msg.configure(text=self.STEPS[min(len(self.STEPS) - 1, self.k * len(self.STEPS) // n)])
        if self.k >= n:
            self.after(400, self.finish)
        else:
            self.after(100, self.tick)

    def finish(self):
        if self.done:
            d, self.done = self.done, None
            self.destroy()
            d()


# ---------------------------------------------------------------- app
class App:
    def __init__(self, root):
        self.root, self.q = root, queue.Queue()
        root.title(f'GR8DVR {VERSION}')
        root.geometry('1000x720')
        root.minsize(960, 690)
        _ttk_style(root)
        self._menu()
        self._header()
        self.tabs = w.Tabs(root)
        self.tabs.pack(fill='both', expand=True, padx=6, pady=(4, 2))
        self.converter = ClipTab(self, self.tabs.add('Media Converter'), 'media')
        self.importer = ClipTab(self, self.tabs.add('Mini DVR Import'), 'dvr')
        self.builder = FirmwareTab(self, self.tabs.add('Mini DVR Firmware Builder'))
        self.about = AboutTab(self, self.tabs.add('About'))
        self._footer()
        root.after(100, self._poll)

    # --- chrome
    def _menu(self):
        m = tk.Menu(self.root, tearoff=0)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label='Add videos…', command=lambda: (self.tabs.select(0), self.converter.add_files()))
        f.add_command(label='Rescan cards', command=lambda: (self.converter.rescan(), self.importer.rescan()))
        f.add_separator()
        f.add_command(label='Exit', command=self.root.destroy)
        m.add_cascade(label='File', menu=f, underline=0)
        o = tk.Menu(m, tearoff=0)
        self.snd = tk.BooleanVar(value=library.load_settings().get('sounds', True))
        sound.enabled = self.snd.get()
        o.add_checkbutton(label='Sounds', variable=self.snd, command=self._sounds)
        m.add_cascade(label='Options', menu=o, underline=0)
        h = tk.Menu(m, tearoff=0)
        h.add_command(label='Install guide && FAQ (website)', command=lambda: webbrowser.open(URL_PAGE))
        h.add_command(label='License && notices', command=self.show_license)
        h.add_separator()
        h.add_command(label='Donate…', command=lambda: webbrowser.open(URL_DONATE))
        h.add_command(label='Buzco store', command=lambda: webbrowser.open(URL_SHOP))
        h.add_separator()
        h.add_command(label='About GR8DVR', command=lambda: self.tabs.select(3))
        m.add_cascade(label='Help', menu=h, underline=0)
        self.root.configure(menu=m)

    def _header(self):
        b = w.Bevel(self.root, 'sunken')
        b.pack(fill='x', padx=6, pady=(6, 0))
        self.sky = w.Backdrop(b.inner, floor=False, stars=1.6, seed=11, height=44)
        self.sky.pack(fill='x')
        self.logo_h = tk.PhotoImage(file=asset('logo_horiz.png'))
        self.sky.create_rectangle(9, 4, 12 + self.logo_h.width(), 7 + self.logo_h.height(), fill=BEIGE, outline='')
        self.sky.create_image(11, 6, image=self.logo_h, anchor='nw')
        for dx, col in ((1, '#000000'), (0, BEIGE)):
            self.sky.create_text(28 + self.logo_h.width() + dx, 23 + dx, text='MiniDV · Mini DVR · Media Toolkit',
                                 anchor='w', font=F['bold'], fill=col)
            self.sky.create_text(-10 + dx, 22 + dx, text=f'v{VERSION}', anchor='e', font=F['bold'], fill=col,
                                 tags='ver')
        self.sky.bind('<Configure>', lambda e: [self.sky.coords(i, e.width - 10 + k, 22 + k) for k, i in
                                                zip((1, 0), self.sky.find_withtag('ver'))], add='+')

    def _footer(self):
        bar = tk.Frame(self.root, bg=FACE)
        bar.pack(fill='x', side='bottom', padx=2, pady=2)
        sm, ln = F['small'], (F['small'][0], F['small'][1], 'underline')

        def lk(parent, text, url):
            l = tk.Label(parent, text=text, fg=LINK, cursor='hand2', font=ln)
            l.bind('<Button-1>', lambda e: webbrowser.open(url))
            return l
        p1 = w.Bevel(bar, 'status')
        p1.pack(side='left', padx=(0, 2))
        r = tk.Frame(p1.inner)
        r.pack(padx=4, pady=1)
        tk.Label(r, text='Powered by', font=sm).pack(side='left')
        lk(r, 'Buzco · GR8 Success', URL_SITE).pack(side='left', padx=(3, 0))
        p2 = w.Bevel(bar, 'status')
        p2.pack(side='left', fill='x', expand=True)
        r = tk.Frame(p2.inner)
        r.pack(anchor='w', padx=4, pady=1)
        tk.Label(r, text='This is a freeware - use at your own risk! If you like this tool, consider',
                 font=sm).pack(side='left')
        lk(r, 'donating', URL_DONATE).pack(side='left', padx=2)
        tk.Label(r, text='or buy a piece from', font=sm).pack(side='left')
        lk(r, 'our store', URL_SHOP).pack(side='left', padx=(2, 0))

    def _sounds(self):
        sound.enabled = self.snd.get()
        library.save_settings(sounds=sound.enabled)
        sound.play('tick')

    def show_license(self):
        t = tk.Toplevel(self.root)
        t.title('License & notices')
        t.geometry('640x480')
        t.transient(self.root)
        b = w.Bevel(t, 'sunken', bg=FIELD)
        b.pack(fill='both', expand=True, padx=8, pady=8)
        txt = tk.Text(b.inner, bg=FIELD, relief='flat', bd=0, font=F['mono'], wrap='word', padx=6, pady=6)
        sb = tk.Scrollbar(b.inner, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        txt.pack(fill='both', expand=True)
        txt.insert('1.0', legal.LICENSE)
        txt.configure(state='disabled')
        w.Button(t, 'OK', t.destroy, default=True).pack(pady=(0, 8))

    # --- background jobs talk to the UI through this queue
    def post(self, fn, *a):
        self.q.put((fn, a))

    def _poll(self):
        try:
            while True:
                fn, a = self.q.get_nowait()
                fn(*a)
        except queue.Empty:
            pass
        self.root.after(60, self._poll)


def open_folder(path):
    if os.name == 'nt':
        os.startfile(path)                               # noqa: S606
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


# ---------------------------------------------------------------- clip tabs (Media Converter + Mini DVR Import)
ROT_STEPS = ['0°', '90° ⟳', '180°', '90° ⟲']
ROT_NAMES = {'0°': 'Normal', '90° ⟳': 'Right 90°', '180°': '180°', '90° ⟲': 'Left 90°'}


class ClipTab:
    """TM700-style importer: finds the card by itself, ticks only clips that were never imported,
    names files by recording date, shows exactly what will happen, DNA animation + sounds."""

    def __init__(self, app, page, kind):
        self.app, self.kind = app, kind                    # kind: 'media' | 'dvr'
        self.dvr = kind == 'dvr'
        st = library.load_settings()
        self.base = tk.StringVar(value=st.get(f'{kind}_base') or library.default_base(
            'MiniDVR' if self.dvr else 'Converted'))
        self.extra = [p for p in st.get(f'{kind}_extra', []) if os.path.isdir(p)][-3:]
        self.manual = []                                   # files added by hand (media tab)
        self.rows, self.busy, self.scanning, self.scan_id = {}, False, False, 0
        self.ledger = library.Ledger()
        self.preview_img = self.preview_job = None
        self.known_drives = None
        # export settings
        self.fmt = tk.StringVar(value=st.get('fmt', list(convert.FORMATS)[0]))
        if self.fmt.get() not in convert.FORMATS:
            self.fmt.set(list(convert.FORMATS)[0])
        self.quality = tk.StringVar(value=st.get('quality', 'High'))
        self.deint = tk.BooleanVar(value=True)
        self.use_looks = tk.BooleanVar(value=st.get('looks', True))
        self.overscan = tk.BooleanVar(value=True)
        self.keep576 = tk.BooleanVar(value=False)
        self.heading = tk.StringVar(value='Looking for your card…')
        self.sub = tk.StringVar(value='')
        self.source_txt = tk.StringVar(value='')
        self.status = tk.StringVar(value='')
        self.dest = tk.StringVar()
        self._dest_update()
        self._build(page)
        for v in (self.fmt, self.quality, self.deint, self.use_looks, self.overscan):
            v.trace_add('write', lambda *_: (self._explain(), self._remember()))
        page.after(400, self.rescan)
        page.after(3000, self._watch_drives)

    # ------------------------------------------------ layout
    def _build(self, page):
        top = tk.Frame(page)
        top.pack(fill='x')
        hb = w.Bevel(top, 'sunken', bg=DK)
        hb.pack(side='left')
        self.helix = w.Helix(hb.inner, asset('camcorder_px.png'), asset('nautilus_px.png'),
                             width=480, height=94)
        self.helix.pack()
        hd = tk.Frame(top)
        hd.pack(side='left', fill='both', expand=True, padx=(12, 0))
        tk.Label(hd, textvariable=self.heading, font=F['title'], anchor='w').pack(fill='x', pady=(6, 0))
        tk.Label(hd, textvariable=self.sub, anchor='w').pack(fill='x', pady=(2, 6))
        self.bar = w.Progress(hd, height=20)
        self.bar.pack(fill='x')

        g = w.group(page, 'Where')
        g.pack(fill='x', pady=(4, 0))
        g.grid_columnconfigure(1, weight=1)
        tk.Label(g, text='From:', font=F['bold']).grid(row=0, column=0, sticky='w', padx=(0, 10))
        tk.Label(g, textvariable=self.source_txt, anchor='w', width=10).grid(row=0, column=1, sticky='ew')
        r = tk.Frame(g)
        r.grid(row=0, column=2, sticky='e')
        w.Button(r, 'Rescan', self.rescan).pack(side='left')
        w.Button(r, 'Pick folder…', self.pick_folder, width=90).pack(side='left', padx=(4, 0))
        if not self.dvr:
            w.Button(r, 'Add files…', self.add_files).pack(side='left', padx=(4, 0))
        w.Help(r, 'GR8DVR finds your card by itself: '
                  + ('Mini DVR cards (PICT*.AVI). ' if self.dvr else
                     'AVCHD camcorders (PRIVATE\\AVCHD) and camera cards (DCIM). ')
                  + 'Plug the card or camcorder in and it shows up within a few seconds.\n\n'
                  'Somewhere else? Use Pick folder… - GR8DVR remembers it next time.').pack(side='left', padx=(6, 0))
        tk.Label(g, text='Save to:', font=F['bold']).grid(row=1, column=0, sticky='w', pady=(4, 0))
        w.Field(g, self.dest, width=10).grid(row=1, column=1, sticky='ew', pady=(4, 0))
        r = tk.Frame(g)
        r.grid(row=1, column=2, sticky='e', pady=(4, 0))
        w.Button(r, 'Change…', self.pick_base).pack(side='left', padx=(4, 0))
        w.Help(r, 'Every import day gets its own folder named with the date, inside the folder you choose '
                  '(a Google Drive / OneDrive folder works great - clips sync to your phone).\n\n'
                  'Files are named by when they were filmed, e.g. 2026-11-11_14-32-05_00425.mp4, so they '
                  'sort in shooting order.').pack(side='left', padx=(6, 0))

        # bottom first, so the buttons are never pushed off a small screen
        bot = tk.Frame(page)
        bot.pack(side='bottom', fill='x', pady=(6, 0))
        w.Button(bot, 'Open Folder', self.open_dest, width=96).pack(side='right')
        self.cancel_b = w.Button(bot, 'Cancel', self.cancel, width=96)
        self.cancel_b.pack(side='right', padx=4)
        self.go = w.Button(bot, 'Convert' if not self.dvr else 'Import', self.start, width=120, default=True,
                           bold=True)
        self.go.pack(side='right')
        self.cancel_b.set_enabled(False)
        self.ticker = tk.Label(bot, textvariable=self.status, anchor='w', fg=DIM)
        self.ticker.pack(side='left', fill='x')

        row = tk.Frame(page)
        row.pack(side='bottom', fill='x', pady=(4, 0))
        g = w.group(row, 'Export settings')
        g.pack(side='right', fill='y', padx=(8, 0))
        if self.dvr:
            for text, var, tip in (
                    ('Apply the looks picked on the DVR', self.use_looks,
                     'GR8DVR firmware stamps the look number (0-8) into every frame. ON = the import applies '
                     'the matching colour look, also when you switched looks mid-recording. OFF = untouched '
                     'colours.'),
                    ('Hide edge noise (recommended)', self.overscan,
                     'Trims the noisy analog edges a TV would hide, then scales back to full 4:3 PAL.'),
                    ('Also save an untouched 576i master', self.keep576,
                     'An extra file with the original interlaced fields, no looks - for archiving.')):
                r = tk.Frame(g)
                r.pack(fill='x', pady=1)
                w.Check(r, text, var).pack(side='left')
                w.Help(r, tip).pack(side='right', padx=(8, 0))
        else:
            r = tk.Frame(g)
            r.pack(fill='x')
            tk.Label(r, text='Format:', width=7, anchor='w').pack(side='left')
            w.Dropdown(r, self.fmt, convert.FORMATS, width=26).pack(side='left')
            r = tk.Frame(g)
            r.pack(fill='x', pady=(3, 0))
            tk.Label(r, text='Quality:', width=7, anchor='w').pack(side='left')
            w.Dropdown(r, self.quality, convert.QUALITY, width=26).pack(side='left')
            r = tk.Frame(g)
            r.pack(fill='x', pady=(3, 0))
            w.Check(r, 'Smooth interlaced footage', self.deint).pack(side='left')
            w.Help(r, 'Camcorders film 50/60 half-pictures (fields) a second. GR8DVR turns each into a full '
                      'frame, so motion stays camcorder-smooth with no comb lines. Only used on interlaced '
                      'clips.\n\nFormats: MP4 H.264 plays everywhere (iPhone, Instagram, PC). H.265 is half '
                      'the size. ProRes is for editing. GIF for short loops. MP3 for just the sound.'
                   ).pack(side='right')
        g = w.group(row, 'Exact conversion settings for the selected clip')
        g.pack(side='left', fill='both', expand=True)
        eb = w.Bevel(g, 'sunken', bg=FIELD)
        eb.pack(fill='both', expand=True)
        self.explain = tk.Text(eb.inner, height=4, width=10, bg=FIELD, relief='flat', bd=0, font=F['ui'],
                               wrap='word', padx=4, pady=2, state='disabled')
        self.explain.pack(fill='both', expand=True)

        body = tk.Frame(page)
        body.pack(fill='both', expand=True, pady=(4, 0))
        g = w.group(body, 'Preview')
        g.pack(side='right', fill='y', padx=(8, 0))
        pv = w.Bevel(g, 'sunken', bg=DK)
        pv.pack()
        self.canvas = tk.Canvas(pv.inner, width=256, height=192, bg=DK, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.canvas.create_text(128, 96, text='Click a clip to preview it', fill='#9a9a9a', tags='msg')
        self.slider = w.Slider(g, width=260, on_change=self.on_scrub, on_release=lambda v: self.load_preview())
        self.slider.pack(pady=(2, 0))
        self.timepos = tk.Label(g, text='', font=F['mono'])
        self.timepos.pack()
        r = tk.Frame(g)
        r.pack(pady=(2, 0))
        w.Button(r, 'Turn Left', lambda: self.turn(-1), width=82).pack(side='left')
        w.Button(r, 'Turn Right', lambda: self.turn(1), width=82).pack(side='left', padx=4)
        w.Button(r, 'Play', self.play, width=82).pack(side='left')

        g = w.group(body, 'Clips  |  tick the ones to convert')
        g.pack(side='left', fill='both', expand=True)
        r = tk.Frame(g)
        r.pack(side='bottom', fill='x', pady=(4, 0))
        w.Button(r, 'Tick new', self.tick_new).pack(side='left')
        w.Button(r, 'Tick all', lambda: self.tick_all(True)).pack(side='left', padx=4)
        w.Button(r, 'Untick all', lambda: self.tick_all(False)).pack(side='left')
        w.Help(r, 'GR8DVR remembers every clip it has converted (by its content, not its name). Clips you '
                  'already imported show "Imported" and are NOT ticked, so you never convert the same clip '
                  'twice. Tick them yourself if you want them again.').pack(side='left', padx=6)
        cols = ('clip', 'rec', 'len', 'type', 'orient', 'size', 'status')
        self.tree = ttk.Treeview(g, columns=cols, show='tree headings', selectmode='extended', height=4)
        heads = {'#0': ('', 30), 'clip': ('Clip', 94), 'rec': ('Recorded', 116), 'len': ('Length', 54),
                 'type': ('Type', 94), 'orient': ('Orientation', 74), 'size': ('Size', 58),
                 'status': ('Status', 100)}
        for c, (t, wd) in heads.items():
            self.tree.heading(c, text=t, anchor='w')
            self.tree.column(c, width=wd, minwidth=24, stretch=c == 'status', anchor='w')
        self.tree.tag_configure('old', foreground=DIM)
        self.tree.tag_configure('fail', foreground='#a8321c')
        self.tree.tag_configure('done', foreground=OKC)
        self.box_on, self.box_off = _checkbox_img(True), _checkbox_img(False)
        sb = ttk.Scrollbar(g, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Button-1>', self._tree_click, add='+')
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.on_select())
        self.tree.bind('<space>', lambda e: self.toggle(self.tree.selection()))

    # ------------------------------------------------ settings
    def _remember(self):
        library.save_settings(**{f'{self.kind}_base': self.base.get(), f'{self.kind}_extra': self.extra,
                                 'fmt': self.fmt.get(), 'quality': self.quality.get(),
                                 'looks': self.use_looks.get()})

    def _dest_update(self):
        self.dest.set(library.dated_dir(self.base.get()) + os.sep)

    def pick_base(self):
        d = filedialog.askdirectory(title='Save converted clips in…', initialdir=self.base.get())
        if d:
            self.base.set(os.path.normpath(d)); self._dest_update(); self._remember()
            self.rescan()

    def open_dest(self):
        d = self.dest.get()
        open_folder(d if os.path.isdir(d) else self.base.get() if os.path.isdir(self.base.get())
                    else os.path.expanduser('~'))

    # ------------------------------------------------ finding clips
    def _exts(self):
        return ('.avi',) if self.dvr else convert.VIDEO_EXT

    def _watch_drives(self):
        """Card or camcorder plugged in / removed -> rescan by itself (like the TM700 app)."""
        try:
            now = tuple(r for r, rem in library.drives() if rem)
        except Exception:                                    # noqa: BLE001
            now = self.known_drives
        if self.known_drives is not None and now != self.known_drives and not self.busy:
            if set(now) - set(self.known_drives or ()):
                sound.play('card')
            self.rescan()
        self.known_drives = now
        self.tree.after(2500, self._watch_drives)

    def pick_folder(self):
        d = filedialog.askdirectory(title='Folder with clips')
        if d:
            d = os.path.normpath(d)
            self.extra = [p for p in self.extra if p != d][-2:] + [d]
            self._remember()
            self.rescan()

    def add_files(self):
        exts = ' '.join('*' + e for e in convert.VIDEO_EXT)
        ps = filedialog.askopenfilenames(title='Add videos', filetypes=[('Videos', exts + ' ' + exts.upper()),
                                                                        ('All files', '*.*')])
        if ps:
            self.manual += [p for p in ps if p not in self.manual]
            self.rescan()

    def rescan(self):
        if self.busy:
            return
        self.scan_id += 1
        sid = self.scan_id
        self.helix.set_state('scan')
        self.heading.set('Looking for your clips…')
        self.sub.set('Checking cards and drives')
        threading.Thread(target=self._scan, args=(sid,), daemon=True).start()

    def _scan(self, sid):
        kinds = ('dvr',) if self.dvr else ('avchd', 'camera')
        try:
            srcs = library.scan(kinds)
        except Exception:                                    # noqa: BLE001
            srcs = []
        clips, labels = [], [s['label'] for s in srcs]
        for s in srcs:
            clips += s['clips']
        for p in self.extra:
            fc = (importer.find_clips(p) if self.dvr else library.folder_clips(p, convert.VIDEO_EXT))
            if fc:
                labels.append(f'folder {p}')
                clips += fc
        if self.manual:
            labels.append(f'{len(self.manual)} added file(s)')
            clips += self.manual
        hint = ''
        if not self.dvr:
            try:
                if library.scan(('dvr',)):
                    hint = '   + Mini DVR card → see Mini DVR Import'
            except Exception:                                # noqa: BLE001
                pass
        seen, uniq = set(), []
        for c in clips:
            k = os.path.normcase(os.path.abspath(c))
            if k not in seen:
                seen.add(k); uniq.append(c)
        self.app.post(self._list, sid, uniq, labels, hint)

    def _list(self, sid, clips, labels, hint):
        if sid != self.scan_id:
            return
        self.source_txt.set(('  ·  '.join(labels) if labels else
                             'No card found - plug in your SD card / camcorder, or use Pick folder…') + hint)
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for c in clips:
            iid = self.tree.insert('', 'end', image=self.box_off, values=(os.path.basename(c), '', '', '', 'Normal',
                                                                 library.human_size(os.path.getsize(c)),
                                                                 'Checking…'))
            self.rows[iid] = {'path': c, 'info': None, 'fp': None, 'when': None, 'rotate': '0°', 'tick': False,
                              'state': 'checking', 'stamps': None}
        if not clips:
            self.helix.set_state('idle')
            self.heading.set('No clips yet')
            self.sub.set('Plug in a card or camcorder - GR8DVR spots it by itself.')
            self.bar.set(0)
            self._count()
            return
        threading.Thread(target=self._check, args=(sid, list(self.rows.items())), daemon=True).start()

    def _check(self, sid, items):
        n = len(items)
        for i, (iid, r) in enumerate(items, 1):
            if sid != self.scan_id:
                return
            name = os.path.basename(r['path'])
            self.app.post(self.sub.set, f'Checking {name} ({i} of {n})')
            self.app.post(self.bar.set, i / n)
            self.helix.progress = i / n
            try:
                r['fp'] = library.fingerprint(r['path'])
                r['info'] = convert.probe(r['path']) or {'duration': 0, 'video': False}
                r['when'] = library.recorded(r['path'], r['info'])
                if self.dvr:
                    r['stamps'] = looks.stamps(r['path'])
                prev = self.ledger.lookup(r['fp'])
                r['state'] = 'old' if prev else 'new'
                r['prev'] = prev
                r['tick'] = not prev
            except Exception as e:                           # noqa: BLE001
                r['state'], r['err'] = 'fail', str(e)
            self.app.post(self._row, sid, iid)
        self.app.post(self._checked, sid)

    def _checked(self, sid):
        if sid != self.scan_id:
            return
        new = sum(r['state'] == 'new' for r in self.rows.values())
        old = sum(r['state'] == 'old' for r in self.rows.values())
        self.helix.set_state('idle')
        self.heading.set(f'{new} new clip{"s" if new != 1 else ""} ready' if new else 'Nothing new on this card')
        self.sub.set(f'{old} already imported - left unticked.' if old else 'Press '
                     + ('Import' if self.dvr else 'Convert') + ' when you are ready.')
        self.bar.set(0)
        self.helix.progress = 0
        if not self.tree.selection() and self.rows:
            first = next((i for i, r in self.rows.items() if r['tick']), next(iter(self.rows)))
            self.tree.selection_set(first)
            self.tree.see(first)
        self._count()

    def _type(self, r):
        i = r['info'] or {}
        if self.dvr:
            st = r['stamps'] or []
            used = sorted({p for _, p in st})
            mode = '50p' if looks.fps_mode(st) else '25p'
            if not st:
                return 'AVI'
            return f'{mode} · look {used[0]}' if len(used) == 1 else f'{mode} · {len(used)} looks'
        if not i.get('video'):
            return 'audio'
        fmt = {'mpegts': 'AVCHD', 'mov,mp4,m4a,3gp,3g2,mj2': 'MP4/MOV', 'avi': 'AVI', 'dv': 'DV',
               'matroska,webm': 'MKV', 'mpeg': 'MPEG'}.get(i.get('format'), (i.get('format') or '?').split(',')[0].upper())
        h = i.get('height') or 0
        return f"{fmt} {h}{'i' if i.get('interlaced') else 'p'}"

    def _row(self, sid, iid):
        if sid != self.scan_id or iid not in self.rows:
            return
        r = self.rows[iid]
        i = r['info'] or {}
        status = {'new': 'New', 'checking': 'Checking…', 'fail': 'Unreadable'}.get(r['state'], r['state'])
        if r['state'] == 'old':
            status = 'Imported ' + datetime.datetime.fromisoformat(r['prev']['when']).strftime('%d %b')
        when = r['when'].strftime('%d %b %y  %H:%M') if r['when'] else '— no date'
        self.tree.item(iid, image=self.box_on if r['tick'] else self.box_off, tags=(r['state'],),
                       values=(os.path.basename(r['path']), when, hms(i.get('duration')), self._type(r),
                               ROT_NAMES[r['rotate']], library.human_size(os.path.getsize(r['path'])), status))
        self._count()
        if iid in self.tree.selection():
            self._explain()

    def _count(self):
        t = [r for r in self.rows.values() if r['tick']]
        size = sum(os.path.getsize(r['path']) for r in t if os.path.exists(r['path']))
        dur = sum((r['info'] or {}).get('duration') or 0 for r in t)
        self.status.set(f'{len(t)} ticked · {hms(dur)} · {library.human_size(size)}' if t else 'Nothing ticked yet.')

    # ------------------------------------------------ ticking
    def _tree_click(self, e):
        if self.tree.identify_region(e.x, e.y) == 'tree' or self.tree.identify_column(e.x) == '#0':
            iid = self.tree.identify_row(e.y)
            if iid:
                self.toggle([iid])
                return 'break'

    def toggle(self, iids):
        for iid in iids:
            r = self.rows.get(iid)
            if r and r['state'] not in ('checking', 'fail') and not self.busy:
                r['tick'] = not r['tick']
                self._row(self.scan_id, iid)
        return 'break'

    def tick_all(self, on):
        for iid, r in self.rows.items():
            if r['state'] not in ('checking', 'fail'):
                r['tick'] = on
                self._row(self.scan_id, iid)

    def tick_new(self):
        for iid, r in self.rows.items():
            r['tick'] = r['state'] == 'new'
            self._row(self.scan_id, iid)

    # ------------------------------------------------ preview / orientation / explanation
    def current(self):
        s = self.tree.selection()
        return (s[0], self.rows[s[0]]) if s and s[0] in self.rows else (None, None)

    def on_select(self):
        iid, r = self.current()
        self._explain()
        if r:
            if self.slider.value == 0:
                self.slider.set(0.3)
            self.load_preview()

    def _explain(self):
        iid, r = self.current()
        if not r:
            txt = 'Click a clip above to see exactly how it will be converted.'
        elif not r['info']:
            txt = 'Reading the clip…'
        else:
            name = self._out_name(r)
            if self.dvr:
                st = r['stamps'] or []
                segs = looks.segments([p for _, p in st]) if self.use_looks.get() else []
                used = ', '.join(f'{p} {looks.LOOKS[p][0]}' for p in sorted({p for _, _, p in segs})) or 'none'
                txt = (f"Weave both fields → {'50p smooth' if looks.fps_mode(st) else '25p cinematic'} "
                       f"(as recorded) · {'TV-style edge crop' if self.overscan.get() else 'full frame'} → "
                       f"768×576 4:3\nLooks: {used if self.use_looks.get() else 'off (original colours)'}"
                       f"{' · ' + ROT_NAMES[r['rotate']] if r['rotate'] != '0°' else ''}\n"
                       f"H.264 CRF 16, AAC 192 kbit/s 48 kHz, MP4\nSaved as: {name}_"
                       f"{'GR8DVR' if self.use_looks.get() else 'original'}.mp4")
            else:
                txt = convert.describe(r['info'], self.fmt.get(), self.quality.get(), r['rotate'],
                                       self.deint.get()).replace('\n', '  ·  ')
                txt += f'\nSaved as: {name}{convert.FORMATS[self.fmt.get()][0]}'
        self.explain.configure(state='normal')
        self.explain.delete('1.0', 'end')
        self.explain.insert('1.0', txt)
        self.explain.configure(state='disabled')

    def _out_name(self, r):
        return library.export_name(r['path'], r['when'])

    def on_scrub(self, v):
        iid, r = self.current()
        if r and r['info']:
            d = r['info'].get('duration') or 0
            self.timepos.configure(text=f'{hms(v * d)} / {hms(d)}')

    def turn(self, d):
        sel = [i for i in self.tree.selection() if i in self.rows]
        if not sel:
            return
        for iid in sel:
            r = self.rows[iid]
            r['rotate'] = ROT_STEPS[(ROT_STEPS.index(r['rotate']) + d) % 4]
            self._row(self.scan_id, iid)
        self.load_preview()

    def load_preview(self):
        iid, r = self.current()
        if not r:
            return
        self.canvas.itemconfigure('msg', text='Loading preview…')
        token = object()
        self.preview_job = token

        def work():
            info = r['info'] or convert.probe(r['path']) or {'duration': 0}
            t = self.slider.value * max(0.0, (info.get('duration') or 0) - 0.2)
            size = None
            if self.dvr:
                size = '256:192' if r['rotate'] in ('0°', '180°') else '144:192'
            png = (convert.preview_png(r['path'], t, r['rotate'], width=256, info=info, size=size)
                   if info.get('video') else b'')
            self.app.post(self.show_preview, token, png, info, t)
        threading.Thread(target=work, daemon=True).start()

    def show_preview(self, token, png, info, t):
        if token is not self.preview_job:
            return
        self.canvas.delete('frame')
        d = info.get('duration') or 0
        self.timepos.configure(text=f'{hms(t)} / {hms(d)}')
        if not png:
            self.canvas.itemconfigure('msg', text='No picture (audio only or unreadable)')
            return
        img = tk.PhotoImage(data=png)
        k = max(-(-img.height() // 192), -(-img.width() // 256))
        if k > 1:
            img = img.subsample(k, k)
        self.preview_img = img
        self.canvas.itemconfigure('msg', text='')
        self.canvas.create_image(128, 96, image=img, tags='frame')

    def play(self):
        iid, r = self.current()
        if not r:
            return
        vf = convert.ROTATIONS.get(r['rotate']) or 'null'
        if self.dvr:
            vf = 'scale=768:576,' + vf
        if shutil.which('ffplay'):
            subprocess.Popen(['ffplay', '-hide_banner', '-loglevel', 'error', '-autoexit', '-window_title',
                              os.path.basename(r['path']), '-vf', vf, r['path']],
                             **({'creationflags': 0x08000000} if os.name == 'nt' else {}))
        else:
            open_folder(r['path'])

    # ------------------------------------------------ converting
    def start(self):
        if self.busy:
            return
        jobs = [(iid, r) for iid, r in self.rows.items() if r['tick']]
        if not jobs:
            sound.play('error')
            return messagebox.showinfo('GR8DVR', 'Tick at least one clip first (click the box in front of it).')
        from gr8core import procs
        procs.reset()
        self.busy = True
        self.go.set_enabled(False)
        self.cancel_b.set_enabled(True)
        self.helix.set_state('busy')
        self.helix.progress = 0
        out = library.dated_dir(self.base.get())
        opts = dict(fmt=self.fmt.get(), quality=self.quality.get(), deint=self.deint.get(),
                    looks=self.use_looks.get(), overscan=self.overscan.get(), keep=self.keep576.get())
        threading.Thread(target=self._run, args=(jobs, out, opts), daemon=True).start()

    def cancel(self):
        if self.busy:
            from gr8core import procs
            procs.cancel()
            self.heading.set('Cancelling…')

    def _set_status(self, iid, text, tag=None):
        if iid in self.rows:
            vals = list(self.tree.item(iid, 'values'))
            vals[6] = text
            self.tree.item(iid, values=vals, **({'tags': (tag,)} if tag else {}))

    def _run(self, jobs, out, o):
        from gr8core import procs
        ok, errs, n = 0, [], len(jobs)
        os.makedirs(out, exist_ok=True)
        for k, (iid, r) in enumerate(jobs):
            name = os.path.basename(r['path'])
            self.app.post(self.heading.set, f'Converting {k + 1} of {n}…')
            self.app.post(self.sub.set, name)

            def prog(p, k=k, iid=iid):
                p = max(0.0, min(1.0, p))
                self.helix.progress = (k + p) / n
                self.app.post(self.bar.set, (k + p) / n)
                self.app.post(self._set_status, iid, f'Converting {int(p * 100)}%')
            prog(0)
            try:
                stem = self._out_name(r)
                if self.dvr:
                    import re
                    sys.stdout = _QWriter(lambda s: [prog(int(m) / 100 * 0.8) for m in re.findall(r'(\d+)%', s)[-1:]])
                    try:
                        outs = importer.import_clip(r['path'], out, use_looks=o['looks'], overscan=o['overscan'],
                                                    keep_576i=o['keep'],
                                                    out_name=self._free(out, stem, '_GR8DVR.mp4' if o['looks']
                                                                        else '_original.mp4'),
                                                    log=lambda m: prog(0.85) if 'grading' in m else None,
                                                    rotate=r['rotate'])
                    finally:
                        sys.stdout = sys.__stdout__
                else:
                    ext = convert.FORMATS[o['fmt']][0]
                    outs = [convert.convert(r['path'], out, o['fmt'], o['quality'], r['rotate'], o['deint'],
                                            on_progress=prog, name=self._free(out, stem, ext), info=r['info'])]
                self.ledger.add(r['fp'], r['path'], outs)
                r['state'], r['tick'] = 'done', False
                r['prev'] = {'when': datetime.datetime.now().isoformat()}
                ok += 1
                self.app.post(self._set_status, iid, '✓ Done', 'done')
                self.app.post(lambda iid=iid: self.tree.item(iid, image=self.box_off))
                if k < n - 1:
                    sound.play('tick')
            except procs.Cancelled:
                for iid2, _ in jobs[k:]:
                    self.app.post(self._set_status, iid2, 'Cancelled')
                break
            except Exception as e:                           # noqa: BLE001
                msg = str(e).strip().splitlines()[-1] if str(e).strip() else type(e).__name__
                errs.append(f'{name}: {msg}')
                self.app.post(self._set_status, iid, '✗ Failed', 'fail')
        self.app.post(self._done, ok, n, errs, out, procs.cancelled)

    @staticmethod
    def _free(out, stem, tail):
        """File stem that does not overwrite an earlier export: name, name (2), name (3)…"""
        s, n = stem, 2
        while os.path.exists(os.path.join(out, s + tail)):
            s, n = f'{stem} ({n})', n + 1
        return s

    def _done(self, ok, n, errs, out, cancelled):
        self.busy = False
        self.go.set_enabled(True)
        self.cancel_b.set_enabled(False)
        self._count()
        self.bar.set(ok / n if n else 0)
        if cancelled:
            self.helix.set_state('idle')
            self.heading.set('Cancelled')
            self.sub.set(f'{ok} of {n} finished before you cancelled.')
            return
        if errs:
            sound.play('error')
            self.helix.set_state('error', 25)
            self.heading.set(f'{ok} of {n} done - {len(errs)} problem{"s" if len(errs) > 1 else ""}')
            self.sub.set(errs[0][:90])
            messagebox.showwarning('GR8DVR', f'{ok} of {n} clip(s) saved in\n{out}\n\nProblems:\n'
                                   + '\n'.join(errs[:6]))
        else:
            sound.play('ok')
            self.helix.set_state('ok', 70)
            self.heading.set(f'All done! {ok} clip{"s" if ok != 1 else ""} saved')
            self.sub.set(out)


class _QWriter:
    """weave.py prints progress with \\r: forward every chunk."""
    def __init__(self, fn):
        self.fn, self.buf = fn, ''

    def write(self, s):
        for ch in s:
            if ch in '\r\n':
                if self.buf.strip():
                    self.fn(self.buf.strip())
                self.buf = ''
            else:
                self.buf += ch

    def flush(self):
        pass


# ---------------------------------------------------------------- firmware wizard tab
class FirmwareTab:
    def __init__(self, app, page):
        self.app = app
        base = vendor.bundled() or vendor.cached()
        self.vendor = tk.StringVar(value=base or '')
        self.vendor_ok = bool(base)
        self.card = tk.StringVar(value='')
        self.preset = tk.StringVar(value=self._look_label(0))
        self.fps = tk.IntVar(value=1)
        self.mode = tk.StringVar(value='try')
        self.agree = tk.BooleanVar(value=False)
        self.step = 0

        side = w.Bevel(page, 'sunken', bg=DK)
        side.pack(side='left', fill='y')
        self.sky = ArtScene(side.inner, 'sidebar.png', (216, 612), width=216, height=10)
        self.sky.pack(fill='y', expand=True)
        self.icon = tk.PhotoImage(file=asset('nautilus_dvr.png'))
        self.sky.create_image(108, 150, image=self.icon, tags=('icon', 'ui'))
        self.sky.create_text(109, 251, text='Mini DVR\nFirmware Builder', fill='#000000', font=F['bold'],
                             justify='center', tags=('label', 'ui'))
        self.sky.create_text(108, 250, text='Mini DVR\nFirmware Builder', fill=BEIGE, font=F['bold'],
                             justify='center', tags=('label', 'ui'))
        for k, i in zip((1, 0), self.sky.find_withtag('label')):     # below the prism, above the chip
            self.sky.place(i, 108 + k, 505 + k)
        self.bob = 0
        self._float()

        main = tk.Frame(page)
        main.pack(side='left', fill='both', expand=True, padx=(14, 0))
        self.title = tk.Label(main, text='', font=F['title'], anchor='w')
        self.title.pack(fill='x', pady=(2, 8))
        self.body = tk.Frame(main)
        self.body.pack(fill='both', expand=True)
        w.hline(main).pack(fill='x', pady=8)
        nav = tk.Frame(main)
        nav.pack(fill='x')
        self.stepl = tk.Label(nav, text='', fg=DIM)
        self.stepl.pack(side='left')
        self.next = w.Button(nav, 'Next >', self.go_next, width=110, default=True)
        self.next.pack(side='right')
        self.back = w.Button(nav, '< Back', self.go_back)
        self.back.pack(side='right', padx=(0, 2))
        self.steps = [self.s_welcome] + ([] if self.vendor_ok else [self.s_vendor]) + \
            [self.s_defaults, self.s_card, self.s_write, self.s_done]
        self.show()

    def _float(self):
        import math
        self.bob += 1
        self.sky.coords('icon', 108, self.sky.oy + 375 + round(math.sin(self.bob / 6) * 3))
        self.sky.after(80, self._float)

    @staticmethod
    def _look_label(n):
        return f'{n}  {looks.LOOKS[n][0]}' + ('  (no effect)' if n == 0 else '')

    # --- navigation
    def show(self):
        for c in self.body.winfo_children():
            c.destroy()
        self.steps[self.step]()
        n = len(self.steps) - 1
        self.stepl.configure(text='Welcome' if self.step == 0 else f'Step {self.step} of {n - 1}' if self.step < n else 'Finished')
        self.back.set_enabled(0 < self.step < n)
        cur = self.steps[self.step]
        label = {self.s_write: 'Write to card', self.s_done: 'Start over'}.get(cur, 'Next >')
        self.next.set_text(label)
        self.validate()

    def validate(self):
        cur = self.steps[self.step]
        ok = {self.s_vendor: self.vendor_ok, self.s_card: bool(self.card.get()) and os.path.isdir(self.card.get()),
              self.s_write: self.mode.get() != 'install' or self.agree.get()}.get(cur, True)
        self.next.set_enabled(ok)

    def go_back(self):
        self.step = max(0, self.step - 1); self.show()

    def go_next(self):
        cur = self.steps[self.step]
        if cur == self.s_write:
            return self.write()
        self.step = 0 if cur == self.s_done else self.step + 1
        self.show()

    def text(self, s, **kw):
        tk.Label(self.body, text=s, justify='left', anchor='w', wraplength=560, **kw).pack(fill='x', pady=(0, 8))

    # --- steps
    def s_welcome(self):
        self.title.configure(text='Welcome to the GR8DVR Firmware Builder')
        self.text('This wizard makes a personal GR8DVR firmware file for the small 3-button FPV "Mini DVR" '
                  '(53×33 mm, 400 mAh, MENU ◀ ▶ buttons) and puts it on its microSD card.')
        self.text('With GR8DVR your DVR records true 50i/60i fields (smooth like the camcorder), at the finest '
                  'quality, with 9 colour looks you pick live:')
        g = w.group(self.body, 'Buttons with GR8DVR')
        g.pack(fill='x', pady=(0, 8))
        for k, d in (('MENU', 'start / stop recording'), ('▶', 'next look 0 → 8 (the LED blinks the number)'),
                     ('◀', 'switch 60 fps smooth ⇄ 30 fps cinematic')):
            r = tk.Frame(g)
            r.pack(fill='x')
            tk.Label(r, text=k, font=F['bold'], width=7, anchor='w').pack(side='left')
            tk.Label(r, text=d, anchor='w').pack(side='left')
        self.text('You will need:\n  •  the DVR\'s microSD card and a card reader\n'
                  '  •  a fully charged DVR and a USB power source\n'
                  'That\'s it - everything else, including Eachine\'s original firmware it builds on, is inside GR8DVR.')
        r = tk.Frame(self.body)
        r.pack(fill='x')
        link(r, 'Install guide & FAQ on gr8success.xyz', URL_PAGE).pack(side='left')

    def s_vendor(self):
        self.title.configure(text='The original firmware')
        self.text('GR8DVR is built on top of Eachine\'s original firmware. It is fetched for you straight from '
                  'Eachine\'s official download and checked byte for byte - nothing to find or download yourself.')
        self.vmsg = tk.Label(self.body, text='', anchor='w', font=F['bold'], justify='left', wraplength=560)
        self.vmsg.pack(fill='x', pady=(4, 6))
        self.vbar = w.Progress(self.body, width=420, height=18)
        self.vbar.pack(anchor='w')
        r = tk.Frame(self.body)
        r.pack(fill='x', pady=(10, 0))
        self.retry = w.Button(r, 'Try again', self.fetch_vendor)
        self.retry.pack(side='left')
        w.Button(r, 'I have the file…', self.pick_vendor, width=110).pack(side='left', padx=6)
        w.Help(r, 'Offline or behind a firewall? Pick Eachine\'s CRESFW.BIN yourself. GR8DVR checks its '
                  'fingerprint (SHA-256), so a wrong or damaged file can never be turned into firmware.').pack(side='left')
        if self.vendor_ok and self.vendor.get():
            self.vbar.set(1)
            self.vmsg.configure(text='✓ Eachine original firmware ready and verified.', fg=OKC)
        else:
            self.fetch_vendor()

    def fetch_vendor(self):
        if getattr(self, 'fetching', False):
            return
        self.fetching = True
        self.vmsg.configure(text='Getting Eachine\'s original firmware…', fg=DK)
        self.retry.set_enabled(False)

        def work():
            try:
                p = vendor.fetch(on_progress=lambda f: self.app.post(self._vprog, f))
                self.app.post(self._vdone, p, None)
            except Exception as e:                       # noqa: BLE001
                self.app.post(self._vdone, None, str(e))
        threading.Thread(target=work, daemon=True).start()

    def prefetch(self):
        """Fetch quietly in the background the first time the tab is opened."""
        if not self.vendor_ok and vendor.cached():
            self.vendor.set(vendor.CACHE); self.vendor_ok = True
        elif not self.vendor_ok and not getattr(self, 'fetching', False):
            self.fetching = True

            def work():
                try:
                    p = vendor.fetch()
                    self.app.post(self._vdone, p, None)
                except Exception as e:                   # noqa: BLE001
                    self.app.post(self._vdone, None, str(e))
            threading.Thread(target=work, daemon=True).start()

    def _vprog(self, f):
        if self.steps[self.step] == self.s_vendor and self.vbar.winfo_exists():
            self.vbar.set(f)

    def _vdone(self, path, err):
        self.fetching = False
        if path:
            self.vendor.set(path); self.vendor_ok = True
        on_step = self.steps[self.step] == self.s_vendor and self.vmsg.winfo_exists()
        if on_step:
            self.retry.set_enabled(True)
            if path:
                self.vbar.set(1)
                self.vmsg.configure(text='✓ Eachine original firmware ready and verified.', fg=OKC)
            elif not self.vendor_ok:
                self.vbar.set(0)
                self.vmsg.configure(text=f'✗ {err}', fg='#a8321c')
                sound.play('error')
        self.validate()

    def pick_vendor(self):
        p = filedialog.askopenfilename(title="Eachine's original CRESFW.BIN",
                                       filetypes=[('Firmware', '*.BIN *.bin'), ('All files', '*.*')])
        if p:
            self.vendor.set(p)
            self._check_vendor(p)

    def _check_vendor(self, p):
        try:
            firmware.check_vendor(p)
            self.vendor_ok = True
            self.vmsg.configure(text='✓ Original Eachine firmware recognised.', fg=OKC)
        except firmware.FirmwareError as e:
            self.vendor_ok = False
            self.vmsg.configure(text=f'✗ {e}', fg='#a8321c')
            return
        self.vbar.set(1)
        self.validate()

    def s_defaults(self):
        self.title.configure(text='Your start-up settings')
        self.text('Choose what the DVR does right after you switch it on. You can always change it with the '
                  'buttons while filming - this only sets the starting point.')
        g = w.group(self.body, 'Start with this look')
        g.pack(fill='x', pady=(0, 8))
        r = tk.Frame(g)
        r.pack(fill='x')
        w.Dropdown(r, self.preset, [self._look_label(n) for n in range(9)], width=30,
                   command=self._look_desc).pack(side='left')
        w.Help(r, 'Looks are colour styles. They are applied when you import with GR8DVR (Mini DVR Import tab), '
                  'so the raw recording always stays clean - you can turn looks off at import time.').pack(
            side='left', padx=6)
        self.look_desc = tk.Label(g, text='', anchor='w', fg=DIM, wraplength=520, justify='left')
        self.look_desc.pack(fill='x', pady=(4, 0))
        self._look_desc()
        g = w.group(self.body, 'Start with this frame rate')
        g.pack(fill='x')
        for v, t, tip in ((1, '60 fps smooth (50 fields/s PAL) - recommended',
                           'Every field becomes its own frame: motion looks exactly like the camcorder.'),
                          (0, '30 fps cinematic (25 frames/s PAL)', 'Fields are combined into full frames: a calmer, '
                           'film-like look with half the frames.')):
            r = tk.Frame(g)
            r.pack(fill='x', pady=1)
            w.Check(r, t, self.fps, radio_value=v).pack(side='left')
            w.Help(r, tip).pack(side='left', padx=6)

    def _look_desc(self):
        n = int(self.preset.get().split()[0])
        self.look_desc.configure(text=looks.LOOKS[n][1])

    def s_card(self):
        self.title.configure(text='The SD card')
        self.text('Put the DVR\'s microSD card into your computer and pick its drive. Your recordings on the '
                  'card are not touched.')
        cards = guess_cards()
        if cards and not self.card.get():
            self.card.set(cards[0])
        r = tk.Frame(self.body)
        r.pack(fill='x')
        w.Field(r, self.card, width=50).pack(side='left', fill='x', expand=True)
        w.Button(r, 'Browse…', self.pick_card).pack(side='left', padx=6)
        w.Help(r, 'Pick the card\'s top folder (for example E:\\ on Windows, /Volumes/NO NAME on a Mac). Old GR8DVR / ADJUST.BIN / CRESFW.BIN files on '
                  'it are replaced. FAT32 cards up to 32 GB work best.').pack(side='left')
        if cards:
            tk.Label(self.body, text='Found: ' + ', '.join(cards), fg=DIM, anchor='w').pack(fill='x', pady=6)

    def pick_card(self):
        d = filedialog.askdirectory(title='The DVR\'s SD card')
        if d:
            self.card.set(d)
        self.validate()

    def s_write(self):
        self.title.configure(text='Try it or install it')
        self.text(f'Start-up look: {self.preset.get().strip()}    ·    Frame rate: '
                  f'{"60 fps smooth" if self.fps.get() else "30 fps cinematic"}\nCard: {self.card.get()}')
        opts = (('try', 'Try first (recommended)', 'Runs GR8DVR once from memory. Nothing is installed - switch the '
                 'DVR off and on again and you are back to normal. Perfect to test.'),
                ('install', 'Install permanently', 'Flashes GR8DVR into the DVR. It then starts with GR8DVR every '
                 'time, no card file needed.'),
                ('restore', 'Restore the original Eachine firmware', 'Flashes the untouched Eachine firmware back.'))
        for v, t, tip in opts:
            r = tk.Frame(self.body)
            r.pack(fill='x', pady=2)
            w.Check(r, t, self.mode, radio_value=v, command=self.show).pack(side='left')
            w.Help(r, tip).pack(side='left', padx=6)
        if self.mode.get() in ('install', 'restore'):
            g = w.group(self.body, 'Before you flash')
            g.pack(fill='x', pady=(8, 0))
            tk.Label(g, justify='left', anchor='w', wraplength=540, text=(
                '•  Charge the battery fully AND keep USB power connected.\n'
                '•  Never switch off while the red LED blinks (30-60 seconds).\n'
                '•  When it goes quiet, wait 10 seconds, then switch off.\n'
                'A power cut during flashing can only be repaired with an SPI programmer.')).pack(fill='x')
            if self.mode.get() == 'install':
                w.Check(g, 'I understand and flash at my own risk (see Help ▸ License)', self.agree,
                        command=self.validate).pack(anchor='w', pady=(6, 0))

    def write(self):
        mode = self.mode.get()
        n = int(self.preset.get().split()[0])
        try:
            self.name = firmware.write(self.card.get(), self.vendor.get(), mode, preset=n, fps=self.fps.get())
        except firmware.FirmwareError as e:
            return messagebox.showerror('GR8DVR', str(e))
        except OSError as e:
            return messagebox.showerror('GR8DVR', f'Could not write to the card:\n{e}')
        self.step = len(self.steps) - 1
        self.show()

    def s_done(self):
        mode = self.mode.get()
        self.title.configure(text='Done! ' + {'try': 'Ready to try', 'install': 'Ready to install',
                                              'restore': 'Ready to restore'}[mode])
        self.text(f'{self.name} was written to {self.card.get()} and checked byte by byte.')
        steps = {
            'try': ['Eject the card safely and put it in the DVR.',
                    'Switch on. GR8DVR loads once (the DVR deletes ADJUST.BIN by itself).',
                    'MENU = record  ·  ▶ = next look  ·  ◀ = 60/30 fps.',
                    'Happy? Run this wizard again and choose Install permanently.'],
            'install': ['Eject the card safely and put it in the DVR.', 'Connect USB power, battery full.',
                        'Switch on: the red LED blinks while flashing (30-60 s).',
                        'When it goes quiet: wait 10 s, switch off, then delete CRESFW.BIN from the card.'],
            'restore': ['Eject the card safely and put it in the DVR.', 'Connect USB power, battery full.',
                        'Switch on and wait until the LED stops blinking, then 10 s more.',
                        'Switch off and delete CRESFW.BIN from the card.']}[mode]
        for i, s in enumerate(steps, 1):
            r = tk.Frame(self.body)
            r.pack(fill='x', pady=2)
            tk.Label(r, text=f'{i}.', font=F['bold'], width=3, anchor='w').pack(side='left')
            tk.Label(r, text=s, anchor='w', justify='left', wraplength=520).pack(side='left')
        r = tk.Frame(self.body)
        r.pack(fill='x', pady=(14, 0))
        tk.Label(r, text='Enjoying GR8DVR?').pack(side='left')
        w.Button(r, 'Donate…', lambda: webbrowser.open(URL_DONATE)).pack(side='left', padx=6)
        w.Button(r, 'Visit the store', lambda: webbrowser.open(URL_SHOP), width=100).pack(side='left')


# ---------------------------------------------------------------- about tab
class AboutTab:
    """The key illustration, slightly darkened; text sits on the calm area right of the nautilus."""
    X, Y, WRAP = 532, 140, 410                                   # text block, in picture coordinates (970 x 580)

    def __init__(self, app, page):
        b = w.Bevel(page, 'sunken', bg=DK)
        b.pack(fill='both', expand=True)
        self.scene = sc = ArtScene(b.inner, 'about.png', (970, 580))
        sc.pack(fill='both', expand=True)
        self.logo = tk.PhotoImage(file=asset('logo_about.png'))
        self.buzco = tk.PhotoImage(file=asset('buzco.png'))
        X, y = self.X, self.Y
        sc.place(sc.create_image(0, 0, image=self.logo, anchor='nw', tags='ui'), X, y)
        lines = [(f'Version {VERSION}  ·  Freeware', F['title']),
                 ('Made in Lisbon by Buzco · GR8 Success.', F['bold']),
                 ('Built for MiniDV lovers capturing with a pocket DVR.', F['ui']),
                 ('Base firmware: Eachine ProDVR firmware (c) Eachine - included unmodified, all rights theirs.', F['ui']),
                 ('Firmware research: open-minidvr-50i by eonflux7 (MIT).', F['ui']),
                 ('Video engine: FFmpeg (GPL).', F['ui'])]
        y += self.logo.height() + 16
        for i, (t, fnt) in enumerate(lines):
            for dx, col in ((1, '#000000'), (0, BEIGE)):
                it = sc.create_text(0, 0, text=t, anchor='nw', font=fnt, fill=col, width=self.WRAP, tags='ui')
                sc.place(it, X + dx, y + dx)
            sc.update_idletasks()
            bb = sc.bbox(it)
            y += (bb[3] - bb[1] if bb else 18) + (12 if i == 0 else 5)
        btns = tk.Frame(sc, bg=DK)
        for txt, cmd, bold in (('Donate…', lambda: webbrowser.open(URL_DONATE), True),
                               ('Buzco store', lambda: webbrowser.open(URL_SHOP), False),
                               ('Website', lambda: webbrowser.open(URL_PAGE), False),
                               ('License…', app.show_license, False)):
            w.Button(btns, txt, cmd, width=96, bold=bold).pack(side='left', padx=(0, 6))
        sc.place(sc.create_window(0, 0, window=btns, anchor='nw', tags='ui'), X, y + 12)
        bz = sc.place(sc.create_image(0, 0, image=self.buzco, anchor='nw', tags='ui'), 28, 26)
        sc.tag_bind(bz, '<Button-1>', lambda e: webbrowser.open(URL_SITE))


def _checkbox_img(on):
    """13x13 Win95 checkbox as a PhotoImage (for the clip table)."""
    img = tk.PhotoImage(width=16, height=13)
    img.put(FIELD, to=(0, 0, 16, 13))
    img.put(SH, to=(0, 0, 13, 1)); img.put(SH, to=(0, 0, 1, 13))
    img.put(DK, to=(1, 1, 12, 2)); img.put(DK, to=(1, 1, 2, 12))
    img.put(LT, to=(1, 11, 12, 12)); img.put(LT, to=(11, 1, 12, 12))
    img.put(HI, to=(0, 12, 13, 13)); img.put(HI, to=(12, 0, 13, 13))
    if on:
        for x, y in ((3, 5), (4, 6), (5, 7), (6, 6), (7, 5), (8, 4), (9, 3)):
            img.put(DK, to=(x, y, x + 1, y + 3))
    return img


def _ttk_style(root):
    s = ttk.Style(root)
    s.theme_use('clam')
    s.configure('Treeview', background=FIELD, fieldbackground=FIELD, foreground=DK, font=F['ui'], rowheight=19,
                borderwidth=0)
    s.map('Treeview', background=[('selected', ACC)], foreground=[('selected', FIELD)])
    s.configure('Treeview.Heading', background=FACE, foreground=DK, font=F['ui'], relief='raised', borderwidth=2,
                lightcolor=HI, darkcolor=SH, bordercolor=DK)
    s.map('Treeview.Heading', background=[('active', FACE)])
    s.configure('Vertical.TScrollbar', background=FACE, troughcolor=LT, bordercolor=DK, arrowcolor=DK,
                lightcolor=HI, darkcolor=SH, gripcount=0, arrowsize=16)


def main():
    root = tk.Tk()
    root.withdraw()
    w.init_fonts(root)
    try:                                                   # window + taskbar icon
        if os.name == 'nt':
            root.iconbitmap(default=asset('gr8dvr.ico'))
        root._icons = [tk.PhotoImage(file=asset(f'icon_{z}.png')) for z in (256, 48, 32, 16)]
        root.iconphoto(True, *root._icons)
    except tk.TclError:
        pass

    def start():
        App(root)
        root.deiconify()
    if '--no-splash' in sys.argv:
        start()
    else:
        Splash(root, start)
    root.mainloop()


if __name__ == '__main__':
    main()
