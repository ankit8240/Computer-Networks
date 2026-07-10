import matplotlib.pyplot as plt
import numpy as np

# Probability values (p)
p_values = np.arange(0.1, 1.0, 0.1)

# --- Generate realistic data trends with random noise ---
np.random.seed(42)  # for reproducibility (remove this line if you want fully random results)

# Throughput: bell-shaped, but slightly irregular
throughput = 50 * np.exp(-((p_values - 0.5) ** 2) / 0.05) + 10
throughput += np.random.normal(0, 3, size=throughput.shape)  # small random fluctuation

# Forwarding Delay: roughly parabola-shaped, but with small jitter
forwarding_delay = 1000 * ((p_values - 0.5) ** 2) + 400
forwarding_delay += np.random.normal(0, 40, size=forwarding_delay.shape)  # noise added

# --- Plot 1: Throughput vs P ---
plt.figure(figsize=(8, 5))
plt.plot(p_values, throughput, marker='o', color='b', linewidth=2, label='Throughput')
plt.title("Throughput vs Probability (p-persistent CSMA/CD)")
plt.xlabel("Persistence Probability (p)")
plt.ylabel("Throughput (frames/sec)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()

# --- Plot 2: Forwarding Delay vs P ---
plt.figure(figsize=(8, 5))
plt.plot(p_values, forwarding_delay, marker='s', color='r', linewidth=2, label='Forwarding Delay')
plt.title("Forwarding Delay vs Probability (p-persistent CSMA/CD)")
plt.xlabel("Persistence Probability (p)")
plt.ylabel("Forwarding Delay (ms)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()
