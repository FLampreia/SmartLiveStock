import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def create_names(model_path, scan_type):
    """Create names for the timestamp files."""

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    model_name = os.path.splitext(os.path.basename(model_path))[0]

    return timestamp, model_name, scan_type

def save_logs(log_data, model_type, scan_type):
    """Save logs in a CSV, returns filename and DataFrame."""

    model_name, timestamp, scan_type = create_names(model_type, scan_type)
    log_filename = f"../logs/log_{scan_type}_{model_name}_{timestamp}.csv"
    df = pd.DataFrame(log_data)
    df.to_csv(log_filename, index=False)

    return df, log_filename, model_name, timestamp

def save_ids(unique_ids, model_type, scan_type, timestamp, model_name):
    """Save IDs in a CSV, returns filename."""

    ids_filename = f"../ids/ids_{scan_type}_{model_name}_{timestamp}.csv"
    ids_df = pd.DataFrame(list(unique_ids.items()), columns=["sheep_id", "frame"])
    ids_df.to_csv(ids_filename, index=False)

    return ids_filename

def save_plot(df, model_name, scan_type, timestamp):
    """Save graph, FPS and sheep counting."""
    plt.figure(figsize=(12,6))
    plt.plot(df["time"], df["sheep_count"], label="Sheep Count (Accumulated)")
    plt.plot(df["time"], df["sheep_visible"], label="Visible Sheep per Frame")
    plt.plot(df["time"], df["fps"], label="FPS")
    plt.xlabel("Time (s)")
    plt.ylabel("Value")
    plt.legend()
    plt.title(f"Counting and performance evolution ({model_name})")

    plot_filename = f"../plots/plot_{scan_type}_{model_name}_{timestamp}.png"
    plt.savefig(plot_filename)
    plt.show()
    return plot_filename

def resume(df, frame_count, sheep_count,
           log_filename, ids_filename, plot_filename):
    """Show final resume on the terminal."""
    print("\nFiles:")
    print(f"Log saved in: {log_filename}")
    print(f"IDs saved in: {ids_filename}")
    print(f"Graph saved in: {plot_filename}")

    print("\nResume:")
    print(f"Total processed frames: {frame_count}")
    print(f"Number of sheep: {sheep_count}")
    print(f"Average FPS: {df['fps'].mean():.2f}")