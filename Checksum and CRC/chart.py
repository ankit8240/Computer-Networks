import matplotlib.pyplot as plt
import numpy as np

# Data
methods = ["Checksum", "CRC-8", "CRC-10", "CRC-16", "CRC-32"]
error_types = ["Single", "Multiple", "Burst", "Swap"]

# Success rates for each method (rows) and error type (columns)
values = [
    [100, 97.07, 100, 72.65],   # Checksum
    [100, 100, 100, 76.95],     # CRC-8
    [100, 100, 100, 74.60],     # CRC-10
    [100, 100, 100, 70.70],     # CRC-16
    [100, 100, 100, 76.56],     # CRC-32
]

values = np.array(values)

# Bar chart setup
x = np.arange(len(methods))
bar_width = 0.2
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]  # one color per error type

plt.figure(figsize=(12, 6))

for i, err in enumerate(error_types):
    plt.bar(x + i * bar_width, values[:, i], width=bar_width, label=err, color=colors[i])

# Labels and formatting
plt.xticks(x + bar_width * (len(error_types)-1) / 2, methods)
plt.ylabel("Success Rate (%)")
plt.title("Error Detection Performance by Method and Error Type")
plt.legend(title="Error Type")
plt.ylim(60, 105)
plt.grid(axis="y", linestyle="--", alpha=0.6)

plt.show()
