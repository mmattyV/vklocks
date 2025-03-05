## Lab Notebook Entry: Design Decisions for My Distributed System

### 1. Overall System Architecture

- **Multiple Virtual Machines Simulation:**  
  I decided to simulate multiple virtual machines (VMs) as separate entities, each with its own logical clock and network queue. Even though they run on a single physical machine, I modeled them as independent processes that communicate over the network. This approach allowed me to study clock drift and asynchronous behavior.

- **Logical Clock Implementation:**  
  To maintain a consistent ordering of events, I implemented a logical clock for each VM based on Lamport’s clock algorithm. Each VM updates its clock on internal events, send events, and when processing a received message by taking the maximum of its own clock and the incoming clock before incrementing.

### 2. Handling Concurrency and Timing

- **Random Tick Rate:**  
  I assigned each virtual machine a random tick rate between 1 and 6 ticks per second during initialization. This decision simulates machines running at different speeds, which is crucial for analyzing asynchronous behavior and clock drift. The tick rate dictates how many events (or instructions) a VM can process per second.

- **Threading Model:**  
  To manage asynchronous communication without blocking the simulation loop, I ran the gRPC server on a separate thread for each VM. This ensures that incoming messages are received and enqueued promptly while the main simulation loop continues to execute based on the VM's internal clock.

- **Message Queue:**  
  I used Python’s `queue.Queue` to create a thread-safe message queue. This queue decouples message reception (which is asynchronous) from event processing (which is controlled by the tick rate). It ensures that messages are processed in the order they arrive without interfering with the timed simulation loop.

### 3. Communication Between Virtual Machines

- **Using gRPC for Inter-VM Communication:**  
  I chose gRPC as the communication framework because it provides a robust, type-safe, and scalable method for sending messages. With Protocol Buffers defining the message format, I was able to efficiently serialize and deserialize clock messages. Each VM runs its own gRPC server to listen for incoming messages and uses gRPC client stubs to send messages to its peers.

- **Event-Driven Messaging:**  
  The simulation logic decides on every tick whether to process a message from the queue or generate a random event. If a send event is chosen, the VM uses gRPC to send its current logical clock to a designated peer (or broadcasts to all peers). This design clearly separates the communication logic from the clock update logic.

### 4. Logging and Analysis

- **Detailed Event Logging:**  
  I built comprehensive logging into the system. Each VM writes to its own log file and also logs to the console. Every log entry captures the type of event (internal, send, receive), the system time, the updated logical clock, and additional context (like the current queue length for received messages). This detailed log enables me to analyze the behavior of the system, track clock drift, and verify that the logical clocks are updating correctly.

### 5. Launching the Simulation

- **Script for Concurrent Startup:**  
  Finally, I wrote a helper script that uses Python's `subprocess` module to start all VM instances simultaneously. This script makes it easy to launch multiple VMs, each with its designated port and peer configurations, so that I can observe the system’s behavior as a whole.

---

In summary, my design choices were driven by the need to simulate a realistic asynchronous distributed system with varying clock speeds, robust inter-process communication via gRPC, and detailed logging for analysis. Every decision, from the tick rate selection to the threading model and logging details, was carefully considered and documented in my lab notebook.

## Lab Notebook: Experimental Observations for Range 1-6

After running the scale model experiments five times (each run lasting at least one minute), I analyzed the logs and collected the following statistics. Here’s a summary of my observations and reflections on the logical clock behavior, clock drift, and the impact of timing variations:

### Experiment Run 1
- **Tick Rates:**  
  - *machine1:* 3 ticks per second  
  - *machine2 & machine3:* 2 ticks per second
- **Logical Clock Jumps:**  
  - *machine1:* Average jump ~1.01, with very consistent increments (min = 1, max = 2, std = 0.08)  
  - *machine2 & machine3:* Average jumps are higher (~1.47–1.48) with slightly more variability (max up to 6–7).
- **Message Queue Lengths:**  
  - All machines had very low average queue lengths (<0.1).
- **Drift:**  
  - The final clock values differed by 4 ticks at most.
- **Observations:**  
  I noted that when the tick rates are only slightly different (3 vs. 2 ticks per second), the logical clock jumps remain small and the system drift is minimal. This run suggested that minor timing differences lead to only small variations in clock values.

### Experiment Run 2
- **Tick Rates:**  
  - *machine1:* 2 ticks per second  
  - *machine2:* 5 ticks per second  
  - *machine3:* 2 ticks per second
- **Logical Clock Jumps:**  
  - *machine2,* which had a much higher tick rate, showed very consistent jumps (avg = 1.00, with no variation)  
  - *machine1 & machine3:* Both had larger average jumps (~2.47) with high variability (max = 13).
- **Message Queue Lengths:**  
  - *machine2* had almost zero queue length, while the others had moderate queue lengths.
- **Drift:**  
  - The overall drift was small (final clock difference = 2).
- **Observations:**  
  The high tick rate on machine2 meant it processed events very regularly, resulting in smaller jumps and almost no message queuing. In contrast, the lower tick rate machines experienced larger jumps, likely as they processed a backlog of events. Even with these differences, the overall drift between machines remained low.

### Experiment Run 3
- **Tick Rates:**  
  - *machine1 & machine3:* 4 ticks per second  
  - *machine2:* 1 tick per second
- **Logical Clock Jumps:**  
  - *machine2* had much larger average jumps (~2.90) with variability up to 12 ticks, reflecting its slower processing speed.  
  - *machine1 & machine3* had consistent small jumps (avg ~1.09).
- **Message Queue Lengths:**  
  - *machine2* accumulated a very high average queue length (13.50), indicating a significant backlog due to its slow tick rate.
- **Drift:**  
  - The final logical clock values differed by 86 ticks—machine2 lagged far behind.
- **Observations:**  
  This run clearly shows the impact of a machine operating at a significantly lower tick rate. Machine2’s slow pace not only caused larger jumps (to catch up) but also led to a massive build-up of messages. The drift was substantial, highlighting that extreme timing differences can dramatically affect synchronization.

### Experiment Run 4
- **Tick Rates:**  
  - *machine1 & machine3:* 4 ticks per second  
  - *machine2:* 3 ticks per second
- **Logical Clock Jumps:**  
  - All machines showed relatively consistent small jumps (avg ~1.06–1.38) with low variability.
- **Message Queue Lengths:**  
  - Queue lengths remained very low (<0.23) across the board.
- **Drift:**  
  - Final clock values differed by only 5 ticks.
- **Observations:**  
  With more balanced tick rates, the system maintained good synchronization. The jump sizes were uniform, and minimal message queuing was observed. This run confirms that reducing the variation in tick rates minimizes drift and event gaps.

### Experiment Run 5
- **Tick Rates:**  
  - *machine1:* 4 ticks per second  
  - *machine2 & machine3:* 5 ticks per second
- **Logical Clock Jumps:**  
  - *machine2 & machine3* had very consistent small jumps (avg ~1.07–1.08)  
  - *machine1* had slightly larger jumps (avg ~1.34).
- **Message Queue Lengths:**  
  - All machines had very low average queue lengths (<0.20).
- **Drift:**  
  - The final drift was minimal (only 1 tick difference).
- **Observations:**  
  When the tick rates are close (4 vs. 5 ticks per second), the system demonstrates excellent synchronization. The low drift and small, consistent jump sizes indicate that timing variations are almost negligible in their impact.

---

## Overall Reflections

- **Size of Jumps:**  
  The size of the jumps in the logical clocks directly correlates with the machine's tick rate and event processing. Faster machines (higher tick rates) tend to have smaller, more consistent jumps. In contrast, slower machines sometimes show larger jumps as they attempt to catch up after processing a backlog.

- **Clock Drift:**  
  There is noticeable drift when there is a significant difference in tick rates—as seen in Experiment Run 3, where machine2 lagged due to a much slower tick rate. When the tick rates are more balanced, drift is minimal (e.g., Experiment Run 5).

- **Message Queue Impact:**  
  The length of the message queue is an important indicator of processing delays. In the run where a machine had a very low tick rate (Experiment Run 3), the message queue length was high, highlighting that many messages were waiting to be processed. Conversely, when machines operate at similar speeds, the queues remain short.

- **Timing Gaps:**  
  Different timings also affect the gaps in the logical clock values. When a machine processes events more slowly, the gaps (or jumps) are larger. This leads to more irregular updates, which can be clearly seen by the higher standard deviation in jump sizes.

## Lab Notebook: Analysis of Logical Clock Dynamics for Range 1-100

After running the model under conditions where the tick rate (clock cycle) is randomly selected between 1 and 100, I gathered the following statistics for five experiment runs. Below are my observations and reflections on the size of the jumps in logical clock values, the drift between the machines, and the effects on the message queue lengths.

---

### Experiment Run 1
- **Tick Rates:**
  - Machine1: 25 ticks/sec
  - Machine2: 100 ticks/sec
  - Machine3: 45 ticks/sec
- **Logical Clock Jumps:**
  - *Machine1:* Average jump = 3.67 (min 1, max 26, std 3.59)
  - *Machine2:* Average jump = 1.00 (perfectly consistent)
  - *Machine3:* Average jump = 2.16 (min 1, max 17, std 2.31)
- **Message Queue Lengths:**
  - *Machine1:* Average queue length = 2.33
  - *Machine2:* Queue length = 0.00
  - *Machine3:* Average queue length = 0.24
- **Drift:**  
  The final logical clock values drifted by 6 ticks.

*Observations:*  
In Run 1, the large tick rate of Machine2 (100 ticks/sec) led to minimal jumps, while the slower Machine1 (25 ticks/sec) showed larger jumps and a longer message queue. The drift of 6 ticks, though small compared to the overall clock values, indicates that slower machines tend to "jump" more when processing backlogged messages.

---

### Experiment Run 2
- **Tick Rates:**
  - Machine1: 63 ticks/sec
  - Machine2: 51 ticks/sec
  - Machine3: 30 ticks/sec
- **Logical Clock Jumps:**
  - *Machine1:* Avg jump = 1.02
  - *Machine2:* Avg jump = 1.24 (max = 7, std 0.70)
  - *Machine3:* Avg jump = 2.01 (max = 14, std 1.77)
- **Message Queue Lengths:**
  - *Machine1:* ~0.02
  - *Machine2:* ~0.09
  - *Machine3:* ~0.43
- **Drift:**  
  Final clock values were equal (drift = 0).

*Observations:*  
When tick rates are more balanced (63, 51, and 30), the machines remain tightly synchronized. Although Machine3, with the lowest tick rate, shows slightly larger jumps and a longer queue, the overall drift is negligible.

---

### Experiment Run 3
- **Tick Rates:**
  - Machine1: 86 ticks/sec
  - Machine2: 75 ticks/sec
  - Machine3: 72 ticks/sec
- **Logical Clock Jumps:**
  - *Machine1:* Avg jump = 1.02
  - *Machine2:* Avg jump = 1.17
  - *Machine3:* Avg jump = 1.22
- **Message Queue Lengths:**
  - Very low across all machines (0.06 to 0.12)
- **Drift:**  
  Drift of 2 ticks between the fastest and slowest.

*Observations:*  
With high and similar tick rates, all machines show consistent clock increments with minimal drift and almost no message queuing. The slight differences in jump sizes reflect minor processing differences.

---

### Experiment Run 4
- **Tick Rates:**
  - Machine1: 33 ticks/sec
  - Machine2: 48 ticks/sec
  - Machine3: 97 ticks/sec
- **Logical Clock Jumps:**
  - *Machine1:* Avg jump = 2.77
  - *Machine2:* Avg jump = 1.98
  - *Machine3:* Avg jump = 1.00
- **Message Queue Lengths:**
  - *Machine1:* 0.63
  - *Machine2:* 0.24
  - *Machine3:* 0.01
- **Drift:**  
  A drift of 4 ticks between the highest and lowest values.

*Observations:*  
Here, the divergence in tick rates (especially Machine3 being much faster) results in larger jumps on the slower machines and a moderate drift. Machine1’s higher average jump and longer queue indicate that a lower tick rate can lead to processing backlogs.

---

### Experiment Run 5
- **Tick Rates:**
  - Machine1: 77 ticks/sec
  - Machine2: 91 ticks/sec
  - Machine3: 51 ticks/sec
- **Logical Clock Jumps:**
  - *Machine1:* Avg jump = 1.19
  - *Machine2:* Avg jump = 1.01
  - *Machine3:* Avg jump = 1.78
- **Message Queue Lengths:**
  - All machines have very low queue lengths (0.04 to 0.27)
- **Drift:**  
  Drift of 1 tick.

*Observations:*  
When the machines operate at more similar speeds (77, 91, and 51 ticks/sec), the logical clocks are nearly in sync, as indicated by the minimal drift. Even though Machine3 still shows a slightly larger jump size, the overall performance is well-coordinated.

---

### Overall Reflections

- **Jump Sizes:**  
  The jump sizes are inversely related to the tick rates. Higher tick rates (e.g., 100 ticks/sec) result in very consistent jumps (near 1 per tick), whereas lower tick rates show larger and more variable jumps as machines “catch up” when processing queued messages.

- **Drift:**  
  When machines have similar tick rates, the final logical clock values are nearly identical. However, when the tick rates differ significantly, drift increases. This effect is especially pronounced when a machine with a very low tick rate must process a large backlog (as seen in Run 3).

- **Message Queue Length:**  
  Longer message queues are observed in slower machines, which experience larger jumps. Conversely, faster machines keep their queues nearly empty.

- **Impact of a Wider Range (1 to 100 vs. 1 to 6):**  
  By expanding the tick rate variation to 1–100, I observed a much broader range of behaviors. This allowed me to see pronounced differences in logical clock behavior, with high-speed machines maintaining near-continuous updates and slower machines showing irregular, larger jumps and more queue buildup.

## Lab Notebook: Comparing High Variation vs. Tight Mode with Lower Internal Event Probability

In my experiments I compared two different configurations for the distributed system:

1. **High Variation Mode (Default):**  
   Here, the tick rate (clock cycle) could vary over a wide range (ideally 1–100 ticks per second) and the probability of an internal event was relatively high. In that case, slower machines would often process backlogged messages (resulting in larger jumps) and message queues could become long, leading to greater drift between machines.

2. **Tight Mode with Lower Internal Event Probability:**  
   In this configuration, I forced the tick rate to be in a narrow range (1–2 ticks per second) and enabled tight mode, which reduces the probability of internal events. That means the machines are more likely to send messages rather than simply updating their clock internally. The statistics below are from the tight mode experiments:

---

### Experiment Run 1 (Tight Mode, 1–2 ticks/sec)
- **Tick Rates:**  
  - All machines are running at about 2 ticks per second.
- **Final Logical Clocks:**  
  - Machine1: 133  
  - Machine2: 134  
  - Machine3: 133
- **Logical Clock Jumps:**  
  - Averages are around 1.12–1.13, with minimal variation (std ≈ 0.32–0.35).  
- **Average Message Queue Length:**  
  - Very low (approximately 0.06 to 0.14).
- **Drift:**  
  - A drift of only 1 tick across machines.
  
*Observations:*  
With tight mode enabled and all machines running nearly identically at 2 ticks per second, the lower probability of internal events causes more send events. This results in very consistent, small jumps and almost no backlog, keeping the machines in tight sync.

---

### Experiment Run 2 (Tight Mode, 1 tick/sec)
- **Tick Rates:**  
  - All machines are running at 1 tick per second.
- **Final Logical Clocks:**  
  - Machine1: 66  
  - Machine2: 66  
  - Machine3: 65
- **Logical Clock Jumps:**  
  - Jumps average about 1.10, with very little variation.
- **Average Message Queue Length:**  
  - Nearly zero for Machine2 and Machine3; Machine1 shows a slight queue (0.34).
- **Drift:**  
  - A drift of 1 tick.
  
*Observations:*  
When all machines are slow (1 tick/sec) and nearly identical, even with a low internal event probability, synchronization is maintained well. The low processing speed does allow for a slight queue in one machine, but overall, the clocks remain very close.

---

### Experiment Run 3 (Mixed Tick Rates: One at 1 tick/sec, Two at 2 ticks/sec)
- **Tick Rates:**  
  - Machine1: 1 tick/sec  
  - Machine2: 2 ticks/sec  
  - Machine3: 2 ticks/sec
- **Final Logical Clocks:**  
  - Machine1: 115  
  - Machine2: 124  
  - Machine3: 124
- **Logical Clock Jumps:**  
  - Machine1 shows an average jump of 1.93 (with max up to 7), while Machine2 and Machine3 average around 1.04.
- **Average Message Queue Length:**  
  - Machine1’s queue averages 4.71, while the others have nearly no backlog.
- **Drift:**  
  - A drift of 9 ticks.
  
*Observations:*  
A small imbalance in tick rate—with one machine running at 1 tick/sec and the others at 2 ticks/sec—causes the slower machine (Machine1) to build up a backlog. Even though tight mode reduces internal events (thus encouraging sends), the slower processing still leads to larger jumps when Machine1 eventually processes its queue. This results in a noticeable drift.

---

### Experiment Run 4 (Uniform 2 ticks/sec)
- **Tick Rates:**  
  - All machines: 2 ticks/sec.
- **Final Logical Clocks:**  
  - All machines reach about 130.
- **Logical Clock Jumps:**  
  - Consistent jumps averaging ~1.09, with very low variability.
- **Average Message Queue Length:**  
  - Very low (approximately 0.17 to 0.20).
- **Drift:**  
  - Zero drift.
  
*Observations:*  
When all machines are running at 2 ticks per second and tight mode is enabled, the system is highly synchronized. The lower chance of internal events means that almost every tick leads to a send (or broadcast), keeping the clocks updated uniformly and the queues minimal.

---

### Experiment Run 5 (Mixed: Two at 1 tick/sec, One at 2 ticks/sec)
- **Tick Rates:**  
  - Machine1: 1 tick/sec  
  - Machine2: 2 ticks/sec  
  - Machine3: 1 tick/sec
- **Final Logical Clocks:**  
  - Machine1: 100  
  - Machine2: 119  
  - Machine3: 117
- **Logical Clock Jumps:**  
  - Machine1: avg = 1.68; Machine2: avg = 1.00; Machine3: avg = 1.97.
- **Average Message Queue Length:**  
  - Machine1 has an average queue length of 5.53, Machine3 is 1.31, and Machine2 has no queue.
- **Drift:**  
  - A drift of 19 ticks.
  
*Observations:*  
In Run 5, the mix of tick rates (with two machines at 1 tick/sec and one at 2 ticks/sec) leads to significant drift. The machines with the slower tick rate not only exhibit larger jumps but also accumulate longer message queues. Even though tight mode reduces internal events and favors sending, the inherent difference in processing speed causes the slower machines to lag behind noticeably.

---

## Overall Reflections

- **Effect of Tight Mode (Lower Internal Event Probability):**  
  Tight mode increases the chance that an event will be a send rather than an internal update. This generally leads to more frequent communication between machines and more uniform updates of the logical clocks. When machines run at similar speeds, this mode results in very consistent clock jumps and minimal drift.

- **Impact of Tick Rate Variation:**  
  The statistics clearly show that even small differences (e.g., 1 tick/sec versus 2 ticks/sec) can have a significant impact. When machines are uniform, drift is nearly zero. However, even a slight imbalance causes the slower machine to build a backlog, resulting in larger jump sizes and increased drift.

- **Message Queue Dynamics:**  
  Faster machines process messages quickly, keeping their queues near zero. Slower machines, however, build up longer queues, which force them to make larger jumps when processing, thereby increasing the drift between machines.

These findings highlight that in distributed systems, maintaining uniform processing speeds and reducing the chance of internal (non-communicative) events are key to achieving tight synchronization. I have documented these insights in my lab notebook, and they will inform future work on optimizing clock synchronization in asynchronous systems.