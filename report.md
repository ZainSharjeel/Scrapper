Parallel Execution Report: Comparing Threading, Multiprocessing, Joblib, and Hybrid

1. ThreadPoolExecutor (Multithreading)
   - Uses threads within a single process.
   - Ideal for I/O-bound operations like web scraping.
   - Each origin is processed by a separate thread.
   - Number of threads = number of origins (unless otherwise limited).
   - Collected using `threading.get_ident()`.

2. ProcessPoolExecutor (Multiprocessing)
   - Spawns separate processes (each with its own memory space).
   - Good for CPU-bound tasks.
   - Each origin is handled by a separate process.
   - Process IDs captured using `os.getpid()`.

3. joblib.Parallel
   - Built on top of multiprocessing.
   - Uses `n_jobs=-1` to fully utilize all available CPU cores.
   - Automatically manages process-level parallelism.
   - Simpler API and more control over shared memory.
   - Does not support thread-level control directly.

4. Hybrid (Multiprocessing + Threading)
   - Launches multiple processes (like ProcessPoolExecutor).
   - Each process then starts a ThreadPoolExecutor.
   - Each thread handles a different origin inside each process.
   - Useful when combining CPU + I/O parallelism.
   - Thread + process IDs are both captured.

5. GPU Acceleration:
   - Not applicable.
   - Web scraping is I/O-bound and does not benefit from GPU parallelism.

Each approach was measured using `time.time()` for execution duration comparison.
