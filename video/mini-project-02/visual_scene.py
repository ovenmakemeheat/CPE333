"""Visual cut of the Mini-Project 02 video: plots, diagrams and 3D.

Every text is written in the way the title is. A rail at the top names the chapter; each
section ends by handing its object or question to the next. Every number comes from
results/ (e1a, e3, e4, e5, e6, e7, e8). Run:
    manimgx render visual_scene.py MiniProject02Visual
"""

import math
from pathlib import Path

import manimgx as m


m.config.background_color = "#0A1020"
ASSETS = Path(__file__).resolve().parent / "assets"  # images from Wikimedia Commons: see assets/SOURCES.md

INK, MUTED = "#EAF0F7", "#8DA2BA"
BLUE, GOLD, GREEN, RED, GREY = "#4DA3FF", "#F5B841", "#5BD19A", "#FF6B6B", "#6B7A90"
PANEL = "#121C2F"
CAPTION_Y = -3.25
WRITE_TIME = 1.6  # every text is written in, the way the title is
UNWRITE_TIME = 0.8  # and written out the same way
SHAPE_TIME = 1.0  # shapes fade or draw in and out

CHAPTERS = [
    "The question", "The tool", "One fault", "Address space", "Counting regions",
    "Counting faults", "Timing the probe", "The timeline", "Checks", "Edge cases",
]

# results/e1a-report-sleep.txt: the 30 regions of `sleep`, in address order: (kind, size in KB)
REGIONS = [
    ("file", 20), ("file", 4), ("file", 4), ("heap", 132),
    ("file", 2988), ("file", 356), ("file", 1640), ("file", 76), ("file", 12), ("file", 8),
    ("anon", 48), ("file", 156), *[("file", 4)] * 10, ("file", 28), ("file", 4),
    ("anon", 8), ("special", 8), ("special", 4), ("file", 8), ("file", 8), ("stack", 132),
]
KIND_COLOR = {"file": BLUE, "anon": GOLD, "heap": GREEN, "stack": GREEN, "special": GREY}

# results/e7-timeline.txt: watch mode, one sample every 0.5 s (the 0 s row is the forked copy, left out)
TIMES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
VSIZE = [2.2, 66.2, 66.2, 66.2, 98.2, 98.2, 2.2, 2.2]  # MB
RSS = [1.4, 7.9, 65.4, 65.4, 97.2, 97.2, 1.3, 1.3]  # MB
MAJOR = [1, 1, 1, 1, 8193, 8193, 8193, 8193]


def units(mob: m.Mobject) -> list[m.Mobject]:
    """The pieces an animation treats as one: each text, and each shape that holds no text."""
    if isinstance(mob, m.Text) or not any(isinstance(s, m.Text) for s in mob.get_family()):
        return [mob]
    return [unit for sub in mob.submobjects for unit in units(sub)]


class MiniProject02Visual(m.ThreeDScene):
    def construct(self) -> None:
        self.caption_mob = None
        self.rail: list[m.Mobject] = []  # the chapter rail: track, progress, label
        self.add(m.SunLight(4 * m.UP + 3 * m.OUT), m.AmbientLight(intensity=0.35))
        self.set_camera_orientation(phi=0, theta=-90 * m.DEGREES)  # top-down: plots read as flat 2D
        self.title_card()
        self.hook()
        cpu = self.project_map()
        self.fault_path(cpu)
        self.demand_paging()
        bars, head, legend = self.address_space_3d()
        self.counting_walk(bars, head, legend)
        self.fault_counters()
        self.probe_timing()
        self.timeline_charts()
        self.experiments()
        self.validation()
        self.hard_cases()
        self.closing()

    # ---- how things appear and leave: text is written in and out, as the title is ----

    def show(self, *mobs: m.Mobject, shift=None, run_time: float | None = None) -> m.AnimationGroup:
        """Bring mobjects in: each text is written in; each shape fades in."""
        anims = []
        for unit in (u for mob in mobs for u in units(mob)):
            if isinstance(unit, m.Text):
                anims.append(m.Write(unit, run_time=run_time or WRITE_TIME))
            elif shift is None:
                anims.append(m.FadeIn(unit, run_time=run_time or SHAPE_TIME))
            else:
                anims.append(m.FadeIn(unit, shift=shift, run_time=run_time or SHAPE_TIME))
        return m.AnimationGroup(*anims)

    def draw(self, *mobs: m.Mobject, run_time: float | None = None) -> m.AnimationGroup:
        """Like show, but lines and shapes are drawn in: for charts, axes and rules."""
        anims = []
        for unit in (u for mob in mobs for u in units(mob)):
            if isinstance(unit, m.Text):
                anims.append(m.Write(unit, run_time=run_time or WRITE_TIME))
            else:
                anims.append(m.Create(unit, run_time=run_time or SHAPE_TIME))
        return m.AnimationGroup(*anims)

    def hide(self, *mobs: m.Mobject, run_time: float | None = None) -> m.AnimationGroup:
        """Take mobjects out: each text is written out; each shape fades out."""
        anims = []
        for unit in (u for mob in mobs for u in units(mob)):
            if isinstance(unit, m.Text):
                anims.append(m.Unwrite(unit, run_time=run_time or UNWRITE_TIME, remover=True))
            else:
                anims.append(m.FadeOut(unit, run_time=run_time or SHAPE_TIME))
        return m.AnimationGroup(*anims)

    def pin(self, *mobs: m.Mobject) -> None:
        """Pin mobjects to the screen before they are shown, so they hold still as the camera moves."""
        self.camera.add_fixed_in_frame_mobjects(*mobs)

    def write_live(self, *makes):
        """Write in texts that follow a value, then keep them live. Each make() builds its text."""
        statics = [make() for make in makes]
        self.play(self.show(*statics))
        self.remove(*statics)
        lives = [m.always_redraw(make) for make in makes]
        self.add(*lives)
        return lives

    def still(self, *pairs):
        """Swap live texts for still copies at their final values, so they can be hidden with the rest."""
        copies = []
        for live, make in pairs:
            self.remove(live)
            copy = make()
            self.add(copy)
            copies.append(copy)
        return copies

    # ---- the chapter rail, captions and shared building blocks ----------------

    def chapter(self, index: int) -> None:
        """A rail at the top: which chapter we are in, and how far through the story."""
        width = 14.2
        label = m.Text(f"{index + 1:02d} / {len(CHAPTERS)} · {CHAPTERS[index]}", font_size=20, color=MUTED)
        label.move_to([-5.6, 3.5, 0])
        fill_w = width * (index + 1) / len(CHAPTERS)
        fill = m.Rectangle(width=fill_w, height=0.05, stroke_width=0, fill_color=GOLD, fill_opacity=0.9)
        fill.move_to([-width / 2 + fill_w / 2, 3.85, 0])
        if not self.rail:
            track = m.Rectangle(width=width, height=0.05, stroke_width=0, fill_color=MUTED, fill_opacity=0.2)
            track.move_to([0, 3.85, 0])
            self.pin(track, fill, label)
            self.rail = [track, fill, label]
            self.play(m.FadeIn(track), self.show(fill, label))
            return
        self.pin(fill, label)
        self.play(self.hide(self.rail[2]), m.ReplacementTransform(self.rail[1], fill), self.show(label))
        self.rail[1], self.rail[2] = fill, label

    def cap(self, text: str, hold: float = 1.5) -> None:
        """A caption written in at the bottom, held, then replaced by the next one."""
        hold = max(hold, len(text) / 14)  # long enough to read: about 14 characters a second
        line = m.Text(text, font_size=26, color=INK).move_to([0, CAPTION_Y, 0])
        self.add_subcaption(text, WRITE_TIME + hold)
        if self.caption_mob is not None:
            self.play(self.hide(self.caption_mob, run_time=0.5))
        self.pin(line)
        self.play(self.show(line))
        self.caption_mob = line
        self.wait(hold)

    def clear_caption(self) -> None:
        """Take the caption away when its bridge is over, so it does not hang over the next section."""
        if self.caption_mob is not None:
            self.play(self.hide(self.caption_mob, run_time=0.5))
            self.caption_mob = None

    def box(self, title: str, sub: str, color: str, pos, width: float = 3.0, height: float = 1.5) -> m.VGroup:
        frame = m.RoundedRectangle(
            corner_radius=0.12, width=width, height=height, color=color,
            fill_color=PANEL, fill_opacity=0.95, stroke_width=2,
        )
        text = m.VGroup(
            m.Text(title, font_size=26, color=INK), m.Text(sub, font_size=19, color=MUTED)
        ).arrange(m.DOWN, buff=0.12)
        return m.VGroup(frame, text.move_to(frame)).move_to(pos)

    def pill(self, label: str, color: str, pos, width: float = 2.8) -> m.VGroup:
        frame = m.RoundedRectangle(
            corner_radius=0.3, width=width, height=0.7, color=color,
            fill_color=PANEL, fill_opacity=0.95, stroke_width=2,
        )
        return m.VGroup(frame, m.Text(label, font_size=22, color=INK).move_to(frame)).move_to(pos)

    def counter(self, title: str, color: str, pos):
        """A counter box: its title, and a number that follows its value. Returns (box, value, make)."""
        frame = m.RoundedRectangle(
            corner_radius=0.1, width=2.3, height=1.0, color=color,
            fill_color=PANEL, fill_opacity=0.95, stroke_width=2,
        ).move_to(pos)
        head = m.Text(title, font_size=20, color=MUTED).move_to([pos[0], pos[1] + 0.22, 0])
        value = m.ValueTracker(0)

        def make() -> m.Text:
            return m.Text(f"{value.get_value():,.0f}", font_size=30, color=color).move_to([pos[0], pos[1] - 0.2, 0])

        return m.VGroup(frame, head), value, make

    def bars(self, values, names, colors, origin, width: float, height: float, top: float, short: bool = False) -> m.VGroup:
        """A bar chart drawn from rectangles: a value over each bar, a name under it, on a baseline."""
        x0, y0 = origin
        slot = width / len(values)
        scale = height / top
        items = [m.Line([x0, y0, 0], [x0 + width, y0, 0], color=MUTED, stroke_width=1.5)]
        for i, (v, name, c) in enumerate(zip(values, names, colors)):
            x = x0 + slot * (i + 0.5)
            h = max(v * scale, 0.03)
            value = f"{v / 1000:.1f}k" if short and v >= 1000 else f"{v:,}"
            items.append(m.Rectangle(width=slot * 0.56, height=h, stroke_width=0, fill_color=c, fill_opacity=0.85).move_to([x, y0 + h / 2, 0]))
            items.append(m.Text(value, font_size=18 if short else 20, color=c).move_to([x, y0 + h + 0.22, 0]))
            items.append(m.Text(name, font_size=18, color=MUTED).move_to([x, y0 - 0.28, 0]))
        return m.VGroup(*items)

    def region_bars(self) -> m.VGroup:
        bars = []
        for i, (kind, kb) in enumerate(REGIONS):
            h = 0.35 + 0.55 * math.log10(kb)  # log scale: 4 KB and 3 MB both stay visible
            bar = m.Prism(dimensions=[0.16, 0.5, h]).set_color(KIND_COLOR[kind])
            bars.append(bar.move_to([-3.4 + i * 0.235, 0, h / 2]))
        return m.VGroup(*bars)

    # ---- sections ---------------------------------------------------------

    def title_card(self) -> None:
        title = m.Text("Where the Memory Goes", font_size=60, color=INK).move_to([0, 0.7, 0])
        sub = m.Text("CPE333 · Mini-Project 02 · Virtual Memory", font_size=26, color=MUTED).move_to([0, -0.3, 0])
        self.play(self.show(title, run_time=2.5))
        self.play(self.show(sub))
        self.cap("Virtual memory, made visible: plots, diagrams and the numbers behind them.", hold=2)
        self.play(self.hide(title, sub))

    def hook(self) -> None:
        self.chapter(0)
        axes = m.Axes(x_range=[0, 8192, 2048], y_range=[0, 9000, 3000], x_length=9.0, y_length=4.0, tips=False)
        axes.move_to([0, 0.1, 0])
        x_ticks = m.VGroup(*[
            m.Text(f"{v:,}", font_size=18, color=MUTED).next_to(axes.c2p(v, 0), m.DOWN, buff=0.12)
            for v in range(0, 8193, 2048)
        ])
        y_ticks = m.VGroup(*[
            m.Text(f"{v:,}", font_size=18, color=MUTED).next_to(axes.c2p(0, v), m.LEFT, buff=0.12)
            for v in range(0, 9001, 3000)
        ])
        x_lab = m.Text("pages touched, in order (the 32 MB file is 8,192 pages)", font_size=20, color=MUTED)
        x_lab.next_to(x_ticks, m.DOWN, buff=0.2)
        y_lab = m.Text("major faults", font_size=20, color=MUTED).rotate(m.PI / 2).next_to(y_ticks, m.LEFT, buff=0.3)
        cold = axes.plot(lambda x: x, x_range=[0, 8192], color=RED)
        ahead = axes.plot(lambda x: 1, x_range=[0, 8192], color=GREEN)
        area = m.Polygon(axes.c2p(0, 0), axes.c2p(8192, 8192), axes.c2p(8192, 0), fill_color=RED, fill_opacity=0.12, stroke_width=0)
        cold_lab = m.Text("cold cache, random reads: one fault per page", font_size=20, color=RED).move_to(axes.c2p(2600, 8000))
        ahead_lab = m.Text("readahead on: about 1 fault in total", font_size=20, color=GREEN).move_to(axes.c2p(5200, 1200))

        pages = m.ValueTracker(0)
        runner = m.always_redraw(lambda: m.Dot(axes.c2p(pages.get_value(), pages.get_value()), radius=0.09, color=RED))

        def make_count() -> m.Text:
            return m.Text(f"major faults so far: {pages.get_value():,.0f}", font_size=26, color=RED).move_to([3.2, 2.3, 0])

        self.play(self.draw(axes, run_time=1.5), self.show(x_ticks, y_ticks, x_lab, y_lab, run_time=1.5))
        self.cap("Same 32 MB file, read two ways.", hold=0.5)
        (count,) = self.write_live(make_count)
        self.add(runner)
        self.play(self.show(cold_lab, run_time=1.0))
        self.play(m.Create(cold, rate_func=m.linear, run_time=4), pages.animate.set_value(8192), run_time=4)
        self.play(self.show(area))
        self.cap("Random reads, cold cache: one disk read per page. The count climbs.", hold=1.5)
        self.play(m.Create(ahead, run_time=2.5), self.show(ahead_lab))
        self.cap("With readahead the kernel fetches ahead, so the same file barely faults.", hold=2)
        self.cap("The shaded area is the faults. Who counts them? A small tool does.", hold=2)
        (count_end,) = self.still((count, make_count))
        self.remove(runner)
        self.play(self.hide(axes, x_ticks, y_ticks, x_lab, y_lab, cold, ahead, area, cold_lab, ahead_lab, count_end))

    def project_map(self) -> m.VGroup:
        self.chapter(1)
        kernel = m.RoundedRectangle(
            corner_radius=0.2, width=3.7, height=3.0, stroke_color=BLUE, stroke_width=1.5,
            fill_color=BLUE, fill_opacity=0.06,
        ).move_to([0, 1.0, 0])
        kernel_lab = m.Text("kernel space", font_size=20, color=BLUE).move_to([0.45, 2.62, 0])
        user_lab = m.Text("user space", font_size=20, color=MUTED).move_to([-4.4, 2.5, 0])
        tux = m.ImageMobject(str(ASSETS / "tux" / "Tux-on-disc.png")).scale_to_fit_height(0.5).move_to([-0.7, 2.62, 0])

        faultgen = self.box("faultgen", "a workload on purpose", GOLD, [-4.4, 1.0, 0], width=3.2)
        pfcount = self.box("pfcount", "counts faults here", BLUE, [0, 1.0, 0], width=2.9)
        pfstat = self.box("pfstat", "CLI: report and check", GREEN, [4.4, 1.0, 0], width=3.2)
        arrows = [
            m.Arrow(faultgen.get_right(), pfcount.get_left(), buff=0.1, color=MUTED),
            m.Arrow(pfcount.get_right(), pfstat.get_left(), buff=0.1, color=MUTED),
        ]
        arrow_labels = m.VGroup(
            m.Text("faults", font_size=18, color=MUTED).move_to([-2.15, 1.5, 0]),
            m.Text("reports", font_size=18, color=MUTED).move_to([2.2, 1.5, 0]),
        )
        self.play(self.show(kernel, kernel_lab, user_lab, tux), self.show(faultgen, pfcount, pfstat))
        self.play(*[m.GrowArrow(a) for a in arrows], self.show(arrow_labels))
        self.cap("Three parts: a workload in user space, a kernel module, and a CLI.", hold=1)

        dot = m.Dot(faultgen.get_center(), radius=0.14, color=GOLD)
        self.play(self.show(dot))
        self.play(dot.animate.move_to(pfcount.get_center()), run_time=1.2)
        self.cap("pfcount runs in the kernel, where the faults happen, so it counts them there.", hold=1)
        self.play(dot.animate.move_to(pfstat.get_center()), run_time=1.2)

        pills = [
            self.pill(label, color, [x, -1.5, 0])
            for label, color, x in [
                ("regions", BLUE, -4.5), ("address space", BLUE, -1.5),
                ("minor faults", GREEN, 1.5), ("major faults", RED, 4.5),
            ]
        ]
        self.play(m.LaggedStart(*[self.show(p, shift=m.DOWN * 0.2) for p in pills], lag_ratio=0.2))
        self.cap("Four numbers come out: regions, address space, minor and major faults.", hold=2)

        # the bridge: every fault starts with a process touching memory
        self.cap("Every fault starts with a process touching memory. Follow one.", hold=1)
        cpu = self.box("CPU", "touches memory", MUTED, [-5.4, 0.3, 0], width=2.4)
        self.play(
            m.ReplacementTransform(faultgen, cpu),
            self.hide(kernel, kernel_lab, user_lab, tux, pfcount, pfstat, *arrows, arrow_labels, dot, *pills),
        )
        return cpu

    def fault_path(self, cpu: m.VGroup) -> None:
        self.chapter(2)
        pt = self.box("page table", "no page here", GOLD, [-2.2, 0.3, 0], width=2.6)
        handler = self.box("handle_mm_fault()", "kernel fault path", BLUE, [1.8, 0.3, 0], width=3.6)
        minor = self.box("minor", "no I/O needed", GREEN, [5.3, 1.2, 0], width=2.8)
        major = self.box("major", "must read the disk", RED, [5.3, -0.8, 0], width=2.8)
        arrows = [
            m.Arrow(cpu.get_right(), pt.get_left(), buff=0.08, color=MUTED),
            m.Arrow(pt.get_right(), handler.get_left(), buff=0.08, color=MUTED),
            m.Arrow(handler.get_right(), minor.get_left(), buff=0.08, color=MUTED),
            m.Arrow(handler.get_right(), major.get_left(), buff=0.08, color=MUTED),
        ]
        cpu_img = m.ImageMobject(str(ASSETS / "cpu" / "80486_open-1920px.jpg")).scale_to_fit_height(1.2).move_to([-5.4, 1.95, 0])
        disk_img = m.ImageMobject(str(ASSETS / "disk" / "Hard_disk_platters_and_head-1920px.jpg")).scale_to_fit_width(1.7).move_to([5.3, -2.3, 0])
        self.play(self.show(pt, handler, minor, major, *arrows, cpu_img, run_time=1.2))
        self.cap("Step 1: the CPU touches an address. The page table is asked for it.", hold=0.8)

        dot = m.Dot(cpu.get_center(), radius=0.14, color=GOLD)
        self.play(self.show(dot))
        self.play(dot.animate.move_to(pt.get_center()), run_time=1.2)
        self.cap("Step 2: no page is mapped there, so the CPU traps into the kernel.", hold=0.5)
        self.play(dot.animate.move_to(handler.get_center()), run_time=1.2)
        self.cap("Step 3: handle_mm_fault() decides how to fill the page.", hold=0.5)
        self.play(dot.animate.move_to(minor.get_center()), run_time=1.2)
        self.play(m.Indicate(minor[0]))
        self.cap("Step 4, minor: no disk I/O. A zero-filled page, or one already cached.", hold=1)
        self.play(dot.animate.move_to(major.get_center()), run_time=1.5)
        self.play(m.Indicate(major[0]), self.show(disk_img))
        self.cap("Step 4, major: the page must come from disk, so the process waits.", hold=1.5)

        # the bridge: the handler is the function the probe times, so it becomes the timed span
        self.cap("This handler is the function the probe times next.", hold=1)
        span = m.Rectangle(width=5.0, height=0.6, stroke_width=0, fill_color=BLUE, fill_opacity=0.7).move_to([-0.5, 0, 0])
        span_lab = m.Text("handle_mm_fault() runs", font_size=22, color=INK).move_to(span)
        self.play(
            m.ReplacementTransform(handler, m.VGroup(span, span_lab)),
            self.hide(cpu, pt, minor, major, *arrows, dot, cpu_img, disk_img),
        )
        self.play(self.hide(span, span_lab))
        self.clear_caption()

    def demand_paging(self) -> None:
        self.chapter(3)
        cells = m.VGroup(*[
            m.Square(side_length=0.36, stroke_width=1, color=MUTED, fill_color=GOLD, fill_opacity=0)
            for _ in range(64)
        ])
        cells.arrange_in_grid(rows=8, cols=8, buff=0.06).move_to([-2.6, 0.0, 0])
        frame = m.SurroundingRectangle(cells, color=BLUE, buff=0.15)
        frame_lab = m.Text("mmap: 64 MB reserved", font_size=24, color=BLUE).next_to(frame, m.UP, buff=0.2)
        legend = m.VGroup(
            m.Text("outline: reserved, not in RAM", font_size=20, color=MUTED),
            m.Text("gold: resident, in RAM", font_size=20, color=GOLD),
        ).arrange(m.DOWN, buff=0.12).move_to([-2.6, -2.25, 0])
        resident = m.ValueTracker(0)

        def make_ram() -> m.Text:
            return m.Text(f"{resident.get_value():.0f} MB resident", font_size=40, color=GOLD).move_to([4.2, 1.4, 0])

        ram_img = m.ImageMobject(str(ASSETS / "ram" / "DDR-DIMM_512MB_PC3200-1920px.jpg")).scale_to_fit_width(3.4).move_to([4.2, -0.9, 0])
        (ram,) = self.write_live(make_ram)
        self.play(self.show(cells, frame, frame_lab, legend, ram_img))
        self.cap("mmap reserves 64 MB of address space. None of it is in RAM yet.", hold=1)

        # zoom into one cell: 256 pages, each a first-touch fault
        self.cap("Zoom into one 1 MB cell: it holds 256 pages of 4 KB each.", hold=1)
        pages = m.VGroup(*[
            m.Square(side_length=0.2, stroke_width=0.5, color=MUTED, fill_color=GOLD, fill_opacity=0)
            for _ in range(256)
        ])
        pages.arrange_in_grid(rows=16, cols=16, buff=0.02).move_to([-2.6, 0.0, 0])
        self.play(m.FadeOut(cells), m.FadeIn(pages))
        self.cap("First touch of a page is a fault: the kernel supplies a zero-filled page.", hold=1)
        self.play(
            m.LaggedStart(*[p.animate.set_fill(GOLD, opacity=0.9) for p in pages], lag_ratio=0.006),
            resident.animate.set_value(1),
            run_time=3,
        )
        self.cap("256 pages, 256 faults, 1 MB resident. The other 63 cells follow the same rule.", hold=1.5)

        # zoom back out: the first cell stays filled, the rest fill with their pages
        cells[0].set_fill(GOLD, opacity=0.9)
        self.play(m.FadeOut(pages), m.FadeIn(cells))
        fills = [c.animate.set_fill(GOLD, opacity=0.85) for c in cells[1:]]
        self.play(m.LaggedStart(*fills, lag_ratio=0.04), resident.animate.set_value(64), run_time=6)
        self.cap("64 MB resident after 16,384 faults. Address space was only a promise.", hold=2)

        self.cap("Zoom out: a process has many mappings, and each one is a region.", hold=1.5)
        (ram_end,) = self.still((ram, make_ram))
        self.play(self.hide(cells, frame, frame_lab, legend, ram_end, ram_img))

    def address_space_3d(self):
        self.move_camera(phi=64 * m.DEGREES, theta=-78 * m.DEGREES, run_time=2.5)
        bars = self.region_bars().shift(m.DOWN * 0.6)  # low enough to clear the pinned labels
        self.play(m.LaggedStart(*[m.FadeIn(b, shift=m.DOWN * 0.3) for b in bars], lag_ratio=0.04), run_time=3)

        head = m.VGroup(
            m.Text("sleep: 30 regions", font_size=30, color=INK),
            m.Text("5.6 MB of address space", font_size=26, color=MUTED),
        ).arrange(m.DOWN, buff=0.15, aligned_edge=m.LEFT).to_corner(m.UL, buff=0.9)
        kinds = [("file-backed", BLUE), ("anonymous", GOLD), ("heap, stack", GREEN), ("[vdso], [vvar]", GREY)]
        legend = m.VGroup(*[
            m.VGroup(
                m.Square(side_length=0.22, fill_color=c, fill_opacity=1, stroke_width=0),
                m.Text(t, font_size=22, color=INK),
            ).arrange(m.RIGHT, buff=0.15)
            for t, c in kinds
        ]).arrange(m.DOWN, buff=0.12, aligned_edge=m.LEFT).to_corner(m.UR, buff=0.9)
        scale_note = m.Text("height = log10 of the size", font_size=20, color=MUTED).next_to(legend, m.DOWN, buff=0.25, aligned_edge=m.RIGHT)
        self.pin(head, legend, scale_note)
        self.play(self.show(head, legend, scale_note))

        self.cap("Each bar is one region, a VMA. Its height is the log of its size.", hold=1.5)
        self.begin_ambient_camera_rotation(rate=0.12)
        self.cap("The tallest are the locale archive and libc: large, but only a few.", hold=3)
        self.stop_ambient_camera_rotation()
        self.cap("Flatten the bars into a list, and count each region in turn.", hold=1)
        return bars, m.VGroup(head, scale_note), legend

    def counting_walk(self, bars, head, legend) -> None:
        self.chapter(4)
        self.move_camera(phi=0, theta=-90 * m.DEGREES, zoom=1.0, run_time=1.5)
        n = len(REGIONS)
        seg_w = 12 / n
        walk = m.ValueTracker(0)
        segs = m.VGroup(*[
            m.Rectangle(width=seg_w * 0.9, height=0.9, stroke_width=0, fill_color=KIND_COLOR[k], fill_opacity=0.25)
            for k, _ in REGIONS
        ]).arrange(m.RIGHT, buff=seg_w * 0.1).move_to([0, 0.6, 0])
        for i, seg in enumerate(segs):
            seg.add_updater(lambda s, *_, i=i: s.set_fill(opacity=0.95 if walk.get_value() >= i + 1 else 0.25))

        cum = [0]
        for _, kb in REGIONS:
            cum.append(cum[-1] + kb)

        def count_make() -> m.Text:
            return m.Text(f"{min(int(walk.get_value()), n)}", font_size=52, color=INK).move_to([-3.4, -1.7, 0])

        def total_make() -> m.Text:
            return m.Text(f"{cum[min(int(walk.get_value()), n)]:,} KB", font_size=52, color=INK).move_to([3.4, -1.7, 0])

        def x_at(v: float) -> float:
            return -6 + v * seg_w

        cursor = m.always_redraw(lambda: m.Line(
            [x_at(walk.get_value()), -0.2, 0], [x_at(walk.get_value()), 1.6, 0], color=INK, stroke_width=4,
        ))
        # a running total under the regions, growing to the VmSize of the sleep process
        sum_bar = m.always_redraw(lambda: m.Rectangle(
            width=max(0.01, 12 * cum[min(int(walk.get_value()), n)] / cum[-1]), height=0.2,
            stroke_width=0, fill_color=GOLD, fill_opacity=0.9,
        ).move_to([-6 + 6 * cum[min(int(walk.get_value()), n)] / cum[-1], -0.35, 0]))
        target = m.Line([6.0, -0.6, 0], [6.0, 0.1, 0], color=GOLD, stroke_width=2)
        target_lab = m.Text("VmSize 5.6 MB", font_size=18, color=GOLD).move_to([4.7, -0.85, 0])

        labels = m.VGroup(
            m.Text("VMAs counted", font_size=22, color=MUTED),
            m.Text("size summed: vm_end - vm_start", font_size=22, color=MUTED),
        )
        count, total = self.write_live(count_make, total_make)
        labels[0].next_to(count, m.DOWN, buff=0.25)
        labels[1].next_to(total, m.DOWN, buff=0.25)

        # the bridge: the 3D bars flatten into the list the walk counts
        self.play(m.ReplacementTransform(bars, segs), self.hide(head, legend), self.show(labels))
        self.add(cursor, sum_bar, target)
        self.play(self.show(target_lab))
        self.cap("Walk the VMAs in address order: count each one, and add up its size.", hold=0.8)
        self.play(walk.animate.set_value(n), run_time=7, rate_func=m.linear)
        self.cap("30 regions, 5,684 KB in total: the VmSize of 5.6 MB.", hold=2)
        self.cap("Next: each fault is counted by the probe, at the moment it happens.", hold=1.5)
        self.remove(cursor, sum_bar)
        count_end, total_end = self.still((count, count_make), (total, total_make))
        self.play(self.hide(segs, labels, count_end, total_end, target, target_lab))

    def fault_counters(self) -> None:
        self.chapter(5)
        # lifetime: the live threads' counts, plus counts saved from exited ones (shapes only, no numbers)
        threads = [
            m.Rectangle(width=1.5, height=0.9, stroke_width=0, fill_color=c, fill_opacity=0.85).move_to([x, 1.8, 0])
            for c, x in [(BLUE, -5.6), (GREEN, -3.7), (MUTED, -1.8)]
        ]
        plus = m.VGroup(*[m.Text("+", font_size=34, color=MUTED).move_to([x, 1.8, 0]) for x in (-4.65, -2.75)])
        thread_labels = m.VGroup(*[
            m.Text(t, font_size=20, color=MUTED).next_to(r, m.DOWN, buff=0.15)
            for t, r in zip(["live thread", "live thread", "exited thread"], threads)
        ])
        eq = m.Text("=", font_size=34, color=MUTED).move_to([0.5, 1.8, 0])
        total = m.Rectangle(width=3.4, height=0.9, stroke_width=0, fill_color=GOLD, fill_opacity=0.9).move_to([3.0, 1.8, 0])
        total_lab = m.Text("lifetime min_flt", font_size=22, color=INK).next_to(total, m.DOWN, buff=0.15)
        self.play(self.show(*threads, plus, thread_labels))
        self.cap("Lifetime: every live thread's count, plus the counts saved from exited ones.", hold=1)
        self.play(self.hide(*threads, plus, thread_labels), self.show(eq, total, total_lab))
        self.cap("This matches /proc/<pid>/stat, read under the stats lock.", hold=1.5)
        self.play(self.hide(eq, total, total_lab))

        # live: a return probe classifies each fault of the target, using the kernel's own flags
        gate = self.box("same process?", "kretprobe filter", GOLD, [-5.2, 2.0, 0], width=3.0)
        read = self.box("read the result", "mm_account_fault()", BLUE, [-1.4, 2.0, 0], width=3.2)
        decide = self.box("major?", "major flag or retried", RED, [2.9, 2.0, 0], width=3.4)
        skip = self.pill("other process: skipped", GREY, [-5.2, 0.5, 0], width=3.4)
        flow = [
            m.Arrow(gate.get_right(), read.get_left(), buff=0.08, color=MUTED),
            m.Arrow(read.get_right(), decide.get_left(), buff=0.08, color=MUTED),
            m.Arrow(gate.get_bottom(), skip.get_top(), buff=0.08, color=MUTED),
        ]
        counters = [
            self.counter("minor · anon", GREEN, [-2.6, -0.6, 0]),
            self.counter("minor · file", GREEN, [-0.2, -0.6, 0]),
            self.counter("major · anon", RED, [2.4, -0.6, 0]),
            self.counter("major · file", RED, [4.9, -0.6, 0]),
        ]
        frames = [c[0] for c in counters]
        branch = [m.Arrow(decide.get_bottom(), c[0].get_top(), buff=0.05, color=MUTED) for c in counters]
        yes_no = m.VGroup(
            m.Text("no", font_size=20, color=GREEN).move_to([1.3, 0.55, 0]),
            m.Text("yes", font_size=20, color=RED).move_to([2.7, 0.55, 0]),
        )
        note = m.Text("anon: no file behind the mapping. file: a file is behind it.", font_size=20, color=MUTED).move_to([0, -1.9, 0])
        self.play(self.show(gate, read, decide, skip, *flow, *frames, *branch, yes_no, note))
        lives = self.write_live(*[c[2] for c in counters])

        dot = m.Dot([-6.9, 2.0, 0], radius=0.12, color=GREY)
        self.play(self.show(dot))
        self.cap("Live: a return probe on handle_mm_fault() reads the outcome of every fault.", hold=0.5)
        self.play(dot.animate.move_to(gate.get_center()), run_time=0.8)
        self.play(dot.animate.move_to(skip.get_center()), run_time=1.0)
        self.cap("Another process's fault is skipped at once. Only the target counts.", hold=1)
        self.play(self.hide(dot))

        dot = m.Dot([-6.9, 2.0, 0], radius=0.12, color=GOLD)
        self.play(self.show(dot))
        self.play(dot.animate.move_to(gate.get_center()), run_time=0.8)
        self.play(dot.animate.move_to(read.get_center()), run_time=0.9)
        self.cap("The target's fault: read the kernel's result, then decide minor or major.", hold=1)
        self.play(dot.animate.move_to(decide.get_center()), run_time=0.9)
        self.cap("Rule: a retried fault counts once; a failed fault is not counted at all.", hold=1.5)
        self.play(dot.animate.move_to(counters[0][0].get_center()), run_time=1.4)
        self.play(self.hide(dot))
        self.cap("Anonymous or file-backed decides the column. That gives four counters.", hold=1.5)
        self.play(
            counters[0][1].animate.set_value(16452),
            counters[1][1].animate.set_value(78),
            counters[3][1].animate.set_value(8193),
            run_time=5,
        )
        self.cap("E7 run: 16,452 minor on anon, 78 minor on file, 8,193 major on file.", hold=2)
        self.cap("Next: when exactly the probe fires, relative to the kernel's work.", hold=1.5)
        still_nums = self.still(*[(live, c[2]) for live, c in zip(lives, counters)])
        self.play(self.hide(gate, read, decide, skip, *flow, *frames, *branch, yes_no, note, *still_nums))

    def probe_timing(self) -> None:
        self.chapter(6)
        span = m.Rectangle(width=5.0, height=0.6, stroke_width=0, fill_color=BLUE, fill_opacity=0.7).move_to([-0.5, 0, 0])
        span_lab = m.Text("handle_mm_fault() runs", font_size=22, color=INK).move_to(span)
        axis = m.Line([-5.6, 0, 0], [5.6, 0, 0], color=MUTED)
        time_lab = m.Text("time →", font_size=20, color=MUTED).move_to([5.0, -0.4, 0])
        tp = m.Dot([-3.0, 0, 0], radius=0.12, color=RED)
        tp_lab = m.VGroup(
            m.Text("exceptions:page_fault_user", font_size=22, color=RED),
            m.Text("fires first: result not known", font_size=20, color=MUTED),
        ).arrange(m.DOWN, buff=0.1).move_to([-3.0, 1.9, 0])
        tp_arrow = m.Arrow([-3.0, 1.4, 0], [-3.0, 0.2, 0], buff=0.05, color=RED)
        kp = m.Dot([2.0, 0, 0], radius=0.12, color=GREEN)
        kp_lab = m.VGroup(
            m.Text("kretprobe on handle_mm_fault()", font_size=22, color=GREEN),
            m.Text("fires at return: minor or major known", font_size=20, color=MUTED),
        ).arrange(m.DOWN, buff=0.1).move_to([2.0, -1.9, 0])
        kp_arrow = m.Arrow([2.0, -1.4, 0], [2.0, -0.2, 0], buff=0.05, color=GREEN)

        self.play(m.Create(axis), self.show(time_lab, span, span_lab))
        self.cap("The probe times that same function: from its start to its return.", hold=1)
        self.play(self.show(tp, tp_arrow, tp_lab))
        self.cap("The hinted tracepoint fires first, and here it is x86-only: this VM is arm64.", hold=1.5)
        self.play(self.show(kp, kp_arrow, kp_lab))
        self.cap("The return probe fires after the kernel has decided: minor or major is known.", hold=2)
        self.cap("Next: how the fault counts change over time, in the timeline.", hold=1.5)
        self.play(self.hide(axis, time_lab, tp, tp_arrow, tp_lab, kp, kp_arrow, kp_lab, span, span_lab))

    def timeline_charts(self) -> None:
        self.chapter(7)
        ax = m.Axes(x_range=[0, 4.5, 0.5], y_range=[0, 100, 25], x_length=6.2, y_length=3.5, tips=False)
        ax.move_to([-3.0, -0.6, 0])
        x0, y0 = ax.c2p(0, 0)[0], ax.c2p(0, 0)[1]
        ytop = ax.c2p(0, 100)[1]
        x_ticks = m.VGroup(*[
            m.Text(f"{t} s", font_size=18, color=MUTED).next_to(ax.c2p(t, 0), m.DOWN, buff=0.12)
            for t in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        ])
        y_ticks = m.VGroup(*[
            m.Text(f"{v} MB", font_size=18, color=MUTED).next_to(ax.c2p(0, v), m.LEFT, buff=0.12)
            for v in [0, 50, 100]
        ])
        t1 = m.Text("virtual (blue) and resident (gold)", font_size=20, color=MUTED).move_to([-3.0, 1.75, 0])
        key = m.Text("blue shade: reserved, not in RAM", font_size=18, color=BLUE).move_to([-3.0, 1.38, 0])

        def band(t_from: float, t_to: float, label: str, color: str, top: bool):
            xa, xb = ax.c2p(t_from, 0)[0], ax.c2p(t_to, 0)[0]
            rect = m.Rectangle(width=xb - xa, height=ytop - y0, stroke_width=0, fill_color=color, fill_opacity=0.08)
            rect.move_to([(xa + xb) / 2, (y0 + ytop) / 2, 0])
            y_tag = ytop - 0.25 if top else y0 + 0.25
            tag = m.Text(label, font_size=18, color=color).move_to([(xa + xb) / 2, y_tag, 0])
            return rect, tag

        # tags sit where no curve is: the top for mmap and free, the bottom for the cold read
        bands = [band(1.0, 2.0, "mmap+touch", GREEN, True), band(2.5, 3.0, "cold read", RED, False),
                 band(3.5, 4.0, "free", GREY, True)]
        band_items = [b for pair in bands for b in pair]

        vsize_line = ax.plot_line_graph(TIMES, VSIZE, line_color=BLUE, add_vertex_dots=False)
        rss_line = ax.plot_line_graph(TIMES, RSS, line_color=GOLD, add_vertex_dots=False)
        gap = m.Polygon(
            *[ax.c2p(t, v) for t, v in zip(TIMES, VSIZE)],
            *[ax.c2p(t, r) for t, r in reversed(list(zip(TIMES, RSS)))],
            fill_color=BLUE, fill_opacity=0.14, stroke_width=0,
        )
        panel = self.bars(MAJOR, ["0.5 s", "1 s", "1.5 s", "2 s", "2.5 s", "3 s", "3.5 s", "4 s"], [RED] * 8,
                          origin=(1.2, -2.35), width=5.4, height=3.5, top=9000, short=True)
        t2 = m.Text("major faults per sample", font_size=20, color=MUTED).move_to([3.9, 1.75, 0])

        self.play(self.draw(ax, run_time=1.5), self.show(x_ticks, y_ticks, t1, key, *band_items, run_time=1.5))
        self.play(m.Create(vsize_line), m.Create(rss_line), run_time=2.5)
        self.play(m.FadeIn(gap))
        self.cap("Virtual size jumps at mmap. Resident memory follows only as pages are touched.", hold=1.5)
        self.cap("The blue shade is memory that is reserved but not in RAM.", hold=1.5)
        self.play(self.draw(panel, run_time=2), self.show(t2, run_time=2))
        self.cap("Reading the cold file causes 8,193 major faults in one step.", hold=1.5)

        t = m.ValueTracker(0.5)
        cursor = m.always_redraw(lambda: m.Line(ax.c2p(t.get_value(), 0), ax.c2p(t.get_value(), 100), color=INK, stroke_width=2))

        def read_make() -> m.Text:
            i = min(7, max(0, round((t.get_value() - 0.5) / 0.5)))
            return m.Text(
                f"t = {t.get_value():.1f} s · virtual {VSIZE[i]:.1f} MB · resident {RSS[i]:.1f} MB · major {MAJOR[i]:,}",
                font_size=22, color=INK,
            ).move_to([0, 2.7, 0])

        (readout,) = self.write_live(read_make)
        self.add(cursor)
        self.play(t.animate.set_value(4.0), run_time=6, rate_func=m.linear)
        self.cap("Freeing unmaps both: regions and virtual size fall back to 16 and 2.2 MB.", hold=2)
        self.cap("Next: do the experiments agree? Compare the counts side by side.", hold=1.5)
        self.remove(cursor)
        (readout_end,) = self.still((readout, read_make))
        self.play(self.hide(ax, x_ticks, y_ticks, t1, key, *band_items, vsize_line, rss_line, gap, panel, t2, readout_end))

    def experiments(self) -> None:
        self.chapter(8)
        left = self.bars([8192, 1, 0], ["cold, random", "readahead", "warm"], [RED, GREEN, BLUE],
                         origin=(-6.4, -1.2), width=5.4, height=2.7, top=9000)
        right = self.bars([16385, 511, 35], ["4 KB pages", "file, warm", "2 MB pages"], [GOLD, BLUE, GREEN],
                          origin=(1.0, -1.2), width=5.4, height=2.7, top=18000)
        t1 = m.Text("major faults, after baseline", font_size=22, color=INK).move_to([-3.7, 2.1, 0])
        t2 = m.Text("minor faults, after baseline", font_size=22, color=INK).move_to([3.7, 2.1, 0])
        equation = m.VGroup(
            m.Text("raw count − startup baseline = counted", font_size=22, color=INK),
            m.Text("E3: 8,193 − 1 = 8,192 · E4: 586 − 75 ≈ 511 · E2: 16,450 − 65 ≈ 16,385 · E6: 100 − 65 = 35",
                   font_size=18, color=MUTED),
        ).arrange(m.DOWN, buff=0.15).move_to([0, -2.55, 0])

        self.play(self.draw(left, right, run_time=2), self.show(t1, t2, run_time=2))
        self.cap("Access pattern and page size change the counts by orders of magnitude.", hold=1)
        self.cap("Baseline first: the startup faults of faultgen itself are subtracted.", hold=1.5)
        self.play(self.show(equation))
        self.cap("Cold random: 8,192 major faults. With readahead: 1.", hold=1.5)
        self.cap("Huge pages: 35 minor faults for 64 MB, where 4 KB pages took 16,385.", hold=2)
        self.cap("Next: check each number against a second source.", hold=1.5)
        self.play(self.hide(left, right, t1, t2, equation))

    def validation(self) -> None:
        cols = [-6.1, -3.5, -1.3, 1.5, 4.7]  # left edges; the last column holds the tick
        headers = ["quantity", "pfstat", "reference", "source"]

        def put(text: str, x: float, y: float, color: str) -> m.Text:
            t = m.Text(text, font_size=26, color=color)
            return t.move_to([x + t.width / 2, y, 0])

        def tick(x: float, y: float) -> m.VGroup:
            a = m.Line([x - 0.22, y - 0.02, 0], [x - 0.06, y - 0.2, 0], color=GREEN, stroke_width=5)
            b = m.Line([x - 0.06, y - 0.2, 0], [x + 0.26, y + 0.22, 0], color=GREEN, stroke_width=5)
            return m.VGroup(a, b)

        head = [put(h, x, 2.0, MUTED) for h, x in zip(headers, cols)]
        rule = m.Line([-6.3, 1.6, 0], [5.7, 1.6, 0], color=MUTED, stroke_width=1)
        self.play(self.show(*head, rule))
        rows = [
            ("regions", "30", "30", "/proc/<pid>/maps"),
            ("address space", "5.6 MB", "5.6 MB", "VmSize"),
            ("minor faults", "104", "104", "/proc/<pid>/stat"),
            ("major faults", "0", "0", "/proc/<pid>/stat"),
        ]
        row_items = []
        for r, (name, mine, ref, source) in enumerate(rows):
            y = 1.1 - r * 0.9
            cells = [put(name, cols[0], y, INK), put(mine, cols[1], y, INK),
                     put(ref, cols[2], y, INK), put(source, cols[3], y, MUTED)]
            check = tick(cols[3] + 3.9, y)
            self.play(self.show(*cells, run_time=0.7))
            self.play(m.Create(check, run_time=0.4))
            row_items += cells + [check]
        self.cap("Every number has a second source. For a sleeping process, all four match.", hold=2)
        self.cap("Controlled runs matched getrusage(). Real programs match with -f.", hold=2)
        self.cap("Next: the edge cases, where the simple picture breaks down.", hold=1.5)
        self.play(self.hide(*head, rule, *row_items))

    def hard_cases(self) -> None:
        self.chapter(9)
        # a 20 ms program against polling and the exit probe (scale: 1 s = 11 units)
        y = 1.0
        axis = m.Line([-5.5, y, 0], [5.5, y, 0], color=MUTED)
        ticks = m.VGroup(*[
            m.Text(t, font_size=20, color=MUTED).move_to([x, y - 0.45, 0])
            for t, x in [("0 ms", -5.5), ("500 ms", 0.0), ("1 s", 5.5)]
        ])
        prog = m.Rectangle(width=0.22, height=0.3, stroke_width=0, fill_color=RED, fill_opacity=1).move_to([-5.39, y + 0.2, 0])
        prog_lab = m.Text("python3 -c pass: 20 ms", font_size=22, color=RED).move_to([-2.6, y + 0.9, 0])
        polls = m.VGroup(*[m.Circle(radius=0.14, color=BLUE, stroke_width=3).move_to([x, y + 0.7, 0]) for x in (0.0, 5.5)])
        poll_lab = m.Text("polls: nothing left to see", font_size=20, color=BLUE).move_to([2.6, y + 1.5, 0])
        exit_dot = m.Dot([-5.28, y + 0.35, 0], radius=0.1, color=GREEN)
        exit_lab = m.Text("exit probe: taken as the last thread exits", font_size=20, color=GREEN).move_to([-0.4, -0.7, 0])
        exit_arrow = m.Arrow([-4.3, -0.5, 0], [-5.2, y + 0.15, 0], buff=0.05, color=GREEN)
        chips = m.VGroup(*[
            self.pill(text, GREEN, [x, -1.85, 0], width=3.9)
            for text, x in [("map_count → VMAs", -4.5), ("total_vm → size", 0.0), ("hiwater_vm → peak", 4.5)]
        ])

        self.play(m.Create(axis), self.show(ticks, prog, prog_lab))
        self.cap("A 20 ms program exits before any poll. The exit probe still records it.", hold=1.5)
        self.play(self.show(polls, poll_lab, exit_dot, exit_arrow, exit_lab))
        self.cap("At exit, the probe reads counters the kernel already keeps. Nothing is walked.", hold=1.5)
        self.play(self.show(chips))
        self.cap("No mmap lock is needed: the snapshot reads three counters, one per question.", hold=2)
        self.play(self.hide(axis, ticks, prog, prog_lab, polls, poll_lab, exit_dot, exit_arrow, exit_lab, chips))
        self.clear_caption()

        # children: gcc alone against gcc with its children (E8, minor faults)
        scale = 8.0 / 6001
        bar_small = m.Rectangle(width=304 * scale, height=0.5, stroke_width=0, fill_color=GOLD, fill_opacity=0.9).move_to([-5.5 + 304 * scale / 2, 1.2, 0])
        bar_big = m.Rectangle(width=6001 * scale, height=0.5, stroke_width=0, fill_color=RED, fill_opacity=0.9).move_to([-5.5 + 6001 * scale / 2, 0.1, 0])
        lab_small = m.Text("gcc alone", font_size=22, color=INK).next_to(bar_small, m.UP, buff=0.15, aligned_edge=m.LEFT)
        lab_big = m.Text("gcc with its children", font_size=22, color=INK).next_to(bar_big, m.UP, buff=0.15, aligned_edge=m.LEFT)
        val_small = m.Text("304", font_size=22, color=GOLD).next_to(bar_small, m.RIGHT, buff=0.15)
        val_big = m.Text("6,001", font_size=22, color=RED).next_to(bar_big, m.RIGHT, buff=0.15)
        root = self.box("gcc", "the driver", GOLD, [0.0, -0.95, 0], width=2.2, height=0.8)
        kids = [self.box(name, role, BLUE, [x, -2.2, 0], width=2.0, height=0.75)
                for name, role, x in [("cc1", "compiler", -4.5), ("as", "assembler", -1.5),
                                      ("collect2", "linker", 1.5), ("ld", "linker", 4.5)]]
        kid_arrows = [m.Arrow(root.get_bottom(), k.get_top(), buff=0.06, color=MUTED) for k in kids]

        self.play(self.show(bar_small, lab_small, val_small, bar_big, lab_big, val_big, run_time=1.5))
        self.cap("gcc alone: 304 minor faults. With its children: 6,001.", hold=2)
        self.play(self.show(root, *kids, *kid_arrows))
        self.cap("The children are cc1, as, collect2 and ld: follow mode counts their faults too.", hold=2)
        self.cap("With -f the totals match getrusage(). Without it, the gap is the children.", hold=2)
        self.play(self.hide(bar_small, lab_small, val_small, bar_big, lab_big, val_big, root, *kids, *kid_arrows))

    def closing(self) -> None:
        self.play(self.hide(*self.rail))
        self.rail = []
        self.move_camera(phi=64 * m.DEGREES, theta=-78 * m.DEGREES, run_time=2.5)
        bars = self.region_bars().shift(m.OUT * 0.6)  # raised clear of the summary rows, not off the top
        self.play(m.LaggedStart(*[m.FadeIn(b, shift=m.DOWN * 0.3) for b in bars], lag_ratio=0.03))
        rows = [
            ("regions", "walk the VMAs under the map lock", "/proc/<pid>/maps"),
            ("address space", "sum of vm_end − vm_start", "VmSize"),
            ("minor, major", "kretprobe on handle_mm_fault()", "/proc/<pid>/stat, getrusage()"),
        ]
        summary = m.VGroup(*[
            m.VGroup(
                m.Text(a, font_size=24, color=INK),
                m.Text(b, font_size=22, color=MUTED),
                m.Text(c, font_size=22, color=GREEN),
            ).arrange(m.RIGHT, buff=0.5)
            for a, b, c in rows
        ]).arrange(m.DOWN, buff=0.25, aligned_edge=m.LEFT).move_to([0, -2.1, 0])  # under the bars, above the caption
        self.pin(summary)
        self.play(self.show(summary))

        self.begin_ambient_camera_rotation(rate=0.12)
        self.cap("Four numbers from the kernel, each checked against a second source.", hold=3)
        self.cap("CPE333 · Mini-Project 02: pfcount and pfstat.", hold=2)
        self.stop_ambient_camera_rotation()
        self.play(m.FadeOut(bars), self.hide(summary, self.caption_mob))
        self.move_camera(phi=0, theta=-90 * m.DEGREES, frame_center=[0, 0, 0], run_time=2)  # flat and centred for the credits
        credits = m.VGroup(
            m.Text("Images: Wikimedia Commons (see assets/SOURCES.md)", font_size=22, color=INK),
            m.Text("CPU: public domain · RAM: Raimond Spekking, CC BY-SA 4.0", font_size=20, color=MUTED),
            m.Text("Disk: Matthew Field, CC BY-SA 3.0 · Tux: Larry Ewing et al.", font_size=20, color=MUTED),
        ).arrange(m.DOWN, buff=0.2).move_to([0, 0, 0])
        self.play(self.show(credits))
        self.wait(4)
