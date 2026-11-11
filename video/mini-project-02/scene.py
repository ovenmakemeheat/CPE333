"""Mini-Project 02 video: the narration in script.md, as on-screen captions,
with the visuals the script's Visual notes ask for. Run: manimgx render scene.py"""

import re
import textwrap
from pathlib import Path

import manimgx as m


SCRIPT = Path(__file__).resolve().with_name("script.md")
WORDS_PER_SECOND = 2.0  # caption reading pace: slower than speech, so it can be read
CAPTION_Y = -3.1

BG, INK, MUTED = "#0A1020", "#EAF0F7", "#8DA2BA"
BLUE, GOLD, GREEN, RED = "#4DA3FF", "#F5B841", "#5BD19A", "#FF6B6B"
PANEL = "#121C2F"
m.config.background_color = BG

# results/e7-timeline.txt, watch mode, one sample every 0.5 s
TIMES = ["0.5 s", "1.0 s", "1.5 s", "2.5 s", "3.5 s"]
REGIONS = [16, 17, 17, 18, 16]
VSIZE = [2.2, 66.2, 66.2, 98.2, 2.2]  # MB
RSS = [1.4, 7.9, 65.4, 97.2, 1.3]  # MB
MAJOR = [1, 1, 1, 8193, 8193]


def narration() -> list[list[str]]:
    """The narration paragraphs of each section of script.md, in order."""
    sections: list[list[str]] = []
    buf: list[str] = []

    def close() -> None:
        if buf and sections:
            sections[-1].append(" ".join(buf))
        buf.clear()

    for line in SCRIPT.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            close()
            sections.append([])
        elif line.startswith(">") and line[1:].strip():
            buf.append(line[1:].strip())
        else:
            close()
    close()
    return sections


def segments(text: str, limit: int = 150) -> list[str]:
    """The text in caption-sized pieces, cut at sentence ends."""
    out, cur = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if cur and len(cur) + len(sentence) + 1 > limit:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    return out + [cur] if cur else out


def caption(text: str) -> m.VGroup:
    body = m.Text("\n".join(textwrap.wrap(text, 84)), font_size=24, color=INK)
    body.move_to([0, CAPTION_Y, 0])
    band = m.Rectangle(
        width=13.4,
        height=body.height + 0.5,
        fill_color="#000000",
        fill_opacity=0.65,
        stroke_width=0,
    )
    band.move_to([0, CAPTION_Y, 0])
    return m.VGroup(band, body)


def card(
    title: str,
    lines: list[str] = (),
    width: float = 4.0,
    height: float = 1.6,
    color: str = BLUE,
    pos: tuple[float, float] = (0, 0),
    size: int = 26,
) -> m.VGroup:
    frame = m.Rectangle(
        width=width,
        height=height,
        color=color,
        fill_color=PANEL,
        fill_opacity=0.95,
        stroke_width=2,
    )
    texts = [m.Text(title, font_size=size, color=INK)]
    texts += [m.Text(line, font_size=size - 6, color=MUTED) for line in lines]
    body = m.VGroup(*texts).arrange(m.DOWN, buff=0.12)
    body.move_to(frame)
    group = m.VGroup(frame, body)
    group.move_to([pos[0], pos[1], 0])
    return group


class MiniProject02(m.Scene):
    def construct(self) -> None:
        self.cap = None  # the caption on screen
        self.shown = None  # the demo's readout on screen
        sections = narration()
        assert [len(s) for s in sections] == [2, 3, 3, 4, 4, 6, 3, 3, 3], (
            "script.md changed: the scene's visuals need the same paragraph layout"
        )
        self.hook(*sections[0])
        self.project(*sections[1])
        self.concepts(*sections[2])
        self.counting(*sections[3])
        self.faults(*sections[4])
        self.demo(*sections[5])
        self.checks(*sections[6])
        self.hard(*sections[7])
        self.close(*sections[8])

    # ---- captions -------------------------------------------------------

    def narrate(self, text: str, *anims, clear: bool = False) -> None:
        """Show the narration as captions over its own time; anims play with the first."""
        for i, part in enumerate(segments(text)):
            self.caption_step(part, anims if i == 0 else (), clear and i == 0)

    def caption_step(self, text: str, anims, clear: bool) -> None:
        hold = max(2.0, len(text.split()) / WORDS_PER_SECOND)
        new = caption(text)
        moves = []
        if clear:
            others = [x for x in self.mobjects if x is not self.cap]
            if others:
                moves.append(m.FadeOut(*others, run_time=0.5))
        if self.cap is not None:
            moves.append(m.FadeOut(self.cap, run_time=0.3))
        moves.append(m.FadeIn(new, run_time=0.3))
        moves.extend(anims)
        self.add_subcaption(text, hold)
        self.play(*moves)
        self.cap = new
        longest = max(getattr(a, "run_time", 1.0) for a in moves)
        if hold > longest:
            self.wait(hold - longest)

    # ---- sections -------------------------------------------------------

    def hook(self, p0: str, p1: str) -> None:
        file = card("32 MB file", ["8,192 pages"], width=4.0, height=1.2, pos=(0, 1.6))
        left = card("random reads", ["cold cache, MADV_RANDOM"], width=5.0, height=1.3, pos=(-3.6, -0.4))
        right = card("sequential reads", ["readahead on"], width=5.0, height=1.3, color=GREEN, pos=(3.6, -0.4))
        arrows = [
            m.Arrow(file.get_bottom(), left.get_top(), buff=0.1, color=MUTED),
            m.Arrow(file.get_bottom(), right.get_top(), buff=0.1, color=MUTED),
        ]
        left_count = m.Text("8,193 major faults", font_size=34, color=GOLD).move_to([-3.6, -1.9, 0])
        right_count = m.Text("2 major faults", font_size=34, color=GOLD).move_to([3.6, -1.9, 0])
        self.narrate(p0, m.FadeIn(file), clear=True)
        self.narrate(
            p1,
            m.GrowArrow(arrows[0]),
            m.GrowArrow(arrows[1]),
            m.FadeIn(left, right),
            m.FadeIn(left_count, right_count),
        )

    def project(self, p0: str, p1: str, p2: str) -> None:
        title = m.Text("CPE333 · Virtual Memory", font_size=30, color=MUTED).move_to([0, 2.4, 0])
        head = m.Text("Page-Fault Counter", font_size=56, color=INK).move_to([0, 1.3, 0])
        asked = m.VGroup(
            *[
                m.Text(t, font_size=28, color=BLUE)
                for t in ["memory regions", "virtual address space", "minor page faults", "major page faults"]
            ]
        ).arrange(m.DOWN, buff=0.25).move_to([0, -0.4, 0])
        self.narrate(p0, m.FadeIn(title, head, asked), clear=True)

        parts = [
            card("pfcount", ["kernel module"], pos=(-4.5, 0.8), width=4.0, color=BLUE),
            card("pfstat", ["command-line tool"], pos=(0, 0.8), width=4.0, color=GREEN),
            card("faultgen", ["test program"], pos=(4.5, 0.8), width=4.0, color=GOLD),
        ]
        self.narrate(p1, m.FadeIn(*parts), clear=True)

        env = m.VGroup(
            m.Text("Ubuntu 24.04 · kernel 6.8 · arm64", font_size=28, color=INK),
            m.Text("Lima virtual machine on a Mac host", font_size=24, color=MUTED),
        ).arrange(m.DOWN, buff=0.2).move_to([0, -0.6, 0])
        self.narrate(p2, m.FadeIn(env), clear=True)

    def concepts(self, p0: str, p1: str, p2: str) -> None:
        names = ["executable", "heap", "anonymous mapping", "stack"]
        blocks = m.VGroup(
            *[
                m.Rectangle(width=4.6, height=0.8, color=MUTED, stroke_width=2, fill_color=BLUE, fill_opacity=0)
                for _ in names
            ]
        ).arrange(m.DOWN, buff=0.15).move_to([-3.2, 0.4, 0])
        labels = m.VGroup(
            *[m.Text(n, font_size=24, color=INK).move_to(b) for n, b in zip(names, blocks)]
        )
        heading = m.Text("virtual address space", font_size=26, color=MUTED).next_to(blocks, m.UP, buff=0.25)
        self.narrate(p0, m.FadeIn(blocks, labels, heading), clear=True)

        resident = [blocks[0], blocks[1], blocks[3]]  # the anonymous mapping stays reserved
        legend = m.VGroup(
            m.Text("outline: reserved, not in RAM yet", font_size=22, color=MUTED),
            m.Text("filled: resident, in RAM", font_size=22, color=GOLD),
        ).arrange(m.DOWN, buff=0.25).move_to([3.8, 1.4, 0])
        self.narrate(
            p1,
            m.FadeIn(legend),
            *[b.animate.set_fill(GOLD, opacity=0.6) for b in resident],
        )

        minor = card("minor fault", ["no disk I/O: a zero page or a page-cache hit"], width=6.0, height=1.2, color=GREEN, pos=(3.8, 0.0))
        major = card("major fault", ["the page must be read from disk"], width=5.6, height=1.2, color=RED, pos=(3.8, -1.5))
        self.narrate(p2, m.FadeIn(minor, major))

    def counting(self, p0: str, p1: str, p2: str, p3: str) -> None:
        code = [
            "task = get_pid_task(target_pid, PIDTYPE_PID);",
            "mm = get_task_mm(task);                # the address space",
            "mmap_read_lock_killable(mm);           # hold the map still",
            "for_each_vma(vmi, vma) {",
            "    regions++;",
            "    vsize += vma->vm_end - vma->vm_start;",
            "}",
            "mmap_read_unlock(mm);",
        ]
        highlight = {1, 2, 3}  # get_task_mm, the lock, the VMA walk
        lines = m.VGroup(
            *[m.Text(c, font_size=20, color=GOLD if i in highlight else INK) for i, c in enumerate(code)]
        ).arrange(m.DOWN, buff=0.22, aligned_edge=m.LEFT).move_to([0, 0.5, 0])
        panel = m.Rectangle(
            width=lines.width + 0.6,
            height=lines.height + 0.5,
            fill_color=PANEL,
            fill_opacity=1,
            stroke_color=MUTED,
            stroke_width=1,
        ).move_to(lines)
        self.narrate(p0, m.FadeIn(panel, lines), clear=True)
        self.narrate(p1)  # the code stays up while the sums are explained

        rows = [
            ("regions (VMAs)", "30 lines in /proc/<pid>/maps"),
            ("virtual address space", "VmSize: 5.6 MB"),
            ("mm->total_vm", "equals the VMA sum"),
        ]
        table = m.VGroup(
            *[
                m.VGroup(
                    m.Text(left, font_size=26, color=INK),
                    m.Text("match", font_size=26, color=GREEN),
                    m.Text(right, font_size=24, color=MUTED),
                ).arrange(m.RIGHT, buff=0.6)
                for left, right in rows
            ]
        ).arrange(m.DOWN, buff=0.5, aligned_edge=m.LEFT).move_to([0, 0.4, 0])
        self.narrate(p2, m.FadeIn(table), clear=True)

        term = card(
            "$ sudo tools/pfstat 213654 --maps",
            [
                "Memory regions (VMAs)          30   match vs /proc/PID/maps",
                "Total virtual address space  5.6 MB  match vs /proc/PID/maps",
                "regions by type: file 24 · anon 2 · heap 1 · stack 1 · special 2",
            ],
            width=11.0,
            height=2.4,
            color=GREEN,
            pos=(0, 0.6),
            size=24,
        )
        self.narrate(p3, m.FadeIn(term), clear=True)

    def faults(self, p0: str, p1: str, p2: str, p3: str) -> None:
        lifetime = card("Lifetime counters", ["since the process started"], width=5.6, height=1.5, pos=(-3.6, 0.6))
        live = card("Live counters", ["since monitoring began"], width=5.6, height=1.5, color=GREEN, pos=(3.6, 0.6))
        self.narrate(p0, m.FadeIn(lifetime, live), clear=True)

        sums = m.VGroup(
            card("task->min_flt, task->maj_flt", ["summed over every live thread"], width=6.6, height=1.2),
            card("+ signal->min_flt, signal->maj_flt", ["counts saved from threads that already exited"], width=6.6, height=1.2),
            card("read under signal->stats_lock", ["a seqlock, so no thread is counted twice"], width=6.6, height=1.2, color=GOLD),
        ).arrange(m.DOWN, buff=0.25).move_to([0, 0.4, 0])
        self.narrate(p1, m.FadeIn(sums), clear=True)

        entry = card("kretprobe entry", ["same tgid as the target?"], width=3.2, height=1.3, pos=(-5.4, 0.4), size=22)
        handler = card("handle_mm_fault()", ["the kernel's fault path"], width=3.2, height=1.3, pos=(-1.8, 0.4), size=22)
        ret = card("return: read result", ["mm_account_fault() rule"], width=3.2, height=1.3, color=GREEN, pos=(1.8, 0.4), size=22)
        minor = card("minor", ["counted as minor"], width=3.0, height=1.0, color=GREEN, pos=(5.4, 1.3), size=22)
        major = card("major", ["counted as major"], width=3.0, height=1.0, color=RED, pos=(5.4, -0.6), size=22)
        arrows = [
            m.Arrow(entry.get_right(), handler.get_left(), buff=0.05, color=MUTED),
            m.Arrow(handler.get_right(), ret.get_left(), buff=0.05, color=MUTED),
            m.Arrow(ret.get_right(), minor.get_left(), buff=0.05, color=MUTED),
            m.Arrow(ret.get_right(), major.get_left(), buff=0.05, color=MUTED),
        ]
        self.narrate(p2, m.FadeIn(entry, handler, ret, minor, major), *[m.GrowArrow(a) for a in arrows], clear=True)

        tracepoint = card(
            "exceptions:page_fault_user",
            ["x86 only; this VM is arm64", "fires before the fault is handled"],
            width=6.4, height=1.6, color=RED, pos=(-3.6, -0.4),
        )
        kretprobe = card(
            "kretprobe on handle_mm_fault()",
            ["works on every architecture", "sees the result"],
            width=6.4, height=1.6, color=GREEN, pos=(3.6, -0.4),
        )
        self.narrate(p3, m.FadeIn(tracepoint, kretprobe), clear=True)

    def demo(self, p0: str, p1: str, p2: str, p3: str, p4: str, p5: str) -> None:
        command = card(
            "sudo tools/pfstat -w 0.5 -- tests/faultgen",
            ["sleep:1 anon:64 sleep:1 file:/tmp/pfcount-big.bin sleep:1 free sleep:1"],
            width=12.6, height=1.2, color=MUTED, pos=(0, 2.6), size=22,
        )
        self.narrate(p0, m.FadeIn(command), clear=True)

        base, scale = -1.8, 0.022  # y of the axis; inches of bar per MB
        xs = [-4.4, -2.2, 0.0, 2.2, 4.4]
        bars = []
        for x, v, r in zip(xs, VSIZE, RSS):
            vbar = m.Rectangle(width=0.6, height=v * scale, fill_color=BLUE, fill_opacity=0.9, stroke_width=0)
            vbar.move_to([x - 0.35, base + v * scale / 2, 0])
            rbar = m.Rectangle(width=0.6, height=r * scale, fill_color=GOLD, fill_opacity=0.9, stroke_width=0)
            rbar.move_to([x + 0.35, base + r * scale / 2, 0])
            bars.append(m.VGroup(vbar, rbar))
        axis = m.Line([-5.6, base, 0], [5.6, base, 0], color=MUTED)
        labels = m.VGroup(
            *[m.Text(t, font_size=20, color=MUTED).move_to([x, base - 0.35, 0]) for t, x in zip(TIMES, xs)]
        )
        legend = m.VGroup(
            m.VGroup(
                m.Square(side_length=0.22, fill_color=BLUE, fill_opacity=1, stroke_width=0),
                m.Text("virtual size (address space)", font_size=20, color=INK),
            ).arrange(m.RIGHT, buff=0.15),
            m.VGroup(
                m.Square(side_length=0.22, fill_color=GOLD, fill_opacity=1, stroke_width=0),
                m.Text("resident (in RAM)", font_size=20, color=INK),
            ).arrange(m.RIGHT, buff=0.15),
        ).arrange(m.DOWN, buff=0.15).move_to([-3.6, 1.5, 0])

        def readout(i: int) -> m.VGroup:
            return m.VGroup(
                m.Text(f"t = {TIMES[i]} · {REGIONS[i]} regions · major faults {MAJOR[i]:,}", font_size=22, color=INK),
                m.Text(f"{VSIZE[i]} MB virtual · {RSS[i]} MB resident", font_size=22, color=GOLD),
            ).arrange(m.DOWN, buff=0.12).move_to([3.3, 1.5, 0])

        self.shown = readout(1)
        self.narrate(
            p1,
            m.FadeIn(axis, labels, legend),
            m.FadeIn(bars[0], bars[1]),
            m.FadeIn(self.shown),
        )
        for i, text in [(2, p2), (3, p3), (4, p4)]:
            new = readout(i)
            self.narrate(text, m.FadeIn(bars[i]), m.ReplacementTransform(self.shown, new))
            self.shown = new
        self.narrate(p5, m.Indicate(legend))

    def checks(self, p0: str, p1: str, p2: str) -> None:
        a = card("sleep 300, checked against /proc", ["30 regions · 5.6 MB · 104 minor · 0 major", "all four match"], width=6.2, height=1.7, color=GREEN, pos=(-3.5, 1.9))
        b = card("8,192 random pages, cold cache", ["8,193 major faults in total", "1 of them is the startup baseline"], width=6.2, height=1.7, pos=(3.5, 1.9))
        c = card("same file, readahead on", ["2 major faults in total", "about 1 after startup"], width=6.2, height=1.7, color=GREEN, pos=(-3.5, -0.3))
        d = card("64 MB anonymous, THP on", ["about 35 faults after baseline", "vs about 16,384 with 4 KB pages"], width=6.2, height=1.7, color=GOLD, pos=(3.5, -0.3))
        self.narrate(p0, m.FadeIn(a), clear=True)
        self.narrate(p1, m.FadeIn(b))
        self.narrate(p2, m.FadeIn(c, d))

    def hard(self, p0: str, p1: str, p2: str) -> None:
        exits = card("python3 -c pass", ["exits in about 20 ms, before the first sample"], width=5.6, height=1.5, color=RED, pos=(-3.5, 1.0))
        snap = card("exit snapshot", ["region count, size and peak at exit"], width=5.6, height=1.5, color=GREEN, pos=(3.5, 1.0))
        self.narrate(p0, m.FadeIn(exits, snap), clear=True)

        gcc = card("gcc driver", ["about 5% of the faults"], width=4.0, height=1.3, pos=(0, 2.0))
        kids = [
            card(name, [role], width=3.6, height=1.3, color=GOLD, pos=(x, -0.5))
            for name, role, x in [("cc1", "the compiler", -4.4), ("as", "the assembler", 0.0), ("collect2, ld", "the linker", 4.4)]
        ]
        arrows = [m.Arrow(gcc.get_bottom(), k.get_top(), buff=0.1, color=MUTED) for k in kids]
        self.narrate(p1, m.FadeIn(gcc, *kids), *[m.GrowArrow(a) for a in arrows], clear=True)

        wait4 = card(
            "wait4() as the reference",
            ["counts only descendants that were waited for", "a lower bound, not proof the probe is wrong"],
            width=8.0, height=1.8, color=GOLD, pos=(0, -0.4),
        )
        self.narrate(p2, m.FadeIn(wait4), clear=True)

    def close(self, p0: str, p1: str, p2: str) -> None:
        rows = [
            ("Memory regions", "VMA count", "/proc/<pid>/maps"),
            ("Virtual address space", "sum of VMA sizes", "/proc/<pid>/maps, VmSize"),
            ("Minor page faults", "task->min_flt", "/proc/<pid>/stat, getrusage()"),
            ("Major page faults", "task->maj_flt", "/proc/<pid>/stat, getrusage()"),
        ]
        table = m.VGroup()
        for row in rows:
            cells = []
            for text, x, size, color in zip(row, (-6.4, -1.4, 2.2), (24, 24, 22), (INK, BLUE, GREEN)):
                t = m.Text(text, font_size=size, color=color)
                t.move_to([x + t.width / 2, 0, 0])  # left edge at x
                cells.append(t)
            table.add(m.VGroup(*cells))
        table.arrange(m.DOWN, buff=0.5, aligned_edge=m.LEFT).move_to([0, 0.4, 0])
        self.narrate(p0, m.FadeIn(table), clear=True)

        note = m.VGroup(
            m.Text("Address space is not RAM.", font_size=44, color=INK),
            m.Text("A mapping reserves address space; RAM is used only when pages are touched.", font_size=26, color=MUTED),
        ).arrange(m.DOWN, buff=0.3).move_to([0, 0.6, 0])
        self.narrate(p1, m.FadeIn(note), clear=True)

        end = m.VGroup(
            m.Text("pfcount · pfstat", font_size=54, color=INK),
            m.Text("CPE333 · Mini-Project 02 · Virtual Memory", font_size=26, color=MUTED),
        ).arrange(m.DOWN, buff=0.3).move_to([0, 0.6, 0])
        self.narrate(p2, m.FadeIn(end), clear=True)
        self.wait(2)
