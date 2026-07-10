import os
import subprocess
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
SERVER_EXE = "server.exe"
CLIENT_EXE = "client.exe"
TEST_FILE = "input2.txt"
CSV_RESULTS_FILE = "results.csv"

# Test parameters
PROTOCOLS = {
    "Stop-and-Wait": 1,
    "Go-Back-N": 2,
    "Selective Repeat": 3
}
WINDOW_SIZES = [5]  # Test with N=8 for GBN and SR
ERROR_PROBS = [0.0, 0.05, 0.1, 0.15, 0.2]

# --- Main Script ---
def create_test_file(size_kb=50):
    """Creates a dummy file for transmission."""
    if not os.path.exists(TEST_FILE):
        print(f"Creating a {size_kb}KB test file: {TEST_FILE}")
        with open(TEST_FILE, "w") as f:
            f.write("A" * (size_kb * 1024))

def run_analysis():
    """Automates the testing and generates results."""
    
    # 1. Create a dummy file for testing
    create_test_file()

    # 2. Run all test cases
    with open(CSV_RESULTS_FILE, "w") as f:
        # Write CSV header
        f.write("Protocol,WindowSize,ErrorProbability,TotalTime_ms,TotalFramesSent,Throughput_Kbps,Efficiency\n")

        for name, number in PROTOCOLS.items():
            # For Stop-and-Wait, window size is always 1 and we only need to test it once per error rate
            current_window_sizes = WINDOW_SIZES if name != "Stop-and-Wait" else [1]
            
            for n in current_window_sizes:
                for prob in ERROR_PROBS:
                    print(f"Testing: {name} (N={n}), Error Rate={prob*100}%")

                    # Start the server in the background
                    server_proc = subprocess.Popen([f"./{SERVER_EXE}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1) # Give server time to start up

                    # Prepare input for the client
                    client_input = f"{number}\n{n}\n{prob}\n"
                    
                    try:
                        # Run the client and capture its output
                        client_proc = subprocess.run(
                            [f"./{CLIENT_EXE}", TEST_FILE, "--csv"],
                            input=client_input,
                            capture_output=True,
                            text=True,
                            timeout=60 # 60-second timeout for each run
                        )
                        
                        # Write the result to the CSV file
                        if client_proc.returncode == 0 and client_proc.stdout:
                            f.write(client_proc.stdout)
                        else:
                            print(f"  -> Run failed or produced no output. Error: {client_proc.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        print("  -> Run timed out.")
                    finally:
                        # Ensure server is terminated
                        server_proc.terminate()
                        server_proc.wait()

    print(f"\nAnalysis complete. Data saved to {CSV_RESULTS_FILE}")

    # 3. Generate graphs from the CSV data
    generate_graphs()

def generate_graphs():
    """Reads the CSV file and creates plots using pandas and matplotlib."""
    if not os.path.exists(CSV_RESULTS_FILE):
        print(f"Error: {CSV_RESULTS_FILE} not found. Run the analysis first.")
        return

    df = pd.read_csv(CSV_RESULTS_FILE)
    
    # Use a nice style for the plots
    sns.set_theme(style="whitegrid")

    # --- Plot 1: Throughput vs. Error Rate ---
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x="ErrorProbability", y="Throughput_Kbps", hue="Protocol", style="Protocol", markers=True, dashes=False)
    plt.title('Throughput vs. Channel Error Rate', fontsize=16)
    plt.xlabel('Error Probability')
    plt.ylabel('Throughput (Kbps)')
    plt.grid(True)
    plt.legend(title='Protocol')
    plt.tight_layout()
    plt.savefig('throughput_vs_error1.png')
    print("Generated throughput_vs_error.png")

    # --- Plot 2: Efficiency vs. Error Rate ---
    plt.figure(figsize=(10, 6))
    df['EfficiencyPercentage'] = df['Efficiency'] * 100
    sns.lineplot(data=df, x="ErrorProbability", y="EfficiencyPercentage", hue="Protocol", style="Protocol", markers=True, dashes=False)
    plt.title('Protocol Efficiency vs. Channel Error Rate', fontsize=16)
    plt.xlabel('Error Probability')
    plt.ylabel('Efficiency (%)')
    plt.grid(True)
    plt.legend(title='Protocol')
    plt.tight_layout()
    plt.savefig('efficiency_vs_error1.png')
    print("Generated efficiency_vs_error.png")

if __name__ == "__main__":
    run_analysis()