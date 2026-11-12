"""Mini-Project 02 video, told in the order of REPORT.md (see STORYBOARD.md).

One world for the whole film: the process's memory as a ribbon of blocks across the
top, the kernel as a dark band across the bottom, a scoreboard top right, and one gold
fault token that travels between them. No arrows. Every timing is in beats of a 96 BPM
grid, so music and voice can be laid on later. Numbers come from results/. Run:
    manimgx render story_scene.py Story
"""

import math
import random
import unicodedata

from manimgx.audio.sound import Sound
from pathlib import Path

import manimgx as m


m.config.background_color = "#0A1020"
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"  # credits: assets/SOURCES.md
SFX = ASSETS / "sfx"  # Kenney Interface Sounds (CC0), see assets/SOURCES.md
KENNEY = {"typing": "tick_002.ogg", "tick": "tick_002.ogg", "click": "select_001.ogg", "enter": "click_002.ogg", "thud": "drop_002.ogg",
          "chime": "confirmation_001.ogg", "whoosh": "maximize_004.ogg", "miss": "error_004.ogg",
          "open": "open_001.ogg", "close": "close_001.ogg", "switch": "switch_002.ogg", "toggle": "toggle_001.ogg",
          "pluck": "pluck_001.ogg", "glass": "glass_001.ogg", "scroll": "scroll_001.ogg", "swoosh": "minimize_003.ogg",
          "line": "click_005.ogg", "bong": "bong_001.ogg"}

INK, MUTED = "#EAF0F7", "#8DA2BA"
BLUE, GOLD, GREEN, RED, GREY = "#4DA3FF", "#F5B841", "#5BD19A", "#FF6B6B", "#6B7A90"
PANEL, BAND = "#121C2F", "#05080F"
B = 0.43  # one beat (~140 BPM); change this alone to retime, keep the film >= 7 min
BAR = 4 * B
SUB_FONTS = HERE / "assets" / "fonts"  # LINE Seed (OFL), see assets/SOURCES.md
TH_CPS = 12.0  # spoken Thai, base characters per second (marks above/below not counted); tune to the real voice
TH_GAP = 0.2  # breath between subtitle lines, seconds
TOP_Y = 3.55  # the short English key line sits top centre
RIBBON_Y, BAND_Y, CAPTION_Y = 1.25, -2.0, -3.4

# results/e1a-report-sleep.txt: the 30 regions of `sleep`, in address order
REGIONS = [
    ("file", 20), ("file", 4), ("file", 4), ("heap", 132),
    ("file", 2988), ("file", 356), ("file", 1640), ("file", 76), ("file", 12), ("file", 8),
    ("anon", 48), ("file", 156), *[("file", 4)] * 10, ("file", 28), ("file", 4),
    ("anon", 8), ("special", 8), ("special", 4), ("file", 8), ("file", 8), ("stack", 132),
]
MEMBERS = [  # order as on the report cover
    ("67070501003", "Guntee Doungmanee"), ("67070501016", "Drarun Yookphan"),
    ("67070501027", "Natthawat Primsirikunawut"), ("67070501037", "Rattathamnoon Buranapattana"),
    ("67070501042", "Wisit Suwannao"), ("67070501045", "Supawit Marayat"),
    ("67070501067", "Polwarit Watthanahemmarat"),
]
GROUP = "Ta Nai Tum Chuoy Soo"
KIND_COLOR = {"file": BLUE, "anon": GOLD, "heap": GREEN, "stack": GREEN, "special": GREY}


def load_script(path: Path) -> dict[str, list[str]]:
    """script_th.md: '## scene' headers, '- line' subtitle lines."""
    acts, key = {}, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            key = line[3:].strip()
            acts[key] = []
        elif line.startswith("- ") and key:
            acts[key].append(line[2:].strip())
    return acts


def speak_time(text: str) -> float:
    n = sum(1 for ch in text if unicodedata.category(ch) != "Mn")
    return max(1.0, n / TH_CPS)


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def beats(n: float) -> float:
    return n * B


def units(mob: m.Mobject) -> list[m.Mobject]:
    """The pieces an animation treats as one: each text, and each shape that holds no text."""
    if isinstance(mob, m.Text) or not any(isinstance(s, m.Text) for s in mob.get_family()):
        return [mob]
    return [u for sub in mob.submobjects for u in units(sub)]


def ribbon_blocks(regions, y=RIBBON_Y, width=12.0, height=0.6) -> m.VGroup:
    """One block per VMA, in address order; widths on a log scale so 4 KB and 3 MB both show."""
    w = [0.3 + math.log10(kb) for _, kb in regions]
    s = width / sum(w)
    blocks = [
        m.Rectangle(width=wi * s * 0.94, height=height, stroke_width=0, fill_color=KIND_COLOR[k], fill_opacity=0.9)
        for (k, _), wi in zip(regions, w)
    ]
    return m.VGroup(*blocks).arrange(m.RIGHT, buff=width * 0.004).move_to([0, y, 0])


class Story(m.ThreeDScene):
    def construct(self) -> None:
        random.seed(333)  # the shuffled page order in E3 is the same on every render
        self.caption_mob = None
        self.add(m.SunLight(4 * m.UP + 3 * m.OUT), m.AmbientLight(intensity=0.35))
        self.set_camera_orientation(phi=0, theta=-90 * m.DEGREES)
        self.subtitles_start()
        music = next(iter(sorted(SFX.glob("music.*"))), None)  # drop your own licensed track in as assets/sfx/music.*
        if music:  # looped with 2 s crossfades to cover the whole film
            track = Sound(music).gain(-10).fade_in(2.0).fade_out(2.0)
            length = float(track.duration) - 2.0
            for k in range(int(460 / length) + 1):
                self.add_sound(track, time_offset=k * length)
        for key in ("opening", "analogies"):
            self.speak(key)
            getattr(self, key)()
            self.hold()
        for label, act in [("1 · Goal", self.goal), ("2 · What a page fault is", self.background),
                           ("4.1 · Counting regions", self.regions_walk), ("4.2 · Counting faults", self.fault_counting),
                           ("4.5 · Watching it run", self.demo), ("6 · Experiments", self.experiments),
                           ("7 · Checks and findings", self.checks), ("9 · Summary", self.ending)]:
            self.chapter(label)
            self.speak(act.__name__)
            act()
            self.hold()
        self.write_srt()

    # ---- Thai subtitles: a clock driven by frame time; each scene waits for its own speech ----

    def subtitles_start(self):
        self.script = load_script(HERE / "script_th.md")
        self.sub_clock, self.sub_end, self.cues = 0.0, 0.0, []
        self.strip = m.Rectangle(width=14.4, height=0.95, stroke_width=0, fill_color="#000000", fill_opacity=0)
        self.strip.move_to([0, -3.38, 0])
        self.sub = m.VGroup()
        self.pin(self.strip)

        def tick(mob, dt):
            self.sub_clock += dt
            cur = next((c for c in self.cues if c[0] <= self.sub_clock < c[1]), None)
            if cur is None:
                mob.submobjects = []
                self.strip.set_fill(opacity=0)
                return
            fade = min(1.0, (self.sub_clock - cur[0]) / 0.15, (cur[1] - self.sub_clock) / 0.1)  # quick swap, no Write
            cur[3].set_opacity(fade)
            mob.submobjects = [cur[3]]
            self.strip.set_fill(opacity=0.55 * fade)
        self.sub.add_updater(tick)
        self.add(self.strip, self.sub)

    def sub_text(self, text):
        """One line, one font: every subtitle is set in LINE Seed JP, Thai included (Thai glyphs fall back to Noto Sans Thai)."""
        t = m.Text(text, font="LINE Seed JP", font_paths=[SUB_FONTS], font_size=26, color=INK)
        if t.width > 12.6:
            t.scale_to_fit_width(12.6)
        t.move_to([0, -3.38, 0])
        self.pin(t)
        return t

    def speak(self, key):
        start = max(self.sub_clock, self.sub_end)
        for line in self.script.get(key, []):
            d = speak_time(line)
            self.cues.append((start, start + d, line, self.sub_text(line)))
            start += d + TH_GAP
        self.sub_end = start

    def hold(self):
        """The picture never runs ahead of the voice: wait out the rest of this scene's lines."""
        if self.sub_end - self.sub_clock > 0.05:
            self.wait(self.sub_end - self.sub_clock)

    def write_srt(self):
        rows = [f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n" for i, (a, b, txt, _) in enumerate(self.cues, 1)]
        (HERE / "Story.th.srt").write_text("\n".join(rows), encoding="utf-8")

    def sfx(self, name: str, gain: float = -8, trim: float | None = None, fade: float = 0.0):
        """A sound effect at the current film time: call it just before the play it belongs to."""
        snd = Sound(SFX / KENNEY[name])
        if trim is not None:
            snd = snd.trim(0, trim)
        if fade:
            snd = snd.fade_out(fade)
        self.add_sound(snd.gain(gain + 2))  # effects sit 2 dB above their nominal level

    def burst(self, name: str, n: int, span: float, gain: float = -12):
        """n copies of a sound spread evenly over span seconds, from now: one per item that appears."""
        for k in range(n):
            self.add_sound(Sound(SFX / KENNEY[name]).gain(gain + 2), time_offset=k * span / max(1, n))

    def move_camera(self, *args, **kwargs):
        self.sfx("swoosh", -12)  # every camera move has a soft swoosh
        super().move_camera(*args, **kwargs)

    def chapter(self, label: str):
        """A small chapter tag, top left, rewritten in place; the camera carries the cut."""
        tag = m.Text(label, font_size=20, color=MUTED).to_corner(m.UL, buff=0.35)
        self.pin(tag)
        old = getattr(self, "tag", None)
        self.sfx("whoosh", -6)
        self.play(*([self.hide(old, run_time=beats(1))] if old else []), m.Write(tag, run_time=beats(2)))
        self.tag = tag

    def band_in(self):
        self.sfx("open", -10) if not self.band_on else None
        if not self.band_on:
            self.play(m.FadeIn(self.band), m.Create(self.band_edge), m.FadeIn(self.band_lab), self.tux.animate.move_to(self.TUX_BAND), run_time=beats(2))
            self.band_on = True

    def band_out(self):
        self.sfx("close", -12) if self.band_on else None
        if self.band_on:
            self.play(m.FadeOut(self.band), m.FadeOut(self.band_edge), m.FadeOut(self.band_lab), self.tux.animate.move_to(self.TUX_DOCK), run_time=beats(2))
            self.band_on = False

    # ---- appearing and leaving: text is written, shapes fade ------------------

    def show(self, *mobs, run_time=None, shift=None):
        anims = []
        for u in (u for mob in mobs for u in units(mob)):
            if isinstance(u, m.Text):
                anims.append(m.Write(u, run_time=run_time or BAR))
            elif shift is None:
                anims.append(m.FadeIn(u, run_time=run_time or beats(2)))
            else:
                anims.append(m.FadeIn(u, shift=shift, run_time=run_time or beats(2)))
        return m.AnimationGroup(*anims)

    def hide(self, *mobs, run_time=None):
        anims = []
        for u in (u for mob in mobs for u in units(mob)):
            if isinstance(u, m.Text):
                anims.append(m.Unwrite(u, run_time=run_time or beats(2), remover=True))
            else:
                anims.append(m.FadeOut(u, run_time=run_time or beats(2)))
        return m.AnimationGroup(*anims)

    def pin(self, *mobs):
        self.camera.add_fixed_in_frame_mobjects(*mobs)

    def cap(self, text: str, bars: int = 2) -> None:
        """One caption line: written on a downbeat, held for the rest of its bars."""
        line = m.Text(text, font_size=20, color=MUTED)
        if line.width > 6.2:
            line.scale_to_fit_width(6.2)
        line.move_to([-0.25, TOP_Y, 0])
        self.add_subcaption(text, bars * BAR)
        self.pin(line)
        anims = [m.Write(line, run_time=beats(2))]
        if self.caption_mob is not None:  # the old line slides up and out while the new one writes in
            anims.append(m.FadeOut(self.caption_mob, shift=m.UP * 0.2, run_time=beats(1)))
        self.play(*anims, run_time=beats(2))
        self.caption_mob = line
        self.wait(max(0.0, bars * BAR - beats(2)))

    def clear(self) -> None:
        if self.caption_mob is not None:
            self.play(self.hide(self.caption_mob, run_time=beats(1)))
            self.caption_mob = None

    def live(self, make):
        """Write a text in, then let it follow its value."""
        still = make()
        self.play(self.show(still, run_time=beats(2)))
        self.remove(still)
        mob = m.always_redraw(make)
        self.add(mob)
        return mob

    def freeze(self, mob, make):
        self.remove(mob)
        still = make()
        self.add(still)
        return still

    # ---- a compact terminal: a command is typed, Enter is pressed, then the visual it starts plays ----

    def term_open(self, pos, width=6.4, rows=3, title="lima-cpe333: ~/mini-project-02"):
        h = 0.36 + rows * 0.3 + 0.16
        win = m.RoundedRectangle(corner_radius=0.1, width=width, height=h, stroke_color=MUTED, stroke_width=1,
                                 fill_color="#03060C", fill_opacity=1).move_to(pos)
        bar = m.Rectangle(width=width - 0.06, height=0.28, stroke_width=0, fill_color=PANEL, fill_opacity=1)
        bar.move_to(win.get_top() + m.DOWN * 0.17)
        dots = m.VGroup(*[m.Dot(radius=0.05, color=c) for c in (RED, GOLD, GREEN)]).arrange(m.RIGHT, buff=0.08)
        dots.move_to(bar).align_to(bar, m.LEFT).shift(m.RIGHT * 0.15)
        ttl = m.Text(title, font_size=13, color=MUTED).move_to(bar)
        self.pin(win, bar, dots, ttl)
        self.sfx("open", -10)
        self.play(m.FadeIn(win, shift=m.UP * 0.2), m.FadeIn(bar, shift=m.UP * 0.2), m.FadeIn(dots), m.Write(ttl), run_time=beats(1))
        return {"g": [win, bar, dots, ttl], "x": win.get_left()[0] + 0.2, "y": bar.get_bottom()[1] - 0.2}

    def term_cmd(self, t, cmd, size=16):
        prompt = m.Text("$", font_size=size, color=GREEN)
        prompt.shift([t["x"] - prompt.get_left()[0], t["y"] - prompt.get_y(), 0])
        line = m.Text(cmd, font_size=size, color=INK).next_to(prompt, m.RIGHT, buff=0.12)
        cur = m.Rectangle(width=0.09, height=0.2, stroke_width=0, fill_color=INK, fill_opacity=0.9).next_to(prompt, m.RIGHT, buff=0.12)
        self.pin(prompt, line, cur)
        self.play(m.Write(prompt), m.FadeIn(cur), run_time=beats(0.5))
        dur = beats(max(1.5, len(cmd) / 16))
        for k in range(int(dur / 0.07)):  # one soft key tick per ~70 ms while the command types
            self.add_sound(Sound(SFX / KENNEY["typing"]).gain(-14 + random.uniform(-3, 0)), time_offset=k * 0.07)
        self.play(m.Write(line, rate_func=m.linear), cur.animate.next_to(line, m.RIGHT, buff=0.05),
                  run_time=beats(max(1.5, len(cmd) / 16)), rate_func=m.linear)  # typed left to right
        self.sfx("enter", -6)  # Enter
        self.play(cur.animate.set_fill(GOLD), m.Flash(cur, color=GOLD, flash_radius=0.18, line_length=0.1), run_time=beats(0.5))  # Enter
        self.remove(cur)
        t["g"] += [prompt, line]
        t["y"] -= 0.3

    def term_out(self, t, lines, color=MUTED, size=15):
        outs = []
        for txt in lines:
            o = m.Text(txt, font_size=size, color=color)
            o.shift([t["x"] - o.get_left()[0], t["y"] - o.get_y(), 0])
            t["y"] -= 0.3
            outs.append(o)
        self.pin(*outs)
        self.burst("line", len(outs), beats(1 + 0.5 * len(outs)), -12)
        self.play(m.LaggedStart(*[m.Write(o) for o in outs], lag_ratio=0.5), run_time=beats(1 + 0.5 * len(outs)))
        t["g"] += outs

    def term_close(self, t):
        self.sfx("close", -12)
        return self.hide(*t["g"], run_time=beats(1))

    def token(self, pos, color=GOLD):
        tok = m.Square(0.24, fill_color=color, fill_opacity=1, stroke_width=0).move_to(pos)
        trail = m.TracedPath(tok.get_center, stroke_color=color, stroke_width=3, dissipating_time=0.5)
        self.add(trail, tok)
        return tok, trail

    def code(self, lines, pos, size=22) -> m.VGroup:
        texts = m.VGroup(*[m.Text(t, font_size=size, color=INK) for t in lines])
        texts.arrange(m.DOWN, buff=0.14, aligned_edge=m.LEFT)
        panel = m.RoundedRectangle(corner_radius=0.12, width=texts.width + 0.6, height=texts.height + 0.45,
                                   stroke_color=MUTED, stroke_width=1, fill_color=PANEL, fill_opacity=0.95)
        texts.move_to(panel)
        return m.VGroup(panel, texts).move_to(pos)

    def run_line(self, block, i, *effects, bars=1):
        """Bring code line i in (or light it), dim the others, and play its effect on the same beat."""
        self.sfx("line", -12)
        lines = block[1]
        anims = [*effects]
        for j, t in enumerate(lines):
            if j == i:
                anims.append(m.Write(t, run_time=beats(2)) if t not in self.mobjects else t.animate.set_opacity(1))
            elif t in self.mobjects:
                anims.append(t.animate.set_opacity(0.3))
        self.play(*anims, run_time=bars * BAR)

    # ---- the shared world -------------------------------------------------------

    def build_world(self):
        self.band = m.Rectangle(width=14.4, height=1.6, stroke_width=0, fill_color=BAND, fill_opacity=1).move_to([0, BAND_Y, 0])
        self.band_edge = m.Line([-7.2, BAND_Y + 0.8, 0], [7.2, BAND_Y + 0.8, 0], color=BLUE, stroke_width=1.5, stroke_opacity=0.5)
        self.TUX_DOCK, self.TUX_BAND = [6.65, -3.55, 0], [-6.5, BAND_Y + 0.45, 0]
        self.tux = m.ImageMobject(str(ASSETS / "tux" / "Tux-on-disc.png")).scale_to_fit_height(0.45).move_to(self.TUX_DOCK)
        self.pin(self.tux)  # always on screen: docked bottom right, or inside the kernel band
        self.band_lab = m.Text("inside Linux (the kernel)", font_size=18, color=BLUE).move_to([-4.85, BAND_Y + 0.45, 0])
        self.band_on = False

    def scoreboard(self, title: str):
        """Four slots top right. Each value is -1 until the story earns it."""
        self.vals = {k: m.ValueTracker(-1) for k in ("regions", "size", "minor", "major")}
        fmt = {"regions": lambda v: f"{v:,.0f}", "size": lambda v: f"{v / 1024:.1f} MB" if v >= 1024 else f"{v:,.0f} KB",
               "minor": lambda v: f"{v:,.0f}", "major": lambda v: f"{v:,.0f}"}
        x0, y0 = 4.0, 3.55
        self.board_title = m.Text(title, font_size=20, color=MUTED).move_to([5.2, y0, 0])
        self.matched = set()
        labels, values = [], []
        for i, k in enumerate(self.vals):
            y = y0 - 0.38 * (i + 1)
            lab = m.Text(k, font_size=20, color=MUTED).move_to([x0, y, 0])
            lab.add_updater(lambda l, *_, k=k: l.set_opacity(0 if self.vals[k].get_value() < 0 else 1))  # a row appears once it has a value
            labels.append(lab)

            def make(k=k, y=y):
                v = self.vals[k].get_value()
                if v < 0:
                    return m.VGroup()
                return m.Text(fmt[k](v), font_size=22, color=GREEN if k in self.matched else INK).move_to([6.0, y, 0])
            values.append(make)
        self.board_labels = m.VGroup(*labels)
        self.board_makes = values
        self.pin(self.board_title, self.board_labels)  # the board stays flat when the camera tilts
        self.play(self.show(self.board_title, self.board_labels, run_time=beats(4)))
        self.board_live = [self.live(mk) for mk in values]
        self.pin(*self.board_live)

    def board_tick(self, *keys):
        """A matched number turns green and glows once."""
        self.matched.update(keys)
        self.sfx("chime", -12, trim=1.6, fade=0.5)
        glows = []
        for k in keys:
            y = 3.55 - 0.38 * (list(self.vals).index(k) + 1)
            dot = m.Dot([6.0, y, 0], radius=0.01)
            self.pin(dot)
            glows.append(m.Flash(dot, color=GREEN, line_length=0.15, flash_radius=0.45))
        self.play(*glows, run_time=beats(2))
        return []

    def board_title_to(self, text: str):
        self.sfx("switch", -12)
        self.matched.clear()
        new = m.Text(text, font_size=20, color=MUTED).move_to(self.board_title)
        self.pin(new)
        self.play(m.ReplacementTransform(self.board_title, new), run_time=beats(2))
        self.board_title = new

    # ---- Act 0 · plain-words opening -------------------------------------------

    def opening(self):
        title = m.Text("Where the Memory Goes", font_size=60, color=INK).move_to([0, 2.2, 0])
        sub = m.Text("CPE333 Mini-Project 2 · pfcount / pfstat / faultgen", font_size=24, color=MUTED).next_to(title, m.DOWN, buff=0.25)
        grp = m.Text(f"Group: {GROUP}", font_size=30, color=GOLD).move_to([0, 0.75, 0])
        names = m.VGroup(*[m.Text(f"{sid}  {n}", font_size=19, color=INK) for sid, n in MEMBERS])
        names.arrange(m.DOWN, buff=0.1).next_to(grp, m.DOWN, buff=0.4)
        self.sfx("bong", -8)
        self.play(m.Write(title), run_time=beats(4))
        self.play(self.show(sub, grp, run_time=beats(3)))
        self.burst("pluck", len(names), beats(6) * 0.7, -12)
        self.play(m.LaggedStart(*[m.Write(n) for n in names], lag_ratio=0.35), run_time=beats(6))
        self.wait(beats(2))
        self.play(self.hide(title, sub, grp, names, run_time=beats(2)))
        pages = m.VGroup(*[m.Square(0.9, color=MUTED, stroke_width=2, fill_color=GOLD, fill_opacity=0) for _ in range(8)])
        pages.arrange(m.RIGHT, buff=0.3).move_to([0, 0.4, 0])
        self.burst("tick", 8, beats(8), -10)
        self.play(m.LaggedStart(*[m.Create(p) for p in pages], lag_ratio=1), run_time=beats(8))
        self.cap("mmap() and brk() reserve address space. No RAM is given yet.", 2)
        self.cap("Physical pages are assigned lazily, on first access.", 2)
        tok, trail = self.token([-6.5, 2.4, 0])
        self.play(tok.animate.move_to(pages[0].get_center()), run_time=beats(4))
        dim = m.Rectangle(width=14.4, height=8.2, stroke_width=0, fill_color="#000000", fill_opacity=0.55)
        self.play(m.FadeIn(dim), run_time=beats(1))  # the program pauses
        self.sfx("click", -6)
        self.play(m.FadeOut(dim), m.Flash(pages[0], color=GOLD), pages[0].animate.set_fill(GOLD, opacity=0.9),
                  m.FadeOut(tok), run_time=beats(3))
        self.remove(trail)
        self.cap("First access traps into the kernel: a page fault.", 3)
        self.play(m.LaggedStart(*[p.animate.set_fill(GOLD, opacity=0.9) for p in pages[1:]], lag_ratio=1), run_time=beats(6))
        self.pages = pages  # carried into the next scene: they become sleep's first regions

    # ---- Act 1 · what we report ---------------------------------------------------

    def analogies(self):
        self.scoreboard("process: sleep")
        self.cap("pfcount reports four numbers for one process, each checked against Linux.", 3)

    def mobjects_of(self, group):
        return [mob for mob in self.mobjects if mob is not group and (mob in group.submobjects or
                (isinstance(mob, m.VGroup) and mob.submobjects and all(sm in group.submobjects for sm in mob.submobjects)))]

    def grow(self, mob):
        return m.FadeIn(mob, shift=m.UP * 0.3)

    # ---- Act 2 · the goal and the three parts (REPORT §1) ------------------------

    def goal(self):
        self.build_world()
        self.ribbon = ribbon_blocks(REGIONS)
        self.ribbon_lab = m.Text("sleep · its memory, one block per region", font_size=20, color=MUTED).move_to([-3.2, RIBBON_Y + 0.6, 0])
        self.burst("line", 12, beats(5), -16)
        self.play(m.ReplacementTransform(self.pages, self.ribbon[:8]),
                  m.LaggedStart(*[m.FadeIn(b, shift=m.UP * 0.2) for b in self.ribbon[8:]], lag_ratio=0.12),
                  self.show(self.ribbon_lab), run_time=beats(5))
        self.remove(*self.mobjects_of(self.ribbon))
        self.add(self.ribbon)
        key = m.VGroup(*[m.VGroup(m.Square(0.22, fill_color=c, fill_opacity=0.9, stroke_width=0), m.Text(t, font_size=18, color=MUTED)).arrange(m.RIGHT, buff=0.12)
                         for t, c in [("file-backed", BLUE), ("anonymous", GOLD), ("heap / stack", GREEN), ("vdso / vvar", GREY)]])
        key.arrange(m.RIGHT, buff=0.5).move_to([0, RIBBON_Y - 0.75, 0])
        note = m.Text("width: log of size", font_size=18, color=MUTED).next_to(key, m.DOWN, buff=0.2)
        self.play(self.show(key, note, run_time=beats(3)))
        self.play(m.FadeIn(self.tux), run_time=beats(1))
        self.cap("sleep's address space: 30 VMAs, in address order.", 3)
        self.key = m.VGroup(key, note)
        self.pin(self.key)  # docked legend stays flat and on screen while the ribbon is
        self.play(self.key.animate.scale(0.8).to_corner(m.UL, buff=0.35).shift(m.DOWN * 0.45), run_time=beats(2))

    # ---- Act 3 · background: what a fault is (REPORT §2) -------------------------

    def background(self):
        src = self.ribbon[4]  # the locale archive: a big file-backed region
        big = m.Rectangle(width=8.0, height=1.4, stroke_color=BLUE, stroke_width=3, fill_color=BLUE, fill_opacity=0.15).move_to([0, -0.1, 0])
        start = m.Text("vm_start", font_size=20, color=BLUE).next_to(big, m.UP, buff=0.12, aligned_edge=m.LEFT)
        end = m.Text("vm_end", font_size=20, color=BLUE).next_to(big, m.UP, buff=0.12, aligned_edge=m.RIGHT)
        self.move_camera(zoom=1.8, frame_center=src.get_center(), run_time=beats(2))  # fly into the block...
        self.move_camera(zoom=1.0, frame_center=[0, 0, 0], added_anims=[m.TransformFromCopy(src, big)], run_time=beats(2))  # ...and it opens up
        self.play(self.show(start, end, run_time=beats(4)))
        self.cap("Each block is a region, a VMA: one range from vm_start to vm_end.", 3)
        cells = m.VGroup(*[m.Square(0.55, color=MUTED, stroke_width=1.5, fill_color=GOLD, fill_opacity=0) for _ in range(10)])
        cells.arrange(m.RIGHT, buff=0.18).move_to(big)
        self.play(m.LaggedStart(*[m.Create(c) for c in cells], lag_ratio=0.5), run_time=BAR)
        self.cap("Inside it, pages are only reserved. Nothing is in RAM yet.", 2)

        # one fault, top to bottom and back
        self.band_in()
        target = cells[3]
        tok, trail = self.token([target.get_x(), 1.0, 0])
        self.play(tok.animate.move_to(target.get_center()), run_time=beats(2))
        self.play(tok.animate.move_to([target.get_x(), BAND_Y, 0]), run_time=beats(2))
        self.play(m.Flash(tok, color=GOLD), run_time=beats(2))
        self.play(tok.animate.move_to(target.get_center()), run_time=beats(2))
        self.sfx("click", -6)
        self.play(target.animate.set_fill(GOLD, opacity=0.9), m.FadeOut(tok), run_time=beats(2))
        self.remove(trail)
        self.cap("Touch a page: the program drops into the kernel, which fills it, then returns.", 3)

        # minor and major side by side
        quick, slow = cells[1], cells[7]
        t1, tr1 = self.token([quick.get_x(), 1.0, 0], GREEN)
        t2, tr2 = self.token([slow.get_x(), 1.0, 0], RED)
        disk = m.ImageMobject(str(ASSETS / "disk" / "Hard_disk_platters_and_head-1920px.jpg")).scale_to_fit_height(0.9).move_to([5.6, BAND_Y - 0.15, 0])
        cache = m.RoundedRectangle(corner_radius=0.08, width=2.2, height=0.9, stroke_color=BLUE, stroke_width=1.5,
                                   fill_color=PANEL, fill_opacity=0.9).move_to([2.4, BAND_Y - 0.1, 0])
        cache_lab = m.Text("page cache", font_size=18, color=BLUE).move_to(cache)
        self.play(m.FadeIn(disk), m.FadeIn(cache), self.show(cache_lab, run_time=beats(2)), run_time=beats(2))
        self.cap("The kernel first looks in the page cache, already in RAM.", 2)
        self.play(t1.animate.move_to(cache.get_center() + m.LEFT * 0.5), t2.animate.move_to(cache.get_center() + m.RIGHT * 0.5), run_time=beats(2))
        self.play(m.Flash(t1, color=GREEN), m.Flash(t2, color=RED), run_time=beats(1))  # found / not found
        self.sfx("click", -6)
        self.play(t1.animate.move_to(quick.get_center()), quick.animate.set_fill(GREEN, opacity=0.9),
                  t2.animate.move_to(disk.get_center()), run_time=beats(2))
        self.play(m.FadeOut(t1), run_time=beats(1))
        self.wait(beats(2))  # the slow one is still waiting on the disk
        self.sfx("thud", -4)
        self.play(t2.animate.move_to(slow.get_center()), slow.animate.set_fill(RED, opacity=0.9), run_time=beats(2))
        self.play(m.FadeOut(t2), run_time=beats(1))
        self.remove(tr1, tr2)
        self.cap("Found: minor. Not found: read from disk first, a major fault.", 3)
        self.play(m.FadeOut(cache), self.hide(cache_lab), run_time=beats(1))

        # what the difference costs: same scale, typical orders of magnitude
        self.play(m.FadeOut(disk), run_time=beats(1))
        self.band_out()  # the band is shown only while a fault is inside it; no camera tilt happens while it is up
        labs = m.VGroup(*[m.Text(t, font_size=20, color=c) for t, c in [("minor  ~1 µs", GREEN), ("major  ~1 ms (SSD)", RED)]])
        labs.arrange(m.DOWN, buff=0.35, aligned_edge=m.LEFT).move_to([-3.2, -1.5, 0])
        x0 = labs.get_right()[0] + 0.4
        bars = [m.Rectangle(width=w, height=0.3, stroke_width=0, fill_color=c, fill_opacity=0.9).move_to([x0 + w / 2, l.get_y(), 0])
                for l, c, w in zip(labs, (GREEN, RED), (0.02, 6.0))]
        rows = m.VGroup(*[m.VGroup(l, b) for l, b in zip(labs, bars)])
        for b in bars:
            b.stretch(0.001, 0, about_edge=m.LEFT)
        self.play(self.show(rows[0][0], rows[1][0], run_time=beats(2)), *[m.FadeIn(b) for b in bars], run_time=beats(2))
        self.play(*[b.animate.stretch(1000, 0, about_edge=m.LEFT) for b in bars], run_time=beats(4))
        self.cap("Typical cost: a major fault is about a thousand times slower.", 3)
        self.play(self.hide(rows))

        # the kernel's own rule, line by line
        rule = self.code([
            "if (ret & VM_FAULT_RETRY)  return;",
            "if (ret & VM_FAULT_ERROR)  return;",
            "major = (ret & VM_FAULT_MAJOR) || (flags & FAULT_FLAG_TRIED);",
        ], [0, 0.3, 0], size=20)
        notes = [m.Text(t, font_size=18, color=c) for t, c in
                 [("retried: counted once, later", MUTED), ("failed: not counted", MUTED), ("needed I/O, or a retry: major", RED)]]
        self.play(self.hide(big, start, end, cells), self.grow(rule[0]), run_time=beats(4))
        self.band_out()
        for i, note in enumerate(notes):
            note.next_to(rule, m.DOWN, buff=0.25 + 0.3 * i)
            self.run_line(rule, i, self.show(note, run_time=beats(3)), bars=2)
        self.cap("This is how Linux itself decides, in mm_account_fault().", 2)
        self.play(m.FadeOut(rule, shift=m.UP * 0.3), self.hide(*notes), run_time=beats(2))

    # ---- Act 4 · counting regions (REPORT §4.1) ----------------------------------

    def regions_walk(self):
        n = len(REGIONS)
        cum = [0]
        for _, kb in REGIONS:
            cum.append(cum[-1] + kb)
        walk = m.ValueTracker(0)
        for i, blk in enumerate(self.ribbon):
            blk.add_updater(lambda b, *_, i=i: b.set_fill(opacity=1.0 if walk.get_value() >= i + 1 else 0.35))
        scan = m.always_redraw(lambda: m.Line(
            [self.ribbon[min(int(walk.get_value()), n - 1)].get_x(), RIBBON_Y - 0.45, 0],
            [self.ribbon[min(int(walk.get_value()), n - 1)].get_x(), RIBBON_Y + 0.45, 0], color=INK, stroke_width=4))

        walk_code = self.code([
            "mm = get_task_mm(task);",
            "mmap_read_lock_killable(mm);",
            "for_each_vma(vmi, vma) {",
            "    regions++;",
            "    vsize += vma->vm_end - vma->vm_start;",
            "}",
            "mmap_read_unlock(mm);",
        ], [-2.6, -0.3, 0], size=20)
        self.pin(walk_code)  # code stays flat while the camera tilts
        t = self.term_open([3.7, -0.4, 0], width=5.8, rows=3)
        self.term_cmd(t, "sudo tools/pfstat 10605")
        self.play(self.grow(walk_code[0]), run_time=beats(1))
        self.run_line(walk_code, 0, m.Indicate(self.ribbon_lab), bars=1)
        self.cap("Get the process's memory map...", 1)
        self.run_line(walk_code, 1, bars=1)
        self.cap("...hold it still while we read...", 1)
        self.vals["regions"].set_value(0)
        self.vals["size"].set_value(0)
        self.add(scan)
        self.run_line(walk_code, 2, bars=1)
        self.run_line(walk_code, 3, bars=1)
        self.run_line(walk_code, 4, bars=1)
        self.run_line(walk_code, 5, bars=1)
        self.cap("...and visit every region: count it, add its size.", 1)
        self.add(self.vals["regions"], self.vals["size"])  # trackers only update while in the scene
        self.vals["regions"].add_updater(lambda v, *_: v.set_value(min(int(walk.get_value()), n)))
        self.vals["size"].add_updater(lambda v, *_: v.set_value(cum[min(int(walk.get_value()), n)]))
        self.move_camera(phi=38 * m.DEGREES, run_time=beats(2))  # lean in: the ribbon becomes a floor
        self.play(walk.animate.set_value(n), run_time=beats(16), rate_func=m.linear)
        # 3D: each region rises to the log of its size; one file mapping dominates the address space
        hgt = [0.3 + 0.55 * math.log10(kb) for _, kb in REGIONS]
        sky = m.VGroup(*[m.Prism(dimensions=[max(0.05, b.width), 0.55, hh]).set_color(KIND_COLOR[k]).move_to([b.get_x(), RIBBON_Y, hh / 2])
                         for b, (k, _), hh in zip(self.ribbon, REGIONS, hgt)])
        self.move_camera(phi=62 * m.DEGREES, added_anims=[m.LaggedStart(*[m.FadeIn(pr, shift=m.OUT * 0.5) for pr in sky], lag_ratio=0.06)],
                         run_time=beats(4))
        self.cap("Height = log of size: one 3 MB file mapping outweighs the other 29.", 2)
        self.move_camera(phi=0, added_anims=[m.FadeOut(sky, shift=m.IN * 0.5)], run_time=beats(2))
        self.vals["regions"].clear_updaters()
        self.vals["size"].clear_updaters()
        self.remove(self.vals["regions"], self.vals["size"])
        self.remove(scan)
        self.scan_last = m.Line([self.ribbon[-1].get_x(), RIBBON_Y - 0.45, 0], [self.ribbon[-1].get_x(), RIBBON_Y + 0.45, 0],
                                color=INK, stroke_width=4)  # kept: it drops into the kernel as the probe gate
        self.add(self.scan_last)
        self.run_line(walk_code, 6, bars=1)
        self.play(m.FadeOut(walk_code, shift=m.UP * 0.3), run_time=beats(2))

        self.term_out(t, ["VMAs          30      match /proc/PID/maps", "Virtual size  5.6 MB  match VmSize"], color=GREEN)
        ticks = self.board_tick("regions", "size")
        self.cap("30 regions, 5.6 MB: exactly what Linux itself reports.", 3)
        for blk in self.ribbon:
            blk.clear_updaters()
        self.play(self.term_close(t))

    # ---- Act 5 · counting faults (REPORT §4.2–4.3) --------------------------------

    def fault_counting(self):
        self.band_in()
        # live: a gate in the kernel band keeps only the target's faults
        gate = m.Rectangle(width=0.18, height=1.3, stroke_width=0, fill_color=GOLD, fill_opacity=0.8).move_to([-2.4, BAND_Y, 0])
        gate_lab = m.Text("probe", font_size=18, color=GOLD).next_to(gate, m.LEFT, buff=0.12)
        wells = []
        for i, (t, c) in enumerate([("minor", GREEN), ("major", RED), ("anon", GOLD), ("file-backed", BLUE)]):
            x = -0.6 + 1.85 * i
            frame = m.RoundedRectangle(corner_radius=0.08, width=1.7, height=1.2, stroke_color=c, stroke_width=1.5,
                                       fill_color=PANEL, fill_opacity=0.9).move_to([x, BAND_Y, 0])
            wells.append((frame, m.Text(t, font_size=16, color=MUTED).move_to([x, BAND_Y + 0.38, 0]), m.ValueTracker(0), c, x))
        self.play(m.ReplacementTransform(self.scan_last, gate), self.show(gate_lab, *[w[0] for w in wells], *[w[1] for w in wells]), run_time=BAR)
        well_nums = [self.live(lambda w=w: m.Text(f"{w[2].get_value():,.0f}", font_size=22, color=w[3]).move_to([w[4], BAND_Y - 0.15, 0]))
                     for w in wells]

        probe = self.code([
            "entry:  if (current->tgid != target) return 1;",
            "return: classify the kernel's result",
        ], [-2.4, -0.15, 0], size=20)
        self.play(self.grow(probe[0]), run_time=beats(2))
        greys = [m.Square(0.34, fill_color=GREY, fill_opacity=1, stroke_width=0).move_to([x, RIBBON_Y + 0.9, 0]) for x in (-6.0, -5.0, -4.0)]
        self.add(*greys)
        self.run_line(probe, 0, m.LaggedStart(*[g.animate.move_to([-2.4, BAND_Y, 0]) for g in greys], lag_ratio=0.3), bars=1)
        self.play(m.LaggedStart(*[g.animate.move_to([7.5, BAND_Y, 0]) for g in greys], lag_ratio=0.3), run_time=beats(3))  # other PIDs pass straight through
        self.remove(*greys)
        self.cap("A probe on handle_mm_fault() sees every fault. Other programs pass by.", 3)
        tok, trail = self.token([self.ribbon[10].get_x(), RIBBON_Y, 0])
        self.play(tok.animate.move_to(gate.get_center()), run_time=beats(3))
        self.sfx("click", -6)
        self.run_line(probe, 1, tok.animate.move_to(wells[0][0].get_center()), wells[0][2].animate.set_value(1), bars=1)
        self.play(m.FadeOut(tok), run_time=beats(1))
        self.remove(trail)
        self.cap("Ours stop at the gate and are sorted: minor or major, anon or file.", 3)
        self.board_title_to("E2 · faultgen anon:64")
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.play(wells[0][2].animate.set_value(16538), wells[1][2].animate.set_value(1), wells[2][2].animate.set_value(16462),
                  wells[3][2].animate.set_value(77), self.vals["minor"].animate.set_value(16538), self.vals["major"].animate.set_value(1),
                  run_time=beats(8))
        self.board_tick("minor", "major")
        self.cap("E2: 16,538 minor and 1 major, exactly what getrusage() reports.", 3)
        self.cap("Lifetime totals add live and exited threads, read under a lock like /proc.", 3)
        frozen = [self.freeze(n_, lambda w=w: m.Text(f"{w[2].get_value():,.0f}", font_size=22, color=w[3]).move_to([w[4], BAND_Y - 0.15, 0]))
                  for n_, w in zip(well_nums, wells)]
        self.play(self.hide(gate, gate_lab, probe, *[w[0] for w in wells], *[w[1] for w in wells], *frozen))
        self.band_out()

        # short programs: the probe at exit freezes the map and stamps it into the board
        self.board_title_to("a 20 ms program")
        for k in self.vals:
            self.vals[k].set_value(-1)
        short = ribbon_blocks(REGIONS[:12], y=0.0, width=5.0, height=0.5)
        self.play(m.LaggedStart(*[m.FadeIn(b, shift=m.UP * 0.2) for b in short], lag_ratio=0.2), run_time=beats(2))
        self.play(short.animate.set_fill(GREY, opacity=0.6), run_time=beats(1))  # exit: the map is frozen
        stamp = short.copy()
        self.play(stamp.animate.scale(0.15).move_to([6.0, 3.0, 0]).set_opacity(0),
                  self.vals["regions"].animate.set_value(12), self.vals["size"].animate.set_value(sum(kb for _, kb in REGIONS[:12])),
                  run_time=beats(2))
        self.remove(stamp)
        self.cap("It exits before any poll. A probe at exit saves map_count and total_vm.", 3)
        self.play(m.FadeOut(short), run_time=beats(1))

    # ---- Act 6 · walkthrough: the tool running (REPORT §4.5, E7) ---------------------

    def demo(self):
        self.board_title_to("demo run · PID 2508")
        t = self.term_open([-2.9, -0.3, 0], width=7.6, rows=3)
        self.term_cmd(t, "sudo tools/pfstat -w 0.5 -- tests/faultgen anon:64 file:big.bin free")

        # faultgen's own memory replaces sleep's: 16 regions, 2.2 MB
        fg = ribbon_blocks(REGIONS[:16], width=7.0).set_x(-2.4)
        fg_lab = m.Text("faultgen · its memory", font_size=20, color=MUTED).move_to(self.ribbon_lab)
        self.play(m.ReplacementTransform(self.ribbon, fg), m.ReplacementTransform(self.ribbon_lab, fg_lab), run_time=BAR)
        self.ribbon, self.ribbon_lab = fg, fg_lab
        # run mode: the child stops itself, pfstat reads a baseline, then lets it exec
        child = m.Circle(radius=0.32, color=GOLD, fill_color=GOLD, fill_opacity=0.25).move_to([3.6, 0.4, 0])
        c_lab = m.Text("child", font_size=18, color=GOLD).next_to(child, m.DOWN, buff=0.1)
        stop = m.Text("SIGSTOP", font_size=20, color=RED).next_to(child, m.UP, buff=0.12)
        self.play(m.GrowFromCenter(child), self.show(c_lab, run_time=beats(1)), run_time=beats(1))
        self.play(self.show(stop, run_time=beats(1)), child.animate.set_fill(opacity=0.06), run_time=beats(1))
        base = m.Text("baseline 468", font_size=22, color=MUTED).move_to([3.6, -0.6, 0])
        self.play(m.TransformFromCopy(child, base), run_time=beats(1))
        self.play(base.animate.scale(0.7).move_to([5.6, -0.9, 0]).set_opacity(0.4), run_time=beats(1))
        go = m.Text("SIGCONT, then exec", font_size=20, color=GREEN).move_to(stop)
        self.play(m.ReplacementTransform(stop, go), child.animate.set_fill(opacity=0.6), run_time=beats(1))
        self.play(*[self.vals[k].animate.set_value(v) for k, v in [("regions", 16), ("size", 2.2 * 1024), ("minor", 0), ("major", 0)]],
                  run_time=beats(1))
        self.cap("Run mode: the child pauses, pfstat records 468 faults as baseline, then lets it run.", 3)
        self.play(m.FadeOut(child), self.hide(c_lab, go, base), run_time=beats(1))

        # anon:64 — the block appears first, the RAM follows
        anon = m.Rectangle(width=3.2, height=0.6, stroke_color=GOLD, stroke_width=2, fill_color=GOLD, fill_opacity=0)
        anon.next_to(fg, m.RIGHT, buff=0.06)
        self.play(m.Create(anon),
                  self.vals["regions"].animate.set_value(17), self.vals["size"].animate.set_value(66.2 * 1024), run_time=BAR)
        self.cap("Map 64 MB: the memory map grows at once. Nothing is in RAM yet.", 3)
        cells = m.VGroup(*[m.Rectangle(width=3.2 / 16, height=0.6, stroke_width=0, fill_color=GOLD, fill_opacity=0.9) for _ in range(16)])
        cells.arrange(m.RIGHT, buff=0).move_to(anon)
        self.sfx("click", -8)
        self.play(m.LaggedStart(*[m.FadeIn(c) for c in cells], lag_ratio=1),
                  self.vals["minor"].animate.set_value(16384), run_time=beats(8), rate_func=m.linear)
        self.cap("Touch every page: about 16,384 minor faults, one per 4 KiB page.", 3)

        # file: a cold file, one disk read per page
        self.band_in()
        fil = m.Rectangle(width=1.6, height=0.6, stroke_color=BLUE, stroke_width=2, fill_opacity=0).next_to(anon, m.RIGHT, buff=0.06)
        disk = m.ImageMobject(str(ASSETS / "disk" / "Hard_disk_platters_and_head-1920px.jpg")).scale_to_fit_height(0.9).move_to([5.6, BAND_Y - 0.15, 0])
        self.play(m.Create(fil), m.FadeIn(disk), self.vals["regions"].animate.set_value(18),
                  self.vals["size"].animate.set_value(98.2 * 1024), run_time=BAR)
        fcells = m.VGroup(*[m.Rectangle(width=1.6 / 8, height=0.6, stroke_width=0, fill_color=RED, fill_opacity=0.9) for _ in range(8)])
        fcells.arrange(m.RIGHT, buff=0).move_to(fil)
        drops = [m.Dot(c.get_center(), radius=0.06, color=RED) for c in fcells]
        self.sfx("thud", -4)
        self.play(m.LaggedStart(*[m.AnimationGroup(m.FadeIn(c), d.animate.move_to(disk.get_center()).set_opacity(0))
                                  for c, d in zip(fcells, drops)], lag_ratio=1),
                  self.vals["major"].animate.set_value(8193), self.vals["minor"].animate.set_value(16521), run_time=beats(8), rate_func=m.linear)
        self.cap("Read a cold 32 MB file: one trip to the disk per page. 8,193 major.", 3)

        # free: both blocks leave, the map shrinks back
        self.fil = fil  # carried into the experiments: it stretches into the E3 row
        self.play(m.FadeOut(anon, cells, fcells, *drops, shift=m.UP * 0.4),
                  self.vals["regions"].animate.set_value(16), self.vals["size"].animate.set_value(2.2 * 1024), run_time=BAR)
        self.term_out(t, ["Minor page faults   16,521   match vs getrusage()",
                          "Major page faults    8,193   match vs getrusage()"], color=INK)
        ticks = self.board_tick("minor", "major")
        self.cap("Freed: back to 16 regions. 16,521 / 8,193 match getrusage().", 3)
        self.play(self.term_close(t), m.FadeOut(disk))
        self.band_out()

    # ---- Act 7 · experiments on one stage (REPORT §6.2) -----------------------------

    def experiments(self):
        """Four experiments race on one floor: each faulted tile rises; the counts end side by side."""
        self.play(m.FadeOut(self.ribbon), self.hide(self.ribbon_lab), m.FadeOut(self.key), run_time=beats(2))
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("E3-E6 · faultgen")
        t = self.term_open([-1.0, -0.2, 0], width=8.2, rows=3)
        self.term_cmd(t, "./vm.sh make experiments")
        self.term_out(t, ["Ubuntu 24.04.5 · Linux 6.8.0-142-generic · aarch64 · Lima, 4 vCPU",
                          "page 4 KiB · THP madvise · fault_around 64 KiB · readahead 128 KiB"])
        self.play(self.term_close(t))
        rows = [  # (label, tiles, final count, unit, colour, y)
            ("E3 cold, random", 64, 8192, "major", RED, 1.5),
            ("E5 cold, readahead", 64, 2, "major", RED, 0.5),
            ("E4 warm cache", 64, 652, "minor", GREEN, -0.5),
            ("E6 THP 64 MiB", 32, 188, "minor", GOLD, -1.5),
        ]
        floor, counts, labels, nums = [], [], [], []
        for lab, n, _, unit, col, y in rows:
            g = m.VGroup(*[m.Rectangle(width=8.4 / n * 0.85, height=0.55, stroke_color=BLUE, stroke_width=1, fill_opacity=0)
                           for _ in range(n)]).arrange(m.RIGHT, buff=8.4 / n * 0.15).move_to([0.3, y, 0])
            floor.append(g)
            labels.append(m.Text(lab, font_size=20, color=MUTED).next_to(g, m.LEFT, buff=0.3))
            c = m.ValueTracker(0)
            counts.append(c)
            nums.append(m.always_redraw(lambda c=c, g=g, unit=unit, col=col: m.Text(
                f"{c.get_value():,.0f} {unit}", font_size=22, color=col).next_to(g, m.RIGHT, buff=0.3)))
        fa = m.Text("one fault maps 16 cached pages (fault_around_bytes = 65536)", font_size=15, color=GREEN).next_to(floor[2], m.DOWN, buff=0.05)
        self.play(m.ReplacementTransform(self.fil, floor[0]), m.Write(labels[0]), run_time=beats(2))  # the demo's file becomes E3
        self.play(*[m.TransformFromCopy(floor[0], g) for g in floor[1:]], *[m.Write(l) for l in labels[1:]], run_time=beats(2))
        labels.append(fa)
        self.add(*nums)
        self.move_camera(phi=48 * m.DEGREES, theta=-78 * m.DEGREES, zoom=0.92, frame_center=[0, 0, 0.3], run_time=beats(2))
        lift = m.OUT * 0.4
        order = list(range(64))
        random.shuffle(order)
        e3 = m.LaggedStart(*[floor[0][i].animate.set_fill(RED, opacity=0.9).shift(lift) for i in order], lag_ratio=0.3)
        e5 = m.Succession(floor[1][0].animate.set_fill(RED, opacity=0.9).shift(lift),
                          m.LaggedStart(*[t.animate.set_fill(GREEN, opacity=0.5) for t in floor[1][1:]], lag_ratio=0.1))
        e4 = m.LaggedStart(*[floor[2][i:i + 4].animate.set_fill(GREEN, opacity=0.9).shift(lift) for i in range(0, 64, 4)], lag_ratio=0.6)
        e6 = m.LaggedStart(*[t.animate.set_fill(GOLD, opacity=0.9).shift(lift) for t in floor[3]], lag_ratio=0.6)
        self.sfx("thud", -8)
        self.play(e3, e5, e4, e6, *[c.animate.set_value(r[2]) for c, r in zip(counts, rows)],
                  m.Write(fa, run_time=beats(3)), run_time=beats(12), rate_func=m.linear)
        self.cap("Same 32 MiB file: cold random reads fault on every page (8,193); readahead needs 2.", 3)
        self.cap("Warm cache + fault-around: 652. THP: 188 vs 16,538 without it (E2).", 3)
        self.begin_ambient_camera_rotation(rate=0.04)
        self.wait(BAR)
        self.stop_ambient_camera_rotation()
        frozen = [self.freeze(n_, lambda c=c, g=g, r=r: m.Text(f"{c.get_value():,.0f} {r[3]}", font_size=22, color=r[4]).next_to(g, m.RIGHT, buff=0.3))
                  for n_, c, g, r in zip(nums, counts, floor, rows)]
        self.play(self.hide(*labels, *frozen))
        self.move_camera(phi=0, theta=-90 * m.DEGREES, zoom=1.0, frame_center=[0, 0, 0], run_time=beats(2))
        self.exp_floor = floor  # carried into E1: the four rows become the table's four row rules

    # ---- Act 8 · checks and findings (REPORT §6.1, §7) --------------------------------

    def checks(self):
        # E1 (e1a, e1b): every number pfstat prints, beside the number Linux prints for it
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("E1 · pfstat vs /proc")
        seps = [m.Line([-5.4, 1.2 - 0.75 * i - 0.38, 0], [4.6, 1.2 - 0.75 * i - 0.38, 0], color=MUTED, stroke_width=1, stroke_opacity=0.4)
                for i in range(4)]
        self.play(*[m.ReplacementTransform(g, sp) for g, sp in zip(self.exp_floor, seps)], run_time=beats(2))
        self.cap("E1 · left: what pfstat prints. Right: what Linux itself prints.", 2)
        cols = [("", -4.2), ("sleep", -0.9), ("PID 1 (systemd)", 2.9)]
        rows = [("regions", "/proc/<pid>/maps lines", "30", "113"),
                ("address space", "VmSize", "5.6 MB", "21.9 MB"),
                ("minor faults", "/proc/<pid>/stat", "106", "12,986"),
                ("major faults", "/proc/<pid>/stat", "0", "94")]
        head = [m.Text(t, font_size=22, color=MUTED).move_to([x, 1.9, 0]) for t, x in cols[1:]]
        sub = [m.Text(t, font_size=16, color=c).move_to([x + dx, 1.55, 0]) for x in (cols[1][1], cols[2][1])
               for t, c, dx in (("pfstat", INK, -0.7), ("/proc", MUTED, 0.7))]
        self.play(self.show(*head, *sub, run_time=beats(2)))
        lines = []
        for i, (name, src, a_, b_) in enumerate(rows):
            y = 1.2 - 0.75 * i
            lab = m.VGroup(m.Text(name, font_size=22, color=INK), m.Text(src, font_size=16, color=MUTED)).arrange(m.DOWN, buff=0.06, aligned_edge=m.LEFT)
            lab.move_to([cols[0][1], y, 0]).align_to([-5.4, 0, 0], m.LEFT)
            cells = []
            for v, x in ((a_, cols[1][1]), (b_, cols[2][1])):
                ours = m.Text(v, font_size=24, color=INK).move_to([x - 0.7, y, 0])
                theirs = m.Text(v, font_size=24, color=MUTED).move_to([x + 0.7, y, 0])
                cells.append((ours, theirs))
            self.sfx("click", -6)  # pfstat writes its number
            self.play(self.show(lab, *[c[0] for c in cells], run_time=beats(2)))  # pfstat writes its number...
            self.sfx("toggle", -10)
            self.play(*[m.FadeIn(c[1], shift=m.LEFT * 0.3) for c in cells], run_time=beats(1))  # ...Linux's lands beside it
            self.play(*[c[0].animate.set_color(GREEN) for c in cells], *[c[1].animate.set_color(GREEN) for c in cells], run_time=beats(1))
            lines.append(m.VGroup(lab, *[x for c in cells for x in c]))
        self.cap("E1 · every number matches what Linux itself reports, for sleep and for PID 1.", 3)
        self.play(self.hide(*head, *sub, *lines, *seps))

        # F3 (REPORT §7): the life of one fault inside handle_mm_fault(), and where each probe can look
        self.board_title_to("F3 · where to probe")
        self.band_in()
        y = BAND_Y
        track = m.Line([-4.4, y, 0], [5.4, y, 0], color=MUTED, stroke_width=2)
        enter = m.Text("enter handle_mm_fault()", font_size=16, color=MUTED).move_to([-3.3, y - 0.6, 0])
        leave = m.Text("return: result known", font_size=16, color=MUTED).move_to([4.2, y - 0.6, 0])
        tp = m.Rectangle(width=0.12, height=0.7, stroke_width=0, fill_color=RED, fill_opacity=0.9).move_to([-3.3, y, 0])
        kp = m.Rectangle(width=0.12, height=0.7, stroke_width=0, fill_color=GREEN, fill_opacity=0.9).move_to([4.2, y, 0])
        tp_lab = m.VGroup(m.Text("tracepoint page_fault_user", font_size=18, color=RED),
                          m.Text("x86 only · our VM is arm64", font_size=16, color=RED)).arrange(m.DOWN, buff=0.06).move_to([-3.3, y + 1.15, 0])
        kp_lab = m.VGroup(m.Text("our kretprobe", font_size=18, color=GREEN),
                          m.Text("any architecture", font_size=16, color=GREEN)).arrange(m.DOWN, buff=0.06).move_to([4.2, y + 1.15, 0])
        self.play(m.Create(track), m.FadeIn(tp), m.FadeIn(kp), self.show(enter, leave, tp_lab, kp_lab, run_time=beats(3)), run_time=beats(3))
        tok, trail = self.token([-4.6, y, 0], GREY)
        self.play(tok.animate.move_to(tp.get_center()), run_time=beats(2))
        q = m.Text("minor or major?", font_size=20, color=RED).next_to(tp_lab, m.UP, buff=0.12)
        self.sfx("thud", -8)
        self.play(self.show(q, run_time=beats(2)), m.Flash(tp, color=RED), run_time=beats(2))  # it fires before the work: no answer yet
        self.cap("F3 · the suggested tracepoint fires on entry, before the kernel knows the answer.", 3)
        work = m.Rectangle(width=4.0, height=0.4, stroke_color=BLUE, stroke_width=1, fill_color=BLUE, fill_opacity=0.15).move_to([0.45, y, 0])
        work_lab = m.Text("kernel handles it: page cache or disk", font_size=16, color=BLUE).next_to(work, m.DOWN, buff=0.08)
        self.play(m.FadeIn(work), self.show(work_lab, run_time=beats(1)), tok.animate.move_to(work.get_center()), run_time=beats(2))
        self.play(tok.animate.set_fill(GREEN), m.Flash(work, color=GREEN), run_time=beats(1))
        self.play(tok.animate.move_to(kp.get_center()), run_time=beats(2))
        a_ = m.Text("minor", font_size=20, color=GREEN).next_to(kp_lab, m.UP, buff=0.12)
        self.sfx("chime", -12, trim=1.6, fade=0.5)
        self.play(self.show(a_, run_time=beats(2)), m.Flash(kp, color=GREEN), run_time=beats(2))
        self.cap("A kretprobe fires on return, sees the result, and works on arm64 too.", 3)
        self.remove(trail)
        self.play(m.FadeOut(tok), self.hide(track, tp, kp, enter, leave, tp_lab, kp_lab, q, work, work_lab, a_))
        self.band_out()

        # post-merge regression suite (report Table 8): every check runs at once and lands on PASS
        self.board_title_to("post-merge regression")
        t = self.term_open([0, 0.4, 0], width=7.0, rows=3)
        self.term_cmd(t, "./vm.sh run sudo sh tests/regress.sh")
        self.term_out(t, ["Linux 6.8.0-147-generic · 5 checks passed", "PID 26873 reused · old target unchanged"], color=GREEN)
        self.play(self.term_close(t))

        # retarget: a fault that started under A must finish in A's session, even after the target moves to B
        wa, wb = [m.RoundedRectangle(corner_radius=0.1, width=2.0, height=1.2, stroke_color=c, stroke_width=1.5,
                                     fill_color=PANEL, fill_opacity=0.9).move_to([x, -0.6, 0]) for x, c in ((-2.4, GOLD), (2.4, BLUE))]
        la = m.Text("session A", font_size=20, color=GOLD).next_to(wa, m.UP, buff=0.1)
        lb = m.Text("session B", font_size=20, color=BLUE).next_to(wb, m.UP, buff=0.1)
        ptr = m.Text("target: A", font_size=24, color=GOLD).move_to([0, 2.0, 0])
        self.play(m.FadeIn(wa), m.FadeIn(wb), self.show(la, lb, ptr, run_time=beats(1)), run_time=beats(1))
        tok, trail = self.token([-2.4, 2.6, 0])
        self.play(tok.animate.move_to([0, 0.9, 0]), run_time=beats(1))
        ptr2 = m.Text("target: B", font_size=24, color=BLUE).move_to(ptr)
        self.sfx("switch", -8)
        self.play(m.ReplacementTransform(ptr, ptr2), m.Indicate(wb, color=BLUE), run_time=beats(1))  # retarget mid-fault
        self.play(tok.animate.move_to(wa.get_center()), m.Flash(wa, color=GOLD), run_time=beats(1))
        self.remove(trail)
        self.cap("Retarget mid-fault: the fault still lands in A's session, never in B's.", 2)
        self.play(m.FadeOut(tok), m.FadeOut(wa), m.FadeOut(wb), self.hide(la, lb, ptr2), run_time=beats(1))
        cards = [("retarget", "A's faults never reach B", None),
                 ("PID reuse", "PID 26873 reused, old counters frozen", 26873),
                 ("thread exit", "snapshots complete", 100),
                 ("lifetime reads", "never decreased", 20000),
                 ("unload in fault", "sessions released", None),
                 ("SIGCHLD ignored", "target reset to idle", None)]
        grid, nums = [], []
        for i, (t, d, n) in enumerate(cards):
            x, y = -3.9 + 3.9 * (i % 3), 1.0 - 1.6 * (i // 3)
            box = m.RoundedRectangle(corner_radius=0.1, width=3.6, height=1.35, stroke_color=MUTED, stroke_width=1.2,
                                     fill_color=PANEL, fill_opacity=0.95).move_to([x, y, 0])
            head = m.Text(t, font_size=22, color=INK).move_to([x, y + 0.35, 0])
            desc = m.Text(d, font_size=15, color=MUTED).move_to([x, y - 0.4, 0])
            grid.append(m.VGroup(box, head, desc))
            if n:
                tr = m.ValueTracker(0)
                unit = {26873: "", 100: " runs", 20000: " reads"}[n]
                fmt = (lambda v: f"PID {v:.0f}") if n == 26873 else (lambda v, unit=unit: f"{v:,.0f}{unit}")
                nums.append((tr, n, m.always_redraw(lambda tr=tr, x=x, y=y, fmt=fmt: m.Text(fmt(tr.get_value()), font_size=20, color=GOLD).move_to([x, y - 0.03, 0]))))
        self.burst("glass", 6, beats(3), -12)
        self.play(m.LaggedStart(*[m.FadeIn(g, shift=m.UP * 0.2) for g in grid], lag_ratio=0.15), run_time=beats(3))
        self.add(*[n_[2] for n_ in nums])
        self.play(*[tr.animate.set_value(n) for tr, n, _ in nums], run_time=beats(4), rate_func=m.linear)
        self.sfx("chime", -12, trim=1.6, fade=0.5)
        self.play(m.LaggedStart(*[g[0].animate.set_stroke(GREEN, width=2.5) for g in grid], lag_ratio=0.12),
                  *[m.Flash(g[0].get_corner(m.UR) + [-0.25, -0.25, 0], color=GREEN, flash_radius=0.25) for g in grid], run_time=beats(3))
        self.cap("Six lifecycle and concurrency checks after merge: all passed.", 2)
        self.play(*[m.FadeOut(g, shift=m.DOWN * 0.2) for g in grid], *[m.FadeOut(n_[2]) for n_ in nums], run_time=beats(2))

        # E8 ls: the same scope question on a smaller program
        self.board_title_to("E8 · sh + ls")
        t = self.term_open([0, 0.2, 0], width=9.0, rows=4)
        self.term_cmd(t, "sudo tools/pfstat -- sh -c 'ls -R /usr/include >/dev/null'")
        self.term_out(t, ["Minor page faults   258   differs by -135 vs getrusage()"], color=RED)
        self.term_cmd(t, "sudo tools/pfstat -f -- sh -c 'ls -R /usr/include >/dev/null'")
        self.term_out(t, ["Minor page faults   390   match vs wait4(), waited descendants only"], color=GREEN)
        self.cap("E8 · sh runs ls as a child: 258 alone, 390 with -f, matching wait4().", 2)
        self.play(self.term_close(t))

        # F7 (e8d, e8e): gcc's own faults vs getrusage(), which also counts the children it waited for
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("gcc -O2 faultgen.c")
        self.play(*[self.vals[k].animate.set_value(v) for k, v in [("regions", 21), ("size", 6.6 * 1024), ("minor", 0), ("major", 0)]],
                  run_time=beats(1))
        tg = self.term_open([0, -2.2, 0], width=8.6, rows=2)
        self.term_cmd(tg, "sudo tools/pfstat -- gcc -O2 -o /tmp/fg tests/faultgen.c")
        parent = ribbon_blocks(REGIONS[:8], y=1.6, width=2.6, height=0.4)
        p_lab = m.Text("gcc", font_size=20, color=INK).next_to(parent, m.UP, buff=0.1)
        self.play(m.FadeIn(parent, shift=m.UP * 0.2), self.show(p_lab, run_time=beats(2)), run_time=beats(2))

        # two bars on one scale: what Linux reports, what we counted
        W, X0, total = 10.0, -5.0, 5987  # 287 + 5,700
        ref = m.Rectangle(width=W, height=0.42, stroke_color=MUTED, stroke_width=1.5, fill_opacity=0).move_to([X0 + W / 2, -0.9, 0])
        ref_lab = m.Text("getrusage(): 5,987", font_size=20, color=MUTED).next_to(ref, m.UP, buff=0.1, aligned_edge=m.LEFT)
        ours = m.Rectangle(width=W * 287 / total, height=0.42, stroke_width=0, fill_color=GOLD, fill_opacity=0.95)
        ours.move_to([X0 + ours.width / 2, -0.9, 0])
        ours_lab = m.Text("pfstat: 287", font_size=20, color=GOLD).next_to(ref, m.DOWN, buff=0.12, aligned_edge=m.LEFT)
        gap = m.Rectangle(width=W - ours.width, height=0.42, stroke_width=0, fill_color=RED, fill_opacity=0.25)
        gap.move_to([X0 + ours.width + gap.width / 2, -0.9, 0])
        gap_lab = m.Text("missing 5,700", font_size=20, color=RED).move_to(gap)
        self.play(m.Create(ref), self.show(ref_lab, run_time=beats(2)), run_time=beats(2))
        self.sfx("click", -6)
        self.play(m.GrowFromEdge(ours, m.LEFT), self.vals["minor"].animate.set_value(287), self.show(ours_lab, run_time=beats(2)), run_time=beats(2))
        self.play(m.FadeIn(gap), self.show(gap_lab, run_time=beats(2)), run_time=beats(2))
        self.term_out(tg, ["Minor page faults   287   differs by -5700 vs getrusage()"], color=RED)
        self.cap("F7 · counting gcc alone gives 287: 5,700 below getrusage().", 3)
        self.play(self.term_close(tg))

        # where the rest lives: gcc forks the real workers
        names = ["cc1", "as", "collect2", "ld"]
        kids = [ribbon_blocks(REGIONS[:10], y=0.45, width=2.4, height=0.36).set_x(x) for x in (-4.5, -1.5, 1.5, 4.5)]
        k_labs = [m.Text(n, font_size=18, color=MUTED).next_to(k, m.UP, buff=0.08) for n, k in zip(names, kids)]
        for k, l in zip(kids, k_labs):  # each child splits off from the parent, one per beat
            self.sfx("pluck", -8)
            self.play(m.TransformFromCopy(parent, k), self.show(l, run_time=beats(1)), run_time=beats(1))
        self.cap("The children it waits for do the work, and wait4() adds theirs in.", 3)

        # -f: the probe also counts any process whose ancestor is the target
        self.board_title_to("gcc -O2 faultgen.c  ·  pfstat -f")
        tg = self.term_open([0, -2.2, 0], width=8.6, rows=2)
        self.term_cmd(tg, "sudo tools/pfstat -f -- gcc -O2 -o /tmp/fg tests/faultgen.c")
        self.play(*[k.animate.set_fill(GOLD, opacity=0.95) for k in kids], run_time=beats(1))
        fill = m.Rectangle(width=W * 5971 / total, height=0.42, stroke_width=0, fill_color=GOLD, fill_opacity=0.95)
        fill.move_to([X0 + fill.width / 2, -0.9, 0])
        drops = [k.copy() for k in kids]
        self.sfx("chime", -10)
        self.play(*[d.animate.scale(0.2).move_to(fill.get_center()).set_opacity(0) for d in drops],
                  m.Transform(ours, fill), m.FadeOut(gap), self.hide(gap_lab, run_time=beats(2)),
                  self.vals["minor"].animate.set_value(5971), run_time=beats(4))
        self.remove(*drops)
        ours_lab2 = m.Text("pfstat -f: 5,971 (separate run)", font_size=20, color=GREEN).move_to(ours_lab, aligned_edge=m.LEFT)
        self.play(m.ReplacementTransform(ours_lab, ours_lab2), run_time=beats(2))
        self.board_tick("minor")
        self.term_out(tg, ["Minor page faults   5,971   match vs wait4(), waited descendants only"], color=GREEN)
        self.cap("With -f the children count too: 5,971, matching wait4() for that run.", 3)
        self.play(self.hide(parent, p_lab, *kids, *k_labs, ref, ref_lab, ours_lab2), self.term_close(tg))
        self.f7bar = ours  # carried into the limits: the bar breaks into the probe's 64 slots

    # ---- Act 9 · limits and the end (REPORT §8–9) -----------------------------------

    def ending(self):
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("limits")
        slots = m.VGroup(*[m.Square(0.26, stroke_color=BLUE, stroke_width=1, fill_color=GOLD, fill_opacity=0) for _ in range(64)])
        slots.arrange_in_grid(rows=4, cols=16, buff=(0.06, 0.06)).move_to([-1.6, 0.8, 0])
        s_lab = m.Text("kretprobe maxactive = 64 faults in flight", font_size=20, color=INK).next_to(slots, m.UP, buff=0.2)
        self.play(m.ReplacementTransform(self.f7bar, slots), m.Write(s_lab), run_time=beats(2))
        self.burst("tick", 16, beats(3), -14)
        self.play(m.LaggedStart(*[sq.animate.set_fill(opacity=0.85) for sq in slots], lag_ratio=0.03), run_time=beats(3))
        x_miss = slots.get_right()[0] + 1.3
        tok, trail = self.token([x_miss, 2.6, 0], RED)
        missed = m.Text("nmissed + 1", font_size=20, color=RED).move_to([x_miss, -0.4, 0])
        self.play(tok.animate.move_to(slots.get_right() + m.RIGHT * 0.25), run_time=beats(1))
        self.sfx("miss", -8)
        self.play(tok.animate.move_to(missed.get_top() + m.UP * 0.25), m.Write(missed), run_time=beats(1))  # the 65th bounces off
        self.remove(trail)
        self.cap("A 65th concurrent fault would be missed; our runs recorded no misses.", 2)
        gauge = m.Arc(radius=0.8, start_angle=m.PI, angle=-m.PI, color=MUTED, stroke_width=6).move_to([4.8, 0.9, 0])
        q = m.Text("?", font_size=40, color=GOLD).move_to(gauge.get_center() + m.DOWN * 0.15)
        g_lab = m.Text("probe overhead: not measured", font_size=18, color=MUTED).next_to(gauge, m.DOWN, buff=0.4)
        others = m.VGroup(*[m.Text(t, font_size=20, color=MUTED) for t in [
            "Live counts start when a target is selected; -f follows real_parent up to 64 levels.",
            "Tested on one VM only: Linux 6.8 · ARM64. No x86_64, no other kernels.",
        ]]).arrange(m.DOWN, buff=0.18).move_to([0, -1.6, 0])
        self.play(m.Create(gauge), m.Write(q), m.Write(g_lab), run_time=beats(2))
        self.play(m.LaggedStart(*[m.Write(o) for o in others], lag_ratio=0.6), run_time=beats(3))
        self.cap("What the evidence does not cover, yet.", 2)
        self.play(m.FadeOut(tok), m.FadeOut(slots), m.FadeOut(gauge), self.hide(s_lab, missed, q, g_lab, others))

        board = [self.board_title, self.board_labels, *self.board_live]
        frozen = [self.freeze(b, mk) for b, mk in zip(self.board_live, self.board_makes)]
        self.band_out()
        self.play(self.hide(self.board_title, self.board_labels, *frozen), run_time=BAR)
        # the E7 run as a 3D timeline: x is time, blue = address space (VmSize), gold = RAM in use (RSS)
        vsize = [2.2, 66.2, 66.2, 66.2, 98.2, 98.2, 2.2, 2.2]
        rss = [1.4, 2.6, 65.4, 65.4, 97.2, 97.2, 1.3, 1.3]
        steps = ["start", "anon:64", "touch", "", "file:32", "read", "free", ""]
        h = lambda mb: max(0.04, mb / 98.2 * 2.3)

        def bar(i, mb, y, col, op):
            return m.Prism(dimensions=[0.7, 0.6, h(mb)]).set_color(col).set_opacity(op).move_to([-3.5 + i, y, h(mb) / 2])
        vb = [bar(i, v, 0.5, BLUE, 0.45) for i, v in enumerate(vsize)]
        rb = [bar(i, r, -0.4, GOLD, 0.95) for i, r in enumerate(rss)]
        ticks = [m.Text(t, font_size=18, color=MUTED).move_to([-3.5 + i, -1.2, 0]) for i, t in enumerate(steps) if t]
        grid = []
        for mb in (0, 50, 100):
            z = h(mb) if mb else 0.0
            grid.append(m.Line([-4.0, 0.85, z], [4.0, 0.85, z], color=MUTED, stroke_width=1, stroke_opacity=0.5))
            grid.append(m.Text(f"{mb} MB", font_size=18, color=MUTED).rotate(m.PI / 2, axis=m.RIGHT).move_to([-4.6, 0.85, z]))
        legend = m.VGroup(m.Text("E7 · address space", font_size=22, color=BLUE), m.Text("RAM in use", font_size=22, color=GOLD)
                          ).arrange(m.RIGHT, buff=0.6).to_corner(m.UR, buff=0.4)
        self.pin(legend)
        self.move_camera(phi=62 * m.DEGREES, theta=-70 * m.DEGREES, frame_center=[0, -1.3, 1.0], run_time=beats(2))  # lift the bars clear of the summary
        self.play(self.show(legend, *ticks, *grid, run_time=beats(2)))
        for i in range(len(vsize)):  # one sample per beat: VmSize jumps first, RSS catches up after the touch
            self.sfx("click", -10)  # one sample per beat, one click per sample
            self.play(m.FadeIn(vb[i], shift=m.OUT * 0.3), m.FadeIn(rb[i], shift=m.OUT * 0.3), run_time=beats(1))
        self.begin_ambient_camera_rotation(rate=0.06)
        self.wait(beats(3))
        self.stop_ambient_camera_rotation()
        self.cap("Mapping grows the address space at once; RAM follows only as pages fault in.", 2)
        # flatten: the 3D bars become the report's 2D line chart (Figure 7)
        pts = lambda vals: [[-3.5 + i, -0.9 + v / 98.2 * 2.6, 0] for i, v in enumerate(vals)]
        self.move_camera(phi=0, theta=-90 * m.DEGREES, frame_center=[0, 0, 0],
                         added_anims=[*[m.FadeOut(g_) for g_ in grid if not isinstance(g_, m.Text)],
                                      self.hide(*[g_ for g_ in grid if isinstance(g_, m.Text)], *ticks, run_time=beats(1))],
                         run_time=beats(2))
        dots = [m.Dot(pt, radius=0.07, color=BLUE) for pt in pts(vsize)] + [m.Dot(pt, radius=0.07, color=GOLD) for pt in pts(rss)]
        self.play(*[m.FadeTransform(b_, d_) for b_, d_ in zip(vb + rb, dots)], run_time=beats(2))
        vline = m.VMobject(color=BLUE, stroke_width=4).set_points_as_corners(pts(vsize))
        rline = m.VMobject(color=GOLD, stroke_width=4).set_points_as_corners(pts(rss))
        axis = m.Line([-4.0, -0.9, 0], [4.2, -0.9, 0], color=MUTED, stroke_width=1.5)
        fig = m.Text("as in Figure 7 of the report · time →", font_size=16, color=MUTED).next_to(axis, m.DOWN, buff=0.12)
        self.play(m.Create(vline), m.Create(rline), m.Create(axis), m.Write(fig), run_time=beats(2))
        summary = m.VGroup(*[
            m.VGroup(m.Text(a, font_size=22, color=INK), m.Text(b, font_size=18, color=MUTED), m.Text(c, font_size=18, color=GREEN)).arrange(m.RIGHT, buff=0.35)
            for a, b, c in [("regions", "walk every VMA", "= /proc/<pid>/maps"),
                            ("address space", "add their sizes", "= VmSize"),
                            ("minor, major", "probe handle_mm_fault()", "= /proc/<pid>/stat, getrusage()")]
        ]).arrange(m.DOWN, buff=0.22, aligned_edge=m.LEFT).move_to([0, -2.3, 0])
        self.pin(summary)
        self.play(self.show(summary), run_time=beats(4))
        self.cap("Four numbers, each checked against Linux itself.", 2)
        self.cap(f"pfcount and pfstat · {GROUP} · CPE333 Mini-Project 2", 2)
        self.play(*[m.FadeOut(x) for x in dots + [vline, rline, axis]], self.hide(summary, legend, fig, self.caption_mob, self.tag),
                  m.FadeOut(self.tux), run_time=BAR)
        self.caption_mob = None
        self.move_camera(phi=0, theta=-90 * m.DEGREES, frame_center=[0, 0, 0], run_time=beats(2))
        credits = m.VGroup(*[m.Text(t, font_size=18, color=MUTED) for t in [
            f"Group {GROUP}",
            *[f"{sid}  {n}" for sid, n in MEMBERS],
            "Submitted to Asst. Prof. Rajchawit Sarochawikasit · CPE333, KMUTT",
            "Images: Wikimedia Commons, see assets/SOURCES.md",
            "Hard disk: Matthew Field · Tux: Larry Ewing, Simon Budig, Garrett LeSage",
        ]]).arrange(m.DOWN, buff=0.2)
        self.play(self.show(credits), run_time=BAR)
        self.wait(beats(8))
