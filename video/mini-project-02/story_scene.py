"""Mini-Project 02 video, told in the order of REPORT.md (see STORYBOARD.md).

One world for the whole film: the process's memory as a ribbon of blocks across the
top, the kernel as a dark band across the bottom, a scoreboard top right, and one gold
fault token that travels between them. No arrows. Every timing is in beats of a 96 BPM
grid, so music and voice can be laid on later. Numbers come from results/. Run:
    manimgx render story_scene.py Story
"""

import math
import random
from pathlib import Path

import manimgx as m


m.config.background_color = "#0A1020"
ASSETS = Path(__file__).resolve().parent / "assets"  # credits: assets/SOURCES.md

INK, MUTED = "#EAF0F7", "#8DA2BA"
BLUE, GOLD, GREEN, RED, GREY = "#4DA3FF", "#F5B841", "#5BD19A", "#FF6B6B", "#6B7A90"
PANEL, BAND = "#121C2F", "#05080F"
B = 0.46  # one beat (~130 BPM); change this alone to retime, keep the film >= 7 min
BAR = 4 * B
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
        self.opening()
        self.analogies()
        for label, act in [("1 · Goal", self.goal), ("2 · What a page fault is", self.background),
                           ("4.1 · Counting regions", self.regions_walk), ("4.2 · Counting faults", self.fault_counting),
                           ("4.5 · Watching it run", self.demo), ("6 · Experiments", self.experiments),
                           ("7 · Checks and findings", self.checks), ("9 · Summary", self.ending)]:
            self.chapter(label)
            act()

    def chapter(self, label: str):
        """A small chapter tag, top left, rewritten in place; the camera carries the cut."""
        tag = m.Text(label, font_size=20, color=MUTED).to_corner(m.UL, buff=0.35)
        self.pin(tag)
        old = getattr(self, "tag", None)
        self.play(*([self.hide(old, run_time=beats(1))] if old else []), m.Write(tag, run_time=beats(2)))
        self.tag = tag

    def band_in(self):
        if not self.band_on:
            self.play(m.FadeIn(self.band), m.Create(self.band_edge), m.FadeIn(self.band_lab), self.tux.animate.move_to(self.TUX_BAND), run_time=beats(2))
            self.band_on = True

    def band_out(self):
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
        line = m.Text(text, font_size=26, color=INK).move_to([0, CAPTION_Y, 0])
        self.add_subcaption(text, bars * BAR)
        if self.caption_mob is not None:
            self.play(self.hide(self.caption_mob, run_time=beats(1)))
        self.pin(line)
        self.play(self.show(line, run_time=beats(3)))
        self.caption_mob = line
        self.wait(max(0.0, bars * BAR - beats(4)))

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
        glows = []
        for k in keys:
            y = 3.55 - 0.38 * (list(self.vals).index(k) + 1)
            dot = m.Dot([6.0, y, 0], radius=0.01)
            self.pin(dot)
            glows.append(m.Flash(dot, color=GREEN, line_length=0.15, flash_radius=0.45))
        self.play(*glows, run_time=beats(2))
        return []

    def board_title_to(self, text: str):
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
        self.play(m.Write(title), run_time=beats(4))
        self.play(self.show(sub, grp, run_time=beats(3)))
        self.play(m.LaggedStart(*[m.Write(n) for n in names], lag_ratio=0.35), run_time=beats(6))
        self.wait(beats(4))
        self.play(self.hide(title, sub, grp, names, run_time=beats(3)))
        pages = m.VGroup(*[m.Square(0.9, color=MUTED, stroke_width=2, fill_color=GOLD, fill_opacity=0) for _ in range(8)])
        pages.arrange(m.RIGHT, buff=0.3).move_to([0, 0.4, 0])
        self.play(m.LaggedStart(*[m.Create(p) for p in pages], lag_ratio=1), run_time=beats(8))
        self.cap("mmap() and brk() reserve address space. No RAM is given yet.", 2)
        self.cap("Physical pages are assigned lazily, on first access.", 2)
        tok, trail = self.token([-6.5, 2.4, 0])
        self.play(tok.animate.move_to(pages[0].get_center()), run_time=beats(4))
        dim = m.Rectangle(width=14.4, height=8.2, stroke_width=0, fill_color="#000000", fill_opacity=0.55)
        self.play(m.FadeIn(dim), run_time=beats(1))  # the program pauses
        self.play(m.FadeOut(dim), m.Flash(pages[0], color=GOLD), pages[0].animate.set_fill(GOLD, opacity=0.9),
                  m.FadeOut(tok), run_time=beats(3))
        self.remove(trail)
        self.cap("First access traps into the kernel: a page fault.", 3)
        self.play(m.LaggedStart(*[p.animate.set_fill(GOLD, opacity=0.9) for p in pages[1:]], lag_ratio=1), run_time=beats(8))
        self.play(self.hide(pages))

    # ---- Act 1 · what we report ---------------------------------------------------

    def analogies(self):
        self.scoreboard("process: sleep")
        self.cap("pfcount reports four numbers for one process, each checked against Linux.", 3)

    def grow(self, mob):
        return m.FadeIn(mob, shift=m.UP * 0.3)

    # ---- Act 2 · the goal and the three parts (REPORT §1) ------------------------

    def goal(self):
        self.build_world()
        self.ribbon = ribbon_blocks(REGIONS)
        self.ribbon_lab = m.Text("sleep · its memory, one block per region", font_size=20, color=MUTED).move_to([-3.2, RIBBON_Y + 0.6, 0])
        self.play(m.LaggedStart(*[m.FadeIn(b, shift=m.UP * 0.2) for b in self.ribbon], lag_ratio=0.25),
                  self.show(self.ribbon_lab), run_time=beats(8))
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
        self.play(m.TransformFromCopy(src, big), m.Indicate(src), run_time=BAR)
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
        self.play(t1.animate.move_to(quick.get_center()), quick.animate.set_fill(GREEN, opacity=0.9),
                  t2.animate.move_to(disk.get_center()), run_time=beats(2))
        self.play(m.FadeOut(t1), run_time=beats(1))
        self.wait(beats(2))  # the slow one is still waiting on the disk
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
        self.play(self.grow(walk_code[0]), run_time=beats(2))
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
        self.play(walk.animate.set_value(n), run_time=beats(24), rate_func=m.linear)
        self.move_camera(phi=0, run_time=beats(2))
        self.vals["regions"].clear_updaters()
        self.vals["size"].clear_updaters()
        self.remove(self.vals["regions"], self.vals["size"])
        self.remove(scan)
        self.run_line(walk_code, 6, bars=1)
        self.play(m.FadeOut(walk_code, shift=m.UP * 0.3), run_time=beats(2))

        maps = m.Text("/proc/<pid>/maps: 30 lines · VmSize: 5.6 MB", font_size=22, color=GREEN).move_to([0, 0.3, 0])
        self.play(self.show(maps))
        ticks = self.board_tick("regions", "size")
        self.cap("30 regions, 5.6 MB: exactly what Linux itself reports.", 3)
        for blk in self.ribbon:
            blk.clear_updaters()
        self.play(self.hide(maps, *ticks))

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
        self.play(m.FadeIn(gate), self.show(gate_lab, *[w[0] for w in wells], *[w[1] for w in wells]), run_time=BAR)
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
        term = m.RoundedRectangle(corner_radius=0.12, width=7.6, height=2.0, stroke_color=MUTED, stroke_width=1,
                                  fill_color="#03060C", fill_opacity=1).move_to([-2.9, -0.15, 0])
        cmd_words = "$ sudo tools/pfstat -w 0.5 -- tests/faultgen anon:64 file:big.bin free".split(" ")
        cmd = m.VGroup(*[m.Text(w, font_size=18, color=GREEN) for w in cmd_words]).arrange(m.RIGHT, buff=0.12)
        cmd.move_to(term).align_to(term, m.UP).shift(m.DOWN * 0.25 + m.RIGHT * 0.05)
        self.board_title_to("demo run · PID 2508")
        self.play(m.FadeIn(term), run_time=beats(2))
        self.play(m.LaggedStart(*[m.Write(w) for w in cmd], lag_ratio=1), run_time=beats(len(cmd)))

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
        for k, v in [("regions", 16), ("size", 2.2 * 1024), ("minor", 0), ("major", 0)]:
            self.vals[k].set_value(v)
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
        self.play(m.LaggedStart(*[m.AnimationGroup(m.FadeIn(c), d.animate.move_to(disk.get_center()).set_opacity(0))
                                  for c, d in zip(fcells, drops)], lag_ratio=1),
                  self.vals["major"].animate.set_value(8193), self.vals["minor"].animate.set_value(16521), run_time=beats(8), rate_func=m.linear)
        self.cap("Read a cold 32 MB file: one trip to the disk per page. 8,193 major.", 3)

        # free: both blocks leave, the map shrinks back
        self.play(m.FadeOut(anon, cells, fil, fcells, *drops, shift=m.UP * 0.4),
                  self.vals["regions"].animate.set_value(16), self.vals["size"].animate.set_value(2.2 * 1024), run_time=BAR)
        out = m.VGroup(*[m.Text(t, font_size=18, color=c) for t, c in [
            ("Minor page faults   16,521   match vs getrusage()", INK),
            ("Major page faults    8,193   match vs getrusage()", INK)]]).arrange(m.DOWN, buff=0.12, aligned_edge=m.LEFT)
        out.next_to(cmd, m.DOWN, buff=0.35).align_to(cmd, m.LEFT)
        self.play(self.show(out), run_time=BAR)
        ticks = self.board_tick("minor", "major")
        self.cap("Freed: back to 16 regions. 16,521 and 8,193 match getrusage() after the baseline.", 3)
        self.play(self.hide(term, cmd, out, *ticks), m.FadeOut(disk))
        self.band_out()

    # ---- Act 7 · experiments on one stage (REPORT §6.2) -----------------------------

    def experiments(self):
        """Four experiments race on one floor: each faulted tile rises; the counts end side by side."""
        self.play(m.FadeOut(self.ribbon), self.hide(self.ribbon_lab), m.FadeOut(self.key), run_time=beats(2))
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("E3-E6 · faultgen")
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
        self.play(*[m.FadeIn(g) for g in floor], self.show(*labels), run_time=BAR)
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
        self.play(e3, e5, e4, e6, *[c.animate.set_value(r[2]) for c, r in zip(counts, rows)],
                  run_time=beats(16), rate_func=m.linear)
        self.cap("Same 32 MiB file: cold random reads fault on every page (8,193); readahead needs 2.", 3)
        self.cap("Warm cache + fault-around: 652. THP: 188 minor vs 16,538 for the same 64 MiB in E2.", 3)
        self.begin_ambient_camera_rotation(rate=0.04)
        self.wait(BAR)
        self.stop_ambient_camera_rotation()
        frozen = [self.freeze(n_, lambda c=c, g=g, r=r: m.Text(f"{c.get_value():,.0f} {r[3]}", font_size=22, color=r[4]).next_to(g, m.RIGHT, buff=0.3))
                  for n_, c, g, r in zip(nums, counts, floor, rows)]
        self.play(*[m.FadeOut(g) for g in floor], self.hide(*labels, *frozen))
        self.move_camera(phi=0, theta=-90 * m.DEGREES, zoom=1.0, frame_center=[0, 0, 0], run_time=beats(2))

    # ---- Act 8 · checks and findings (REPORT §6.1, §7) --------------------------------

    def checks(self):
        # E1 (e1a, e1b): every number pfstat prints, beside the number Linux prints for it
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("E1 · pfstat vs /proc")
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
            self.play(self.show(lab, *[c[0] for c in cells], run_time=beats(2)))  # pfstat writes its number...
            self.play(*[m.FadeIn(c[1], shift=m.LEFT * 0.3) for c in cells], run_time=beats(1))  # ...Linux's lands beside it
            self.play(*[c[0].animate.set_color(GREEN) for c in cells], *[c[1].animate.set_color(GREEN) for c in cells], run_time=beats(1))
            lines.append(m.VGroup(lab, *[x for c in cells for x in c]))
        self.cap("E1 · every number matches what Linux itself reports, for sleep and for PID 1.", 3)
        self.play(self.hide(*head, *sub, *lines))

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
        self.play(self.show(q, run_time=beats(2)), m.Flash(tp, color=RED), run_time=beats(2))  # it fires before the work: no answer yet
        self.cap("F3 · the suggested tracepoint fires on entry, before the kernel knows the answer.", 3)
        work = m.Rectangle(width=4.0, height=0.4, stroke_color=BLUE, stroke_width=1, fill_color=BLUE, fill_opacity=0.15).move_to([0.45, y, 0])
        work_lab = m.Text("kernel handles it: page cache or disk", font_size=16, color=BLUE).next_to(work, m.DOWN, buff=0.08)
        self.play(m.FadeIn(work), self.show(work_lab, run_time=beats(1)), tok.animate.move_to(work.get_center()), run_time=beats(2))
        self.play(tok.animate.set_fill(GREEN), m.Flash(work, color=GREEN), run_time=beats(1))
        self.play(tok.animate.move_to(kp.get_center()), run_time=beats(2))
        a_ = m.Text("minor", font_size=20, color=GREEN).next_to(kp_lab, m.UP, buff=0.12)
        self.play(self.show(a_, run_time=beats(2)), m.Flash(kp, color=GREEN), run_time=beats(2))
        self.cap("A kretprobe fires on return, sees the result, and works on arm64 too.", 3)
        self.remove(trail)
        self.play(m.FadeOut(tok), self.hide(track, tp, kp, enter, leave, tp_lab, kp_lab, q, work, work_lab, a_))
        self.band_out()

        # post-merge regression suite (report Table 8): every check runs at once and lands on PASS
        self.board_title_to("post-merge regression")
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
        self.play(m.LaggedStart(*[m.FadeIn(g, shift=m.UP * 0.2) for g in grid], lag_ratio=0.15), run_time=beats(3))
        self.add(*[n_[2] for n_ in nums])
        self.play(*[tr.animate.set_value(n) for tr, n, _ in nums], run_time=beats(4), rate_func=m.linear)
        self.play(m.LaggedStart(*[g[0].animate.set_stroke(GREEN, width=2.5) for g in grid], lag_ratio=0.12),
                  *[m.Flash(g[0].get_corner(m.UR) + [-0.25, -0.25, 0], color=GREEN, flash_radius=0.25) for g in grid], run_time=beats(3))
        self.cap("Six lifecycle and concurrency checks after merge: all passed.", 2)
        self.play(*[m.FadeOut(g, shift=m.DOWN * 0.2) for g in grid], *[m.FadeOut(n_[2]) for n_ in nums], run_time=beats(2))

        # F7 (e8d, e8e): gcc's own faults vs getrusage(), which also counts the children it waited for
        for k in self.vals:
            self.vals[k].set_value(-1)
        self.board_title_to("gcc -O2 faultgen.c")
        for k, v in [("regions", 21), ("size", 6.6 * 1024), ("minor", 0), ("major", 0)]:
            self.vals[k].set_value(v)
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
        self.play(m.GrowFromEdge(ours, m.LEFT), self.vals["minor"].animate.set_value(287), self.show(ours_lab, run_time=beats(2)), run_time=beats(2))
        self.play(m.FadeIn(gap), self.show(gap_lab, run_time=beats(2)), run_time=beats(2))
        self.cap("F7 · counting gcc alone gives 287: 5,700 below getrusage().", 3)

        # where the rest lives: gcc forks the real workers
        names = ["cc1", "as", "collect2", "ld"]
        kids = [ribbon_blocks(REGIONS[:10], y=0.45, width=2.4, height=0.36).set_x(x) for x in (-4.5, -1.5, 1.5, 4.5)]
        k_labs = [m.Text(n, font_size=18, color=MUTED).next_to(k, m.UP, buff=0.08) for n, k in zip(names, kids)]
        for k, l in zip(kids, k_labs):  # each child splits off from the parent, one per beat
            self.play(m.TransformFromCopy(parent, k), self.show(l, run_time=beats(1)), run_time=beats(1))
        self.cap("The children it waits for do the work, and wait4() adds theirs in.", 3)

        # -f: the probe also counts any process whose ancestor is the target
        self.board_title_to("gcc -O2 faultgen.c  ·  pfstat -f")
        self.play(*[k.animate.set_fill(GOLD, opacity=0.95) for k in kids], run_time=beats(1))
        fill = m.Rectangle(width=W * 5971 / total, height=0.42, stroke_width=0, fill_color=GOLD, fill_opacity=0.95)
        fill.move_to([X0 + fill.width / 2, -0.9, 0])
        drops = [k.copy() for k in kids]
        self.play(*[d.animate.scale(0.2).move_to(fill.get_center()).set_opacity(0) for d in drops],
                  m.Transform(ours, fill), m.FadeOut(gap), self.hide(gap_lab, run_time=beats(2)),
                  self.vals["minor"].animate.set_value(5971), run_time=beats(4))
        self.remove(*drops)
        ours_lab2 = m.Text("pfstat -f: 5,971 (separate run)", font_size=20, color=GREEN).move_to(ours_lab, aligned_edge=m.LEFT)
        self.play(m.ReplacementTransform(ours_lab, ours_lab2), run_time=beats(2))
        self.board_tick("minor")
        self.cap("With -f the children count too: 5,971, matching wait4() for that run.", 3)
        self.play(self.hide(parent, p_lab, *kids, *k_labs, ref, ref_lab, ours, ours_lab2))

    # ---- Act 9 · limits and the end (REPORT §8–9) -----------------------------------

    def ending(self):
        limits = m.VGroup(*[m.Text(t, font_size=22, color=MUTED) for t in [
            "Live counts start when you pick the process.",
            "Children are followed through their parent only.",
            "The probe's overhead was not measured.",
            "Tested on Linux 6.8, arm64, only.",
        ]]).arrange(m.DOWN, buff=0.25, aligned_edge=m.LEFT).move_to([-1.0, 0.2, 0])
        self.play(m.LaggedStart(*[m.Write(t) for t in limits], lag_ratio=1), run_time=beats(16))
        self.cap("What it does not do, yet.", 2)
        self.play(self.hide(limits))

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
            self.play(m.FadeIn(vb[i], shift=m.OUT * 0.3), m.FadeIn(rb[i], shift=m.OUT * 0.3), run_time=beats(1))
        self.cap("Mapping grows the address space at once; RAM follows only as pages fault in.", 3)
        summary = m.VGroup(*[
            m.VGroup(m.Text(a, font_size=22, color=INK), m.Text(b, font_size=18, color=MUTED), m.Text(c, font_size=18, color=GREEN)).arrange(m.RIGHT, buff=0.35)
            for a, b, c in [("regions", "walk every VMA", "= /proc/<pid>/maps"),
                            ("address space", "add their sizes", "= VmSize"),
                            ("minor, major", "probe handle_mm_fault()", "= /proc/<pid>/stat, getrusage()")]
        ]).arrange(m.DOWN, buff=0.22, aligned_edge=m.LEFT).move_to([0, -2.3, 0])
        self.pin(summary)
        self.play(self.show(summary), run_time=beats(4))
        self.begin_ambient_camera_rotation(rate=0.05)
        self.cap("Four numbers, each checked against Linux itself.", 3)
        self.cap("pfcount and pfstat · CPE333 Mini-Project 02", 3)
        self.stop_ambient_camera_rotation()
        self.play(*[m.FadeOut(x) for x in vb + rb], self.hide(summary, legend, *ticks, *grid, self.caption_mob, self.tag), m.FadeOut(self.tux), run_time=BAR)
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
