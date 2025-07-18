from math import ceil
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from joblib import Parallel, delayed

import matplotlib.pyplot as plt
import os

from main import scrape_kayak_flights

def process_chunk(chunk):
    with ThreadPoolExecutor() as executor:
        return list(executor.map(lambda pair: scrape_kayak_flights(pair[0], pair[1]), chunk))

def chunkify(data, num_chunks):
    chunk_size = ceil(len(data) / num_chunks)
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
def scrape_pair(pair):
        origin, destination = pair
        return scrape_kayak_flights(origin, destination)

# old method
# def calculate_metrics(results, label, file_name):
#         all_crawled = [r['route'] for r in results if r]  # assuming each result has a 'route' key
#         total = len(all_crawled)
#         unique = len(set(all_crawled))
#         overlap = total - unique
#         coverage = unique / len(pairs)

#         # Example priority set (adjust as needed)
#         priority_pairs = [("Karachi", "Lahore"), ("Islamabad", "Karachi")]
#         priority_set = set(priority_pairs)
#         crawled_set = set(all_crawled)
#         quality = len(priority_set & crawled_set) / len(priority_set) if priority_set else 0

#         # Print to console
#         print(f"\n=== {label} Metrics ===")
#         print(f"Total Crawled: {total}")
#         print(f"Unique Crawled: {unique}")
#         print(f"Overlap: {overlap}")
#         print(f"Coverage: {coverage:.2f}")
#         print(f"Quality: {quality:.2f}")
#         print("==================================")

#         # Write to file
#         with open(file_name, "a", encoding="utf-8") as f:
#             f.write(f"\n=== {label} Metrics ===\n")
#             f.write(f"Total Crawled: {total}\n")
#             f.write(f"Unique Crawled: {unique}\n")
#             f.write(f"Overlap: {overlap}\n")
#             f.write(f"Coverage: {coverage:.2f}\n")
#             f.write(f"Quality: {quality:.2f}\n")
#             f.write("==================================\n")

# new method
def calculate_metrics(results, label, file_name):
    # Flatten the list of lists and extract (origin, destination) tuples
    all_crawled = [
        (flight.get("Origin"), flight.get("Destination"))
        for sublist in results if sublist
        for flight in sublist if flight
    ]
    
    total = len(all_crawled)
    unique = len(set(all_crawled))
    overlap = total - unique
    coverage = unique / len(pairs)

    # Example priority set (you can modify this as needed)
    priority_pairs = [("Karachi", "Islamabad"), ("Karachi", "Lahore")]
    priority_set = set(priority_pairs)
    crawled_set = set(all_crawled)
    quality = len(priority_set & crawled_set) / len(priority_set) if priority_set else 0

    # Print to console
    print(f"\n=== {label} Metrics ===")
    print(f"Total Crawled: {total}")
    print(f"Unique Crawled: {unique}")
    print(f"Overlap: {overlap}")
    print(f"Coverage: {coverage:.2f}")
    print(f"Quality: {quality:.2f}")
    print("==================================")

    # Write to file
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"Priority Pairs: {priority_pairs}\n")
        f.write(f"\n=== {label} Metrics ===\n")
        f.write(f"Total Crawled: {total}\n")
        f.write(f"Unique Crawled: {unique}\n")
        f.write(f"Overlap: {overlap}\n")
        f.write(f"Coverage: {coverage:.2f}\n")
        f.write(f"Quality: {quality:.2f}\n")
        f.write("==================================\n")

# for plotting graphs
def extract_metrics(results, label, execution_time, file_name):
    # Flatten the list of lists and extract (origin, destination) tuples
    all_crawled = [
        (flight.get("Origin"), flight.get("Destination"))
        for sublist in results if sublist
        for flight in sublist if flight
    ]
    
    total = len(all_crawled)
    unique = len(set(all_crawled))
    overlap = total - unique
    coverage = unique / len(pairs)

    # Example priority set (you can modify this as needed)
    priority_pairs = [("Berlin", "Paris"), ("Berlin", "London")]
    priority_set = set(priority_pairs)
    crawled_set = set(all_crawled)
    quality = len(priority_set & crawled_set) / len(priority_set) if priority_set else 0

    # Print to console
    print(f"\n=== {label} Metrics ===")
    print(f"Total Crawled: {total}")
    print(f"Unique Crawled: {unique}")
    print(f"Overlap: {overlap}")
    print(f"Coverage: {coverage:.2f}")
    print(f"Quality: {quality:.2f}")
    print("==================================")

    # Write to file
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"Priority Pairs: {priority_pairs}\n")
        f.write(f"\n=== {label} Metrics ===\n")
        f.write(f"Total Crawled: {total}\n")
        f.write(f"Unique Crawled: {unique}\n")
        f.write(f"Overlap: {overlap}\n")
        f.write(f"Coverage: {coverage:.2f}\n")
        f.write(f"Quality: {quality:.2f}\n")
        f.write("==================================\n")

    return {
        'label': label,
        'time': execution_time,
        'overlap': overlap,
        'coverage': coverage,
        'quality': quality
    }



if __name__ == "__main__":
    # origins = ["Karachi", "Lahore", "Islamabad"]
    # origins = ["Karachi", "Islamabad"]
    # origins = ["Hyderabad", "Multan", "Rawalpindi"]
    origins = ["London", "Paris", "Berlin"]
    pairs = [(o, d) for o in origins for d in origins if o != d]

    file_name = "output_EU.txt"
    all_metrics = []

    # === Sequential ===
    start_time = time.time()
    results_seq = [scrape_kayak_flights(o, d) for o, d in pairs]
    exec_time = time.time() - start_time
    all_metrics.append(extract_metrics(results_seq, "Sequential", exec_time, file_name))
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"Sequential Execution Time: {exec_time:.2f} seconds\n")

    # === ThreadPoolExecutor ===
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        results_thread = list(executor.map(lambda pair: scrape_kayak_flights(pair[0], pair[1]), pairs))
    exec_time = time.time() - start_time
    all_metrics.append(extract_metrics(results_thread, "ThreadPool", exec_time, file_name))
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"ThreadPoolExecutor Execution Time: {exec_time:.2f} seconds\n")

    # === ProcessPoolExecutor ===
    start_time = time.time()
    with ProcessPoolExecutor() as executor:
        results_process = list(executor.map(scrape_pair, pairs))
    exec_time = time.time() - start_time
    all_metrics.append(extract_metrics(results_process, "ProcessPool", exec_time, file_name))
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"ProcessPoolExecutor Execution Time: {exec_time:.2f} seconds\n")

    # === Joblib Parallel ===
    start_time = time.time()
    results_joblib = Parallel(n_jobs=-1)(delayed(scrape_kayak_flights)(o, d) for o, d in pairs)
    exec_time = time.time() - start_time
    all_metrics.append(extract_metrics(results_joblib, "Joblib", exec_time, file_name))
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"Joblib Parallel Execution Time: {exec_time:.2f} seconds\n")


    # === Hybrid ===
    num_threads_range = [1, 2, 4, 6, 8]
    for num_processes in num_threads_range:
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(f"Number of threads: {num_processes}\n")
        chunks = chunkify(pairs, num_processes)
        start_time = time.time()
        with ProcessPoolExecutor(max_workers=num_processes) as process_executor:
            nested_results = list(process_executor.map(process_chunk, chunks))
        exec_time = time.time() - start_time
        results_hybrid = [item for sublist in nested_results for item in sublist]
        all_metrics.append(extract_metrics(results_hybrid, f"Hybrid-{num_processes}", exec_time, file_name))
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(f"Hybrid Execution Time (Process + Thread): {exec_time:.2f} seconds\n")



    # === Plotting ===

    # Create output directory if needed
    plot_dir = "plots"
    os.makedirs(plot_dir, exist_ok=True)

    labels = [m['label'] for m in all_metrics]
    times = [m['time'] for m in all_metrics]
    overlaps = [m['overlap'] for m in all_metrics]
    coverages = [m['coverage'] for m in all_metrics]
    qualities = [m['quality'] for m in all_metrics]

    plt.figure(figsize=(14, 10))

    plt.subplot(2, 2, 1)
    plt.bar(labels, times, color='steelblue')
    plt.title('Execution Time')
    plt.ylabel('Seconds')
    plt.xticks(rotation=45)

    plt.subplot(2, 2, 2)
    plt.bar(labels, overlaps, color='orange')
    plt.title('Overlap')
    plt.ylabel('Duplicates')
    plt.xticks(rotation=45)

    plt.subplot(2, 2, 3)
    plt.bar(labels, coverages, color='green')
    plt.title('Coverage')
    plt.ylabel('Fraction')
    plt.xticks(rotation=45)

    plt.subplot(2, 2, 4)
    plt.bar(labels, qualities, color='purple')
    plt.title('Quality')
    plt.ylabel('Fraction')
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, "performance_metrics_EU.png"))  # Save all subplots in one image
    plt.show()


    # start_time = time.time()
    # results_seq = [scrape_kayak_flights(origin, destination) for origin, destination in pairs]
    # print(f"Sequential Execution Time: {time.time() - start_time} seconds")
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"Sequential Execution Time: {time.time() - start_time} seconds\n")

    # start_time = time.time()
    # with ThreadPoolExecutor() as executor:
    #     results_thread = list(executor.map(lambda pair: scrape_kayak_flights(pair[0], pair[1]), pairs))
    # print(f"ThreadPoolExecutor Execution Time: {time.time() - start_time} seconds")
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"ThreadPoolExecutor Execution Time: {time.time() - start_time} seconds\n")

        
    # start_time = time.time()
    # with ProcessPoolExecutor() as executor:
    #     results_process = list(executor.map(scrape_pair, pairs))
    # print(f"ProcessPoolExecutor Execution Time: {time.time() - start_time:.2f} seconds")
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"ProcessPoolExecutor Execution Time: {time.time() - start_time:.2f} seconds\n")

    # # ========= Joblib Parallel =========
    # start_time = time.time()
    # results_joblib = Parallel(n_jobs=-1)(delayed(scrape_kayak_flights)(origin, destination) for origin, destination in pairs)
    # print(f"Joblib Parallel Execution Time: {time.time() - start_time:.2f} seconds")
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"Joblib Parallel Execution Time: {time.time() - start_time:.2f} seconds\n")

    # # ========= Hybrid Execution (Process + Thread) =========
    # start_time = time.time()
    # # num_processes = 4
    # num_processes = 6
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"Number of threads: {num_processes}\n")
    # chunks = chunkify(pairs, num_processes)

    # with ProcessPoolExecutor(max_workers=num_processes) as process_executor:
    #     nested_results = list(process_executor.map(process_chunk, chunks))

    # # Flatten results
    # results_hybrid = [item for sublist in nested_results for item in sublist]
    # print(f"Hybrid Execution Time (Process + Thread): {time.time() - start_time:.2f} seconds")
    # with open(file_name, "a", encoding="utf-8") as f:
    #     f.write(f"Hybrid Execution Time (Process + Thread): {time.time() - start_time:.2f} seconds\n")


    # print("==================================")
    # print("=== Results ===")
    # print("==================================")
    # print(f"Sequential: ", results_seq)
    # print(f"ThreadPoolExecutor: ", results_thread)
    # print(f"ProcessPoolExecutor: ", results_process)   
    # print(f"Joblib Parallel: ", results_joblib)
    # print(f"Hybrid (Process + Thread): ", results_hybrid)

    # print("==================================")
    # print("=== Metrics ===")

    # calculate_metrics(results_seq, "Sequential", file_name)
    # calculate_metrics(results_thread, "ThreadPoolExecutor", file_name)
    # calculate_metrics(results_process, "ProcessPoolExecutor", file_name)
    # calculate_metrics(results_joblib, "Joblib Parallel", file_name)
    # calculate_metrics(results_hybrid, "Hybrid (Process + Thread)", file_name)
