import tkinter as tk
from tkinter import ttk
import time
import threading
import csv
from datetime import datetime
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TrafficSignalController:
    def __init__(self, lanes, update_signal_callback, update_progress_callback, total_cycle_time=120):
        self.lanes = lanes
        self.update_signal_callback = update_signal_callback
        self.update_progress_callback = update_progress_callback
        self.total_cycle_time = total_cycle_time
        self.last_green_lane = None
        self.omitted_lanes = []
        self.blinking_thread = None
        self.stop_blinking_event = threading.Event()
        self.blinking_lock = threading.Lock()
        self.historical_data = []

    def calculate_total_vehicle_count(self, active_lanes):
        return sum(self.lanes[lane] for lane in active_lanes)

    def calculate_time_per_vehicle(self, active_lanes, remaining_time):
        total_vehicles = self.calculate_total_vehicle_count(active_lanes)
        return remaining_time / total_vehicles if total_vehicles > 0 else 0

    def calculate_time_per_lane(self, lane, time_per_vehicle):
        return time_per_vehicle * self.lanes[lane]

    def get_active_lanes(self):
        return [lane for lane in self.lanes if lane not in self.omitted_lanes]

    def find_highest_priority_lane(self):
        active_lanes = self.get_active_lanes()
        if not active_lanes:
            return None
        return sorted(active_lanes, key=lambda lane: self.lanes[lane], reverse=True)[0]

    def update_signals(self, remaining_time, prompt_vehicle_counts):
        green_lane = self.find_highest_priority_lane()
        if not green_lane:
            print("No active lanes available for this cycle.")
            return 0

        active_lanes = self.get_active_lanes()
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, remaining_time)
        allocated_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        for remaining in range(int(allocated_time), 0, -1):
            self.update_signal_callback(green_lane, "green", remaining)
            self.update_progress_callback(green_lane, remaining, allocated_time)
            if remaining <= 5:
                self.start_blinking(green_lane)
            time.sleep(1)

        self.stop_blinking_event.set()
        self.update_signal_callback(green_lane, "red")

        self.log_historical_data(green_lane, allocated_time)
        prompt_vehicle_counts()

        self.last_green_lane = green_lane
        self.omitted_lanes.append(green_lane)

        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]

        return allocated_time

    def log_historical_data(self, lane, time_allocated):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.historical_data.append((lane, time_allocated, timestamp))
        with open('historical_data.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([lane, time_allocated, timestamp])

    def run_cycle(self, prompt_vehicle_counts):
        remaining_time = self.total_cycle_time
        while remaining_time > 0 and len(self.omitted_lanes) < len(self.lanes):
            allocated_time = self.update_signals(remaining_time, prompt_vehicle_counts)
            remaining_time -= allocated_time

    def start(self, prompt_vehicle_counts):
        while True:
            self.run_cycle(prompt_vehicle_counts)

    def start_blinking(self, lane):
        if not self.blinking_thread or not self.blinking_thread.is_alive():
            self.stop_blinking_event.clear()
            self.blinking_thread = threading.Thread(target=self.blink_yellow, args=(lane,))
            self.blinking_thread.start()

    def blink_yellow(self, lane):
        with self.blinking_lock:
            while not self.stop_blinking_event.is_set():
                self.update_signal_callback(lane, "yellow")
                time.sleep(0.5)
                self.update_signal_callback(lane, "red")
                time.sleep(0.5)

class TrafficSignalGUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.lanes = controller.lanes
        self.lane_frames = {}
        self.count_entries = {}
        self.progress_bars = {}
        self.is_running = False
        self.stop_event = threading.Event()

        self.create_widgets()

        self.historical_display = tk.Text(self.root, height=10, width=80, font=("Arial", 12))
        self.historical_display.grid(row=4, column=0, columnspan=4)
        self.historical_display.config(state=tk.DISABLED)
        self.load_historical_data()

        self.figure, self.ax = plt.subplots(2, 1, figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=8, column=0, columnspan=4)

        self.memory_thread = threading.Thread(target=self.memory_monitoring, daemon=True)
        self.cpu_thread = threading.Thread(target=self.cpu_monitoring, daemon=True)
        self.memory_thread.start()
        self.cpu_thread.start()

        self.start_graph_updates()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        for idx, lane in enumerate(self.lanes):
            frame = tk.Frame(self.root, borderwidth=2, relief="groove")
            frame.grid(row=0, column=idx, padx=5, pady=5)
            label = tk.Label(frame, text=lane, font=("Arial", 16))
            label.pack()
            signal_label = tk.Label(frame, text="Red", bg="red", width=10, height=2, font=("Arial", 16))
            signal_label.pack()
            self.lane_frames[lane] = signal_label

            progress = ttk.Progressbar(frame, orient="horizontal", length=100, mode='determinate')
            progress.pack(pady=5)
            self.progress_bars[lane] = progress

            label = tk.Label(self.root, text=f"{lane} count:")
            label.grid(row=1, column=idx)
            entry = tk.Entry(self.root)
            entry.grid(row=2, column=idx)
            self.count_entries[lane] = entry

        self.submit_button = tk.Button(self.root, text="Submit Counts", command=self.submit_counts)
        self.submit_button.grid(row=3, column=0, columnspan=4, pady=10)

        self.memory_usage_label = tk.Label(self.root, text="Memory Usage: N/A", font=("Arial", 12))
        self.memory_usage_label.grid(row=5, column=0, columnspan=4)

        self.cpu_usage_label = tk.Label(self.root, text="CPU Usage: N/A", font=("Arial", 12))
        self.cpu_usage_label.grid(row=6, column=0, columnspan=4)

        self.active_threads_label = tk.Label(self.root, text="Active Threads: N/A", font=("Arial", 12))
        self.active_threads_label.grid(row=7, column=0, columnspan=4)

    def prompt_vehicle_counts(self):
        self.display_message("Testing phase")

    def submit_counts(self):
        for lane in self.lanes:
            try:
                count = int(self.count_entries[lane].get())
                self.lanes[lane] = count
            except ValueError:
                self.lanes[lane] = 0

        self.display_message("Vehicle counts submitted")

        if not self.is_running:
            self.is_running = True
            self.start_traffic_signal()

    def update_signal(self, lane, color, remaining=None):
        if remaining is not None:
            self.lane_frames[lane].config(bg=color, text=f"{color.capitalize()} ({remaining}s)")
        else:
            self.lane_frames[lane].config(bg=color, text=color.capitalize())

    def update_progress(self, lane, remaining, allocated_time):
        progress_value = (allocated_time - remaining) / allocated_time * 100
        self.progress_bars[lane]['value'] = progress_value

    def display_message(self, message):
        self.historical_display.config(state=tk.NORMAL)
        self.historical_display.insert(tk.END, f"{message}\n")
        self.historical_display.config(state=tk.DISABLED)

    def load_historical_data(self):
        try:
            with open('historical_data.csv', 'r') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    lane, time_allocated, timestamp = row
                    self.historical_display.config(state=tk.NORMAL)
                    self.historical_display.insert(tk.END, f"{timestamp} - Lane: {lane}, Time Allocated: {time_allocated}\n")
                self.historical_display.config(state=tk.DISABLED)
        except FileNotFoundError:
            self.display_message("Historical data file not found.")

    def memory_monitoring(self):
        while not self.stop_event.is_set():
            memory = psutil.virtual_memory()
            self.root.after(0, lambda: self.memory_usage_label.config(text=f"Memory Usage: {memory.percent}%"))
            time.sleep(1)

    def cpu_monitoring(self):
        while not self.stop_event.is_set():
            cpu_usage = psutil.cpu_percent(interval=1)
            self.root.after(0, lambda: self.cpu_usage_label.config(text=f"CPU Usage: {cpu_usage}%"))
            self.root.after(0, lambda: self.active_threads_label.config(text=f"Active Threads: {threading.active_count()}"))
            time.sleep(1)

    def start_traffic_signal(self):
        threading.Thread(target=self.controller.start, args=(self.prompt_vehicle_counts,), daemon=True).start()

    def start_graph_updates(self):
        if not self.stop_event.is_set():
            self.update_graph()
            self.root.after(1000, self.start_graph_updates)

    def update_graph(self):
        self.ax[0].clear()
        self.ax[0].set_title("Historical Lane Usage")
        self.ax[0].set_xlabel("Timestamp")
        self.ax[0].set_ylabel("Time Allocated")
        if self.controller.historical_data:
            timestamps = [data[2] for data in self.controller.historical_data]
            times_allocated = [data[1] for data in self.controller.historical_data]
            self.ax[0].bar(timestamps, times_allocated)
        
        self.ax[1].clear()
        self.ax[1].set_title("Memory and CPU Usage")
        self.ax[1].set_xlabel("Time (seconds)")
        self.ax[1].set_ylabel("Usage (%)")

        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        
        self.ax[1].bar(["Memory Usage", "CPU Usage"], [memory_usage, cpu_usage])

        self.canvas.draw()

    def on_closing(self):
        self.stop_event.set()
        self.root.quit()
        self.root.destroy()

def main():
    lanes = {"North": 0, "South": 0, "East": 0, "West": 0}
    root = tk.Tk()
    root.title("Traffic Signal Control System")
    controller = TrafficSignalController(lanes, update_signal_callback=lambda lane, color, remaining=None: gui.update_signal(lane, color, remaining), 
                                          update_progress_callback=lambda lane, remaining, allocated_time: gui.update_progress(lane, remaining, allocated_time))
    gui = TrafficSignalGUI(root, controller)
    root.mainloop()

if __name__ == "__main__":
    main()