"""Visualization utilities for commit matrices."""


def plot_matrix(matrix: list[list[int]]) -> None:
    """Plots the commit matrix as a heatmap using matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib and numpy are required for plotting. Install with: pip install matplotlib numpy")
        return
    
    # Convert to numpy array for easier plotting
    data = np.array(matrix)
    
    plt.figure(figsize=(12, 2))
    plt.imshow(data, cmap='Greens', aspect='auto')
    plt.colorbar(label='Commits')
    plt.title('Commit Activity Heatmap')
    plt.xlabel('Week of Year')
    plt.ylabel('Day of Week')
    plt.yticks(range(7), ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"])
    plt.xticks(range(0, 52, 4), range(1, 53, 4))  # Show every 4th week
    plt.show()
