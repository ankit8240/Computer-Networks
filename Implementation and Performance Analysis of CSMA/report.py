import subprocess
import time
import re
import matplotlib.pyplot as plt

# --- Define persistence probabilities to test ---
p_values = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]

NUM_STATIONS = 4
station_throughputs = {i: [] for i in range(1, NUM_STATIONS + 1)}
avg_throughputs = []

# Regex to extract successful frames per station
success_pattern = re.compile(r"\[Station (\d+)\]\s+Finished\. Successful frames: (\d+)/(\d+)")

def run_simulation(p_value):
    """Runs server and multi-station client, returns throughput per station."""
    # Start server
    server = subprocess.Popen(
        ["python", "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(1.5)  # give server time to start

    # Start client with p value
    client = subprocess.Popen(
        ["python", "multi_client.py", str(p_value)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Capture client output
    client_out, client_err = client.communicate()

    # Stop server
    server.terminate()
    server_out, server_err = server.communicate()

    # Extract successful frames per station
    throughput_per_station = {}
    for match in success_pattern.finditer(client_out):
        station_id = int(match.group(1))
        successful_frames = int(match.group(2))
        total_frames = int(match.group(3))
        throughput = successful_frames / total_frames  # fraction
        throughput_per_station[station_id] = throughput
        print(f"p={p_value} → Station {station_id}: {successful_frames}/{total_frames} frames → Throughput={throughput:.2f}")

    # Fill missing stations with 0 if not found
    for sid in range(1, NUM_STATIONS + 1):
        if sid not in throughput_per_station:
            throughput_per_station[sid] = 0.0

    # Average throughput across all stations
    avg_throughput = sum(throughput_per_station.values()) / NUM_STATIONS
    print(f"p={p_value} → Average throughput across stations: {avg_throughput:.2f}\n")
    
    return throughput_per_station, avg_throughput

# --- Main loop over p values ---
for p in p_values:
    per_station, avg = run_simulation(p)
    avg_throughputs.append(avg)
    for sid, thr in per_station.items():
        station_throughputs[sid].append(thr)
    print("-" * 40)

# --- Plot throughput per station ---
plt.figure(figsize=(10, 6))
for sid in range(1, NUM_STATIONS + 1):
    plt.plot(p_values, station_throughputs[sid], marker='o', label=f"Station {sid}")

plt.plot(p_values, avg_throughputs, 'k--', marker='x', label="Average Throughput")
plt.title("Throughput vs Persistence Probability (p) per Station")
plt.xlabel("Persistence Probability (p)")
plt.ylabel("Throughput (fraction of frames successful)")
plt.grid(True)
plt.legend()
plt.savefig("throughput_vs_p_multi_station.png")
plt.show()

print("Graph generated and saved as 'throughput_vs_p_multi_station.png'")
