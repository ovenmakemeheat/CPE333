# Mini-Project 02: Where the Memory Goes (video script)

## Draft — *Where the Memory Goes*

**Target runtime:** about 9 minutes, within the assignment’s 7–11 minute limit.  
**Format:** English narration with code and terminal demonstration.  
**Core message:** `pfcount` and `pfstat` make a process’s memory behavior visible, and check their measurements against independent Linux interfaces.

### 00:00–00:40 — Hook

**Visual:** A 32 MB file splits into two paths: random reads through a cold cache, then a sequential read with readahead. Show the resulting major-fault counts side by side.

**Narration:**

> The same 32-megabyte file can trigger eight thousand major page faults—or about one, after startup overhead. The file didn’t change. The access pattern did.
>
> We built a Linux tool that shows what’s happening inside a process’s memory as it runs: what it has mapped, what it has touched, and what kind of page faults it triggers.

### 00:40–01:25 — The project

**Visual:** Title card: *CPE333 · Virtual Memory · Page-Fault Counter*. Briefly show the project structure: `pfcount`, `pfstat`, and `faultgen`.

**Narration:**

> The assignment was to monitor a process by its process ID and report four things: its number of memory regions, its total virtual address space, and its minor and major page faults.
>
> Our implementation has three parts. `pfcount` is the kernel module. `pfstat` is the command-line interface. And `faultgen` creates controlled workloads so we can test the counts instead of just hoping they’re right.
>
> We tested it in Ubuntu 24.04, running kernel 6.8 on arm64 inside a Lima virtual machine. The module needs a Linux kernel, so it can’t run directly on the Mac host.

### 01:25–02:15 — What the numbers mean

**Visual:** Draw a process address space as labeled blocks—executable, heap, anonymous mapping, stack. Show a large mapped region whose resident portion fills in only as it’s touched.

**Narration:**

> A process doesn’t see physical memory directly. It sees a virtual address space, divided into regions called virtual memory areas, or V-M-As. Each region is a contiguous range with its own permissions and backing—perhaps a file, anonymous memory, the heap, or the stack.
>
> Mapping memory reserves address space; it doesn’t mean every page is already resident in RAM. When the process first accesses a page, the CPU raises a page fault and Linux resolves it.
>
> A minor fault can be handled without waiting for disk I/O—for example, by supplying a zero-filled page or mapping data already in the page cache. A major fault requires I/O. Resident memory grows when pages are actually brought in, not just when address space is reserved.

### 02:15–03:20 — Counting regions and address space

**Visual:** Show a short, readable excerpt from `module/pfcount.c`; highlight `get_task_mm`, the memory-map lock, and the VMA walk. Then show `pfstat --maps` beside `/proc/PID/maps`.

**Narration:**

> To count regions, the module gets the target process’s memory descriptor and walks its V-M-As while holding the memory-map read lock.
>
> For each region, it adds the difference between the ending and starting address. That gives us both the number of regions and the total virtual size.
>
> We don’t treat those numbers as self-validating. The V-M-A count and summed size are checked against `/proc`’s map listing, and the total is also checked against the kernel’s `total_vm` value and the process’s reported `VmSize`.
>
> In the command line, `pfstat` can show the summary or print each region with `--maps`, making it possible to inspect what went into the total.

### 03:20–04:30 — Counting faults

**Visual:** Animate a fault entering `handle_mm_fault`, then returning as either minor or major. Show the counter split into lifetime totals and live counts.

**Narration:**

> Faults need two views. Lifetime counters show what the process has accumulated since it started. Live counters show faults observed after monitoring begins.
>
> For the lifetime view, the module sums the counters across the process’s threads, including counts saved for threads that have already exited. It reads them under the kernel’s statistics lock, because a careless thread walk can double-count a thread as it exits.
>
> For live tracking, we use a return probe on `handle_mm_fault`. At entry, it filters for the selected process and saves the context it needs. At return, it checks the kernel’s result and classifies the fault as minor or major, and as anonymous or file-backed.
>
> The hint in the assignment points to a page-fault tracepoint. But the suggested tracepoint isn’t suitable for this arm64 test environment, and it fires before the fault is resolved—too early to classify the result. The return probe lets us count after Linux has handled the fault.

### 04:30–06:30 — Demonstration

**Visual:** Show the command in the Linux VM, then let the terminal output appear at a readable pace. Highlight the time, region, virtual-size, resident-size, and fault columns.

```sh
sudo tools/pfstat -w 0.5 -- tests/faultgen sleep:1 anon:64 sleep:1 file:/tmp/pfcount-big.bin sleep:1 free sleep:1
```

**Narration:**

> This run gives us a process we can watch. It pauses, maps 64 megabytes of anonymous memory, touches one byte per 4-kilobyte page, then reads a 32-megabyte file with a cold cache and random access. Finally, it frees the mappings.
>
> Watch what changes first. At one second, the address space grows from about 2.2 megabytes to 66.2 megabytes, and the region count goes up by one. But resident memory is only about 7.9 megabytes. The mapping exists; most of its pages haven’t been touched yet.
>
> Half a second later, resident memory is about 65.4 megabytes. The process has now touched almost every page in that anonymous mapping, and the minor-fault count has surged.
>
> Next, the file mapping appears. Virtual size grows to about 98.2 megabytes. At two-and-a-half seconds, resident memory is about 97.2 megabytes and the major-fault count reaches 8,193.
>
> Then `free` unmaps both allocations. The region count falls from 18 to 16, and virtual size returns to about 2.2 megabytes.
>
> This timeline makes the distinction visible: virtual size changes when memory is mapped; resident memory and page-fault counts change as the process accesses it.

### 06:30–07:45 — Validation and findings

**Visual:** Show three cards: `/proc` comparison, cold random file, sequential read. Include a small “startup baseline subtracted” note beneath the adjusted fault totals.

**Narration:**

> We checked the results against independent sources. For a sleeping process, the tool reported 30 regions, about 5.6 megabytes of virtual space, 104 minor faults, and no major faults. The region count and size matched `/proc`; the fault counts matched `/proc`’s process statistics.
>
> The controlled workloads show why access patterns matter. A cold random read of 8,192 file pages produced 8,193 major faults in total. One was the program’s startup baseline; the file workload itself accounted for 8,192.
>
> With sequential reading and readahead, the total was two major faults—about one for the file after startup. With cached data, fault-around can map neighboring pages together, so a warm read doesn’t necessarily produce one fault per page. Huge pages change the count too: a 64-megabyte anonymous workload took roughly 35 faults after baseline, rather than around 16,384 with ordinary 4-kilobyte pages.

### 07:45–08:35 — Hard cases

**Visual:** Show a short-lived process exiting before a polling sample, then a process tree with `gcc` and its helper programs.

**Narration:**

> We also had to handle cases that a simple polling loop misses. A very short program can exit before the first sample, so an exit-time probe records its region count, size, and peak size while its memory descriptor is still available.
>
> And some commands do most of their work in child processes. In our tests, `gcc` launched tools such as `cc1`, the assembler, and the linker. Follow mode tracks descendants so its fault totals can be compared with the child-resource accounting.
>
> That comparison has a boundary: automatically reaped children aren’t always included in `wait4`’s reference totals. The tool reports that difference as a lower-bound comparison, not as proof that its count is wrong.

### 08:35–09:10 — Close

**Visual:** Return to the four assignment requirements. End on the project name and the checked-in report/results.

**Narration:**

> The result is a process-level view of four things the assignment asked us to measure: memory regions, virtual address space, minor faults, and major faults.
>
> We checked those counts against `/proc` and `getrusage`, and used controlled workloads to see how demand paging, caching, readahead, and huge pages change what a process experiences.
>
> The main lesson is simple: a memory map isn’t the same as memory in RAM, and the number of faults depends on how the process reaches its data. With `pfcount` and `pfstat`, we can observe that behavior instead of guessing.

## Notes

**Demo note:** The on-screen values above come from the checked-in experiment results; a fresh run will have a different PID and may vary slightly.

**Production note:** The HyperFrames usage check returned `unknown` (`unsupported_harness`), so available usage is unverified.
