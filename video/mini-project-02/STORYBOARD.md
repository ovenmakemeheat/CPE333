# Mini-Project 02 — Storyboard

**Story source:** `mini-project-02/REPORT.md`, followed in its own order: goal → background → design → walkthrough → experiments → findings → limits → conclusion.
**Length:** 9:30, inside the 7–11 minute limit.
**Sound:** none yet. Every shot is cut on a fixed beat grid so music and voice can be laid on later without retiming.

---

## 1. Rhythm grid

| Unit | Value | Use |
|---|---|---|
| Tempo | 96 BPM | 1 beat = 0.625 s |
| Bar | 4 beats = 2.5 s | the smallest shot length |
| Phrase | 4 bars = 10 s | one idea per phrase |
| Act | phrases | each act starts on a downbeat |

Rules for the scene code:

- Every `run_time` and `wait` is a multiple of one beat (`B = 0.625`). Shot lengths are whole bars.
- Big moves (zoom, morph, counter climbs) land on the **first beat of a bar**. Small accents (a tick, a dot landing) land on beats 2–4.
- Each act opens with one bar of breathing room (no new text) and closes on a held bar, so music swells and voice-over pauses have space.
- Captions are written in on a downbeat and stay for at least one full phrase.

```python
B = 0.625          # one beat at 96 BPM
BAR = 4 * B        # 2.5 s

def beats(n): return n * B
# self.play(..., run_time=beats(4))   a one-bar move
# self.wait(beats(8))                  a two-bar hold
```

---

## 2. Visual system (consistent across all acts)

No arrows and no box-and-arrow diagrams. Two objects carry the whole video.

**The ribbon — the process's address space.**
A long horizontal strip of colored blocks, one block per VMA, in address order, always at the same height on screen. It never leaves; every act zooms into it, slides along it, or lifts it into 3D.

| Color | Meaning |
|---|---|
| blue `#4DA3FF` | file-backed region |
| gold `#F5B841` | anonymous region / resident page |
| green `#5BD19A` | heap, stack / minor fault / "match" |
| red `#FF6B6B` | major fault / disk |
| grey `#6B7A90` | special (`[vdso]`, `[vvar]`) / skipped |
| background `#0A1020`, ink `#EAF0F7`, muted `#8DA2BA` | everything else |

**The fault token — one page's journey.**
A small glowing square with a short trail. It is a page that gets touched, faults, crosses into the kernel, is classified, and lands as a tick. It reappears in every act as *the* fault.

**Space has meaning.** The top two-thirds of the screen is user space. A darker band across the bottom third is the kernel. Anything that happens "in the kernel" sinks into that band, so no labels or arrows are needed to say where code runs.

**Numbers are live.** Every count climbs on screen (`ValueTracker` + `always_redraw`). Numbers sit on a fixed scoreboard at top right with four slots: *regions · size · minor · major*. They fill in as the story earns them.

**Text** is written in (`Write`) and kept to one short line per phrase. Monospace for code and commands, serif for prose.

```python
# the ribbon: one rectangle per VMA, widths on a log scale so 4 KB and 3 MB both show
def ribbon(regions, y=1.2, width=12):
    w = [0.15 + math.log10(kb) for _, kb in regions]
    s = width / sum(w)
    blocks = [m.Rectangle(width=wi * s * 0.94, height=0.6, stroke_width=0,
                          fill_color=KIND_COLOR[k], fill_opacity=0.9)
              for (k, _), wi in zip(regions, w)]
    return m.VGroup(*blocks).arrange(m.RIGHT, buff=0.04).move_to([0, y, 0])

# the kernel band: everything below it is "inside the kernel"
kernel = m.Rectangle(width=14.2, height=2.6, stroke_width=0,
                     fill_color="#060A14", fill_opacity=1).move_to([0, -2.7, 0])

# the fault token: a glowing page with a trail that follows it
token = m.Square(0.22, fill_color=GOLD, fill_opacity=1, stroke_width=0)
trail = m.TracedPath(token.get_center, stroke_color=GOLD, stroke_width=3,
                     dissipating_time=0.6)
```

> `TracedPath` exists in ManimGX (checked).

### Plain words first, then depth

The story descends one level at a time, and each level reuses the picture from the level before:

| Level | Words on screen | Picture |
|---|---|---|
| 1 · everyday | *A program asks for memory. The computer says yes, but hands it over only when it is used.* | hotel key card → empty page outline |
| 2 · simple | *The first touch pauses the program for a moment. That pause is a page fault.* | the token flashes and the screen pauses for one beat |
| 3 · two kinds | *Usually quick. Sometimes it must fetch from the disk, and that is slow.* | book on the desk vs. library stacks → green vs. red token |
| 4 · our tool | *We built a counter inside Linux that counts every pause for one program.* | tally clicker → scoreboard |
| 5 · deep | VMAs, `handle_mm_fault`, the kretprobe, the experiments | ribbon, kernel band, code |

### Image beats

Each photo holds one or two bars, then morphs into the tile it stands for. Images come from Wikimedia Commons with open licenses and go in `assets/`, one folder each, recorded in `assets/SOURCES.md`.

| Idea | Image | Becomes |
|---|---|---|
| reserved, not yet given | hotel key card | empty page outline |
| minor fault | book on a desk | green token |
| major fault | library stacks / disk platter (have) | red token |
| readahead | waiter carrying the next plate | gold wave ahead of the reader |
| huge pages | pallet vs. single boxes | 2 MB tiles |
| kernel | Tux (have) | dark kernel band |
| child processes | kitchen brigade | gcc and its children |
| counting | mechanical tally clicker | scoreboard counter |

### Code moves line by line

- A code block is never shown whole. Each line writes in on a beat; the running line is bright, the rest dimmed.
- The line's effect happens on the same beat and stays after the code fades: `for_each_vma` moves the scan line, `regions++` ticks the counter, `vsize += ...` flies the block's width into the size total.
- When a block ends it shrinks into a chip beside the scoreboard, so the code that produced a number stays next to it.
- Minor faults flash quickly; a major fault dims and slows the screen for a bar, so the viewer feels the wait.

---

## 3. Act and shot list

Times are cumulative. Each row is one shot. **Beat** says what lands on the downbeat. **Sound** marks where music or voice should breathe.

### Act 0 — Plain-words opening (0:00–0:30, 3 phrases) · levels 1–2

| # | Time | Bars | Picture | Beat | Text | Sound |
|---|---|---|---|---|---|---|
| 0.1 | 0:00 | 4 | Title writes in, then lifts to the top. | title done on bar 2 beat 1 | **Where the Memory Goes** | music in, low |
| 0.2 | 0:10 | 4 | A row of 8 empty page outlines appears (reserved, nothing inside). | one outline per beat | *A program asks for memory. The computer says yes, but hands it over only when it is used.* | — |
| 0.3 | 0:20 | 4 | The token glides to outline 1 and touches it. The screen pauses one beat (dims), a flash, the outline fills gold. Then outlines 2–8 fill one per beat. | pause on bar 1 beat 2 | *The first touch pauses the program. That pause is a page fault.* | hit on the first fill |

### Act 1 — The goal (0:20–1:00) · REPORT §1

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 1.1 | 0:20 | 4 | Camera pulls back; the ribbon becomes "a process". Its PID writes in at the left end. | — | *Give the tool a PID.* |
| 1.2 | 0:30 | 4 | The scoreboard slides in top right with four empty slots: regions, size, minor, major. Each slot lights on beats 1–4. | one slot per beat | *It reports four numbers.* |
| 1.3 | 0:40 | 8 | Three glyphs rise from the kernel band and settle: a chip (`pfcount`, sits *inside* the band), a terminal (`pfstat`, above it), a dice (`faultgen`, at the ribbon). No connectors; position alone says who lives where. | each glyph lands on 1 | *A kernel module, a CLI, and a test program that faults on purpose.* |

### Act 2 — Background: what a fault is (1:00–2:00) · REPORT §2

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 2.1 | 1:00 | 4 | Zoom into one blue block. It splits into its VMA bounds: `vm_start` and `vm_end` tick marks write in at the edges. | zoom lands on 1 | *Each block is a VMA: one range, one kind of backing.* |
| 2.2 | 1:10 | 4 | Inside the VMA, empty page outlines appear (reserved, not in RAM). | — | *A VMA only reserves address space.* |
| 2.3 | 1:20 | 8 | **The fault token is born.** One outline is "touched": it flashes, drops through the ribbon into the kernel band, and comes back up filled gold. | drop on beat 1, return on bar 2 beat 1 | *The first touch is a page fault.* |
| 2.4 | 1:40 | 8 | Split screen in the same frame: left, the token comes back instantly (green, "minor, no I/O"); right, it sinks further to a disk photo at the bottom edge, waits one bar, then rises (red, "major, waited for disk"). | minor returns on 1; major returns two bars later | *Minor: no I/O. Major: wait for the disk.* |

Essential code shown on screen (written in, held one phrase, in the kernel band):

```c
if (ret & VM_FAULT_RETRY)  return;   /* retried: count it once, later */
if (ret & VM_FAULT_ERROR)  return;   /* SIGSEGV / SIGBUS: not counted */
major = (ret & VM_FAULT_MAJOR) || (flags & FAULT_FLAG_TRIED);
```

### Act 3 — Design: counting regions (2:00–3:00) · REPORT §4.1

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 3.1 | 2:00 | 4 | Camera returns to the full ribbon. A thin scan line sits at the left end. | — | *Walk every VMA.* |
| 3.2 | 2:10 | 8 | The scan line sweeps the ribbon on a steady beat; each block brightens as it passes. The **regions** slot counts up 1…30; the **size** slot sums to 5,684 KB. | one block per beat, sweep ends on bar 8 beat 1 | — (let the count speak) |
| 3.3 | 2:30 | 4 | Code writes in under the ribbon, each line lighting as the scan line reaches it. | — | (code) |
| 3.4 | 2:40 | 8 | A faint copy of `/proc/<pid>/maps` slides up behind the ribbon, line for line under each block. The regions and size slots get a green tick. | ticks on 1 and 3 | *Same 30 lines as /proc. Same 5.6 MB as VmSize.* |

```c
mm = get_task_mm(task);
mmap_read_lock_killable(mm);
for_each_vma(vmi, vma) {
        regions++;
        vsize += vma->vm_end - vma->vm_start;
}
mmap_read_unlock(mm);
```

### Act 4 — Design: counting faults (3:00–4:20) · REPORT §4.2–4.3

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 4.1 | 3:00 | 8 | **Lifetime.** Three thread lanes run across the ribbon. Each carries a small counter. One lane fades out (thread exits) and its counter drops into a shared pool. The pool and the live counters slide together into one total. | exit on bar 3 beat 1, merge on bar 6 beat 1 | *Lifetime: every thread, plus the threads that already left.* |
| 4.2 | 3:20 | 4 | A thin lock shape closes over the total while it is read. | lock on 1 | *Read under the stats lock, like /proc.* |
| 4.3 | 3:30 | 8 | **Live.** Many tokens fall from the ribbon into the kernel band. A glowing gate sits in the band. Grey tokens (other processes) pass straight through and fade. Gold tokens (the target) stop at the gate. | grey pass on beats, gold stops on bar 2 beat 1 | *A return probe on handle_mm_fault() sees every fault, and keeps only the target's.* |
| 4.4 | 3:50 | 8 | Each kept token is sorted into one of four wells in the kernel band — minor·anon, minor·file, major·anon, major·file — and the wells fill like liquid. The **minor** and **major** slots tick up. | sort on beats, wells finish on bar 8 beat 1 | *Sorted by the kernel's own result: minor or major, anon or file.* |
| 4.5 | 4:10 | 4 | **Exit snapshot.** A short ribbon (a 20 ms program) appears and vanishes before a polling dot can reach it; at the moment it vanishes, a camera-flash frame freezes its three numbers. | flash on 1 | *Short programs: a snapshot as the last thread exits.* |

```c
/* entry: only the target's thread group goes on */
if (current->tgid != target_tgid) return 1;
/* return: the kernel has decided */
if (!(ret & (VM_FAULT_RETRY | VM_FAULT_ERROR)))
        major ? major_cnt++ : minor_cnt++;
```

### Act 5 — Walkthrough: the tool running (4:20–5:40) · REPORT §4.5, §5, E7

This is the live demo, staged as a terminal that sits on top of the ribbon.

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 5.1 | 4:20 | 4 | A terminal panel slides up from the kernel band. The command types itself in (one word per beat). | command complete on bar 4 beat 1 | `sudo tools/pfstat -w 0.5 -- tests/faultgen ...` |
| 5.2 | 4:30 | 4 | The ribbon above the terminal belongs to faultgen now: 16 regions, 2.2 MB. | — | *Run mode: count a program from its first instruction.* |
| 5.3 | 4:40 | 8 | **anon:64.** A wide gold-outlined block grows into the ribbon (+1 region, size → 66.2 MB). Then its pages fill gold, fast; the **minor** slot races to 16,954. A second line under the ribbon (resident) catches up with the first (virtual). | block grows on 1; fill ends on bar 8 beat 1 | *Map 64 MB: address space jumps. Touch it: RAM follows.* |
| 5.4 | 5:00 | 8 | **file.** A wide blue block grows in (+1 region, 98.2 MB). Its pages fill red one by one, each with a small drop to the disk band; the **major** slot climbs to 8,193. | each page red on a beat (stylized), ends on bar 8 beat 1 | *Read a cold file: one disk read per page.* |
| 5.5 | 5:20 | 4 | **free.** Both blocks collapse out of the ribbon; it closes back to 16 regions, 2.2 MB. | collapse on 1 | *Free: regions and size fall back.* |
| 5.6 | 5:30 | 4 | The terminal prints the summary lines with `match vs getrusage()` in green. Hold. | — | (terminal) |

```text
  Memory regions at exit                    16
  Peak virtual address space           98.2 MB
  Minor page faults                     16,530   match vs getrusage()
  Major page faults                      8,193   match vs getrusage()
```

### Act 6 — Experiments (5:40–7:00) · REPORT §6.1–6.2

One stage: a single 32 MB file ribbon (8,192 pages) in the center. Each experiment **replays the same file** with a different rule. The picture changes only in how the pages fill.

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 6.1 | 5:40 | 8 | **E3, cold + random.** Pages fill red in random order, each with a disk drop. Major counter → 8,192. | — | *E3 · cold cache, random: 8,192 major.* |
| 6.2 | 6:00 | 8 | **E5, readahead on.** One red page, then a gold wave rolls ahead of the reader and every later page is already green when reached. Major counter → 1. | wave starts on bar 2 beat 1 | *E5 · readahead: the disk runs ahead. 1 major.* |
| 6.3 | 6:20 | 8 | **E4, warm + fault-around.** Pages light up 16 at a time (one fault maps 16 neighbors). Minor counter → about 511. | one group of 16 per beat | *E4 · warm cache: one fault maps 16 pages. 8,192 / 16 ≈ 512.* |
| 6.4 | 6:40 | 8 | **E6, huge pages.** Switch to the 64 MB anon block; it fills in 32 big tiles instead of 16,384 small ones. Minor counter → about 35. | one tile per beat | *E6 · 2 MB pages: about 35 faults instead of 16,384.* |

A small baseline note writes in once at 6.1 and stays: `counts shown after faultgen's own startup (~65 anon, ~75 file)`.

### Act 7 — Correctness and findings (7:00–8:30) · REPORT §6.1, §7

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 7.1 | 7:00 | 8 | **E1.** The `sleep` ribbon returns. The scoreboard fills 30 · 5.6 MB · 104 · 0, and beside each slot a reference value from `/proc` writes in; each pair locks together with a green tick. Then PID 1: 113 · 22.1 MB · 35,741 · 95, also all ticks. | one tick per beat | *Checked against /proc for sleep and for PID 1. All match.* |
| 7.2 | 7:20 | 8 | **F3, the hinted tracepoint.** On the token's path through the kernel band, a red marker sits at the entry (fires before the result) and a green one at the exit (sees the result). The token passes the red one blank, the green one coloured. | red on 1, green on bar 2 beat 1 | *The suggested tracepoint fires too early, and only on x86. This VM is arm64.* |
| 7.3 | 7:40 | 8 | **F7, children.** The gcc ribbon is short; four child ribbons (cc1, as, collect2, ld) branch below it, linked by shared color, not arrows. Without `-f` only the parent's tokens count (304); with `-f` the children's tokens pour in (6,001). | pour starts on bar 3 beat 1 | *95% of gcc's faults happen in its children. Follow mode counts them.* |
| 7.4 | 8:00 | 4 | **F6, fork before exec.** A brief ghost ribbon (51 regions, 20 MB) flickers before faultgen's ribbon replaces it. | flicker on 1 | *The first sample was the forked Python, not faultgen.* |
| 7.5 | 8:10 | 8 | **F12, auto-reaped children.** A child token drops out of the gcc tree without being "waited for"; pfcount counts it, the getrusage reference doesn't. The difference shows as yellow, labelled as expected. | — | *wait4() is a lower bound. A higher count is not an error.* |

### Act 8 — Limits and conclusion (8:30–9:30) · REPORT §8–9

| # | Time | Bars | Picture | Beat | Text |
|---|---|---|---|---|---|
| 8.1 | 8:30 | 8 | The ribbon dims. Four short limit lines write in one per bar, each next to the part of the picture it limits (live counts start at selection; descendants via real_parent; overhead not measured; tested only on 6.8 arm64). | one line per bar | (the limits) |
| 8.2 | 8:50 | 8 | Ribbon brightens. The scoreboard enlarges to center: four slots, each with its kernel source and its check written underneath. | one slot per bar | *Four numbers. Each checked against the kernel.* |
| 8.3 | 9:10 | 8 | The ribbon lifts into 3D (heights = region size, log scale) and the camera makes one slow orbit; it settles back to flat on the last downbeat. Title and credits write in. | orbit ends on bar 8 beat 1 | *pfcount and pfstat · CPE333 Mini-Project 02* · image credits |

---

## 4. Build order

1. **Shared kit first:** `B`, the ribbon, kernel band, fault token with trail, scoreboard. Render a 20-second test of Act 0 + Act 2.3 and check the token reads clearly.
2. Acts 1–3 (setup, background, regions).
3. Acts 4–5 (fault counting and the demo); this is where the data must match `results/e7-timeline.txt`.
4. Act 6 (experiments as one replayed stage).
5. Acts 7–8.
6. Render, check the storyboard sheets, then lay music to the 96 BPM grid. Voice-over goes on the phrase holds.

## 5. Data each act uses

| Act | Source |
|---|---|
| 3 | `results/e1a-report-sleep.txt` (30 regions, 5,684 KB) |
| 4 | REPORT §4.2–4.3, E7 well totals (16,452 / 78 / 0 / 8,193) |
| 5 | `results/e7-timeline.txt` |
| 6 | E2–E6 tables in REPORT §6.2 |
| 7 | E1 (§6.1), E8 (§6.4), F3, F6, F7, F12 |
| 8 | §8, §9 |

## 6. Open choices

- **96 BPM** suits a calm explainer. If the music you pick is faster, change `B` alone; shot lengths are in beats and will follow.
- The page counts in Acts 5–6 are stylized: a few hundred tiles stand for 8,192 or 16,384 pages, while the counters show the real numbers.
