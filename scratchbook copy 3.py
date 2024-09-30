import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import time
import threading
import csv
import logging
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
        self.running = True
        self.debug_mode = False

    def calculate_total_vehicle_count(self, active_lanes):
        return sum(self.lanes[lane] for lane in active_lanes)

    def calculate_time_per_vehicle(self, active_lanes, remaining_time):
        total_vehicles = self.calculate_total_vehicle_count(active_lanes)
        if total_vehicles == 0:
            return 0
        return remaining_time / total_vehicles

    def calculate_time_per_lane(self, lane, time_per_vehicle):
        return time_per_vehicle * self.lanes[lane]

    def get_active_lanes(self):
        return [lane for lane in self.lanes if lane not in self.omitted_lanes]

    def find_highest_priority_lane(self):
        active_lanes = self.get_active_lanes()
        if not active_lanes:
            return None
        sorted_lanes = sorted(active_lanes, key=lambda lane: self.lanes[lane], reverse=True)
        return sorted_lanes[0]

    def update_signals(self, remaining_time, prompt_vehicle_counts):
        green_lane = self.find_highest_priority_lane()
        if not green_lane:
            logging.info("No active lanes available for this cycle.")
            return 0

        active_lanes = self.get_active_lanes()
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, remaining_time)
        allocated_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        for remaining in range(int(allocated_time), 0, -1):
            if not self.running:
                return 0
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
        while remaining_time > 0 and len(self.omitted_lanes) < len(self.lanes) and self.running:
            allocated_time = self.update_signals(remaining_time, prompt_vehicle_counts)
            remaining_time -= allocated_time

    def start(self, prompt_vehicle_counts):
        while self.running:
            self.run_cycle(prompt_vehicle_counts)

    def start_blinking(self, lane):
        if not self.blinking_thread or not self.blinking_thread.is_alive():
            self.stop_blinking_event.clear()
            self.blinking_thread = threading.Thread(target=self.blink_yellow, args=(lane,))
            self.blinking_thread.start()

    def blink_yellow(self, lane):
        with self.blinking_lock:
            while not self.stop_blinking_event.is_set() and self.running:
                self.update_signal_callback(lane, "yellow")
                time.sleep(0.5)
                self.update_signal_callback(lane, "red")
                time.sleep(0.5)

    def stop(self):
        self.running = False
        if self.blinking_thread and self.blinking_thread.is_alive():
            self.stop_blinking_event.set()
            self.blinking_thread.join()

    def set_cycle_time(self, cycle_time):
        self.total_cycle_time = cycle_time

    def set_debug_mode(self, mode):
        self.debug_mode = mode
        if mode:
            logging.info("Debug mode enabled")
        else:
            logging.info("Debug mode disabled")

class TrafficSignalGUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.lanes = controller.lanes
        self.lane_frames = {}
        self.count_entries = {}
        self.progress_bars = {}
        self.memory_usage_label = None
        self.cpu_usage_label = None
        self.active_threads_label = None
        self.memory_usage_data = []
        self.cpu_usage_data = []
        self.is_running = False
        self.running = True

        self.setup_logging()
        self.create_widgets()
        self.create_developer_panel()

        self.figure, self.ax = plt.subplots(2, 1, figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=11, column=0, columnspan=4)

        self.start_memory_monitoring()
        self.start_cpu_monitoring()
        self.start_thread_monitoring()
        self.start_graph_updates()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_logging(self):
        logging.basicConfig(filename='traffic_signal.log', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler = logging.StreamHandler(self)
        self.log_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(self.log_handler)

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
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.cycle_time_label = tk.Label(self.root, text="Cycle Time (seconds):")
        self.cycle_time_label.grid(row=3, column=2)
        self.cycle_time_entry = tk.Entry(self.root)
        self.cycle_time_entry.insert(0, str(self.controller.total_cycle_time))
        self.cycle_time_entry.grid(row=3, column=3)
        self.cycle_time_button = tk.Button(self.root, text="Set Cycle Time", command=self.set_cycle_time)
        self.cycle_time_button.grid(row=4, column=2, columnspan=2, pady=5)

        self.memory_usage_label = tk.Label(self.root, text="Memory Usage: N/A", font=("Arial", 12))
        self.memory_usage_label.grid(row=8, column=0, columnspan=2)

        self.cpu_usage_label = tk.Label(self.root, text="CPU Usage: N/A", font=("Arial", 12))
        self.cpu_usage_label.grid(row=8, column=2, columnspan=2)

        self.active_threads_label = tk.Label(self.root, text="Active Threads: N/A", font=("Arial", 12))
        self.active_threads_label.grid(row=9, column=0, columnspan=4)

        self.log_display = scrolledtext.ScrolledText(self.root, height=10, width=80, font=("Consolas", 10))
        self.log_display.grid(row=10, column=0, columnspan=4, padx=5, pady=5)
        self.log_display.config(state=tk.DISABLED)

    def create_developer_panel(self):
        dev_frame = ttk.LabelFrame(self.root, text="Developer Controls")
        dev_frame.grid(row=10, column=0, columnspan=4, padx=5, pady=5, sticky="we")

        ttk.Button(dev_frame, text="Toggle Debug Mode", command=self.toggle_debug_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(dev_frame, text="Start", command=self.start_cycle).pack(side=tk.LEFT, padx=5)
        ttk.Button(dev_frame, text="Stop", command=self.stop_cycle).pack(side=tk.LEFT, padx=5)

    def submit_counts(self):
        vehicle_counts = {lane: int(entry.get()) for lane, entry in self.count_entries.items() if entry.get().isdigit()}
        self.controller.lanes = vehicle_counts
        self.update_progress_bars(vehicle_counts)
        self.log_display.insert(tk.END, f"Counts submitted: {vehicle_counts}\n")
        self.log_display.yview(tk.END)

    def update_progress_bars(self, vehicle_counts):
        for lane, count in vehicle_counts.items():
            self.progress_bars[lane]['value'] = count

    def toggle_debug_mode(self):
        self.controller.set_debug_mode(not self.controller.debug_mode)

    def start_cycle(self):
        if not self.is_running:
            self.is_running = True
            self.controller.start(self.prompt_vehicle_counts)

    def stop_cycle(self):
        if self.is_running:
            self.is_running = False
            self.controller.stop()

    def prompt_vehicle_counts(self):
        self.submit_counts()

    def start_memory_monitoring(self):
        self.memory_usage_data.clear()
        self.update_memory_usage()

    def update_memory_usage(self):
        mem = psutil.virtual_memory()
        memory_usage = f"{mem.percent}%"
        self.memory_usage_label.config(text=f"Memory Usage: {memory_usage}")
        self.memory_usage_data.append(mem.percent)
        self.root.after(1000, self.update_memory_usage)

    def start_cpu_monitoring(self):
        self.cpu_usage_data.clear()
        self.update_cpu_usage()

    def update_cpu_usage(self):
        cpu_usage = f"{psutil.cpu_percent()}%"
        self.cpu_usage_label.config(text=f"CPU Usage: {cpu_usage}")
        self.cpu_usage_data.append(psutil.cpu_percent())
        self.root.after(1000, self.update_cpu_usage)

    def start_thread_monitoring(self):
        self.update_active_threads()

    def update_active_threads(self):
        self.active_threads_label.config(text=f"Active Threads: {threading.active_count()}")
        self.root.after(1000, self.update_active_threads)

    def start_graph_updates(self):
        self.update_graph()

    def update_graph(self):
        self.ax[0].clear()
        self.ax[1].clear()

        self.ax[0].plot(self.memory_usage_data, label='Memory Usage (%)')
        self.ax[0].set_title('Memory Usage Over Time')
        self.ax[0].set_ylabel('Usage (%)')
        self.ax[0].legend()

        self.ax[1].plot(self.cpu_usage_data, label='CPU Usage (%)')
        self.ax[1].set_title('CPU Usage Over Time')
        self.ax[1].set_ylabel('Usage (%)')
        self.ax[1].legend()

        self.canvas.draw()
        self.root.after(1000, self.update_graph)

    def on_closing(self):
        self.stop_cycle()
        self.root.destroy()

def main():
    lanes = {'North': 0, 'South': 0, 'East': 0, 'West': 0}
    root = tk.Tk()
    root.title("Traffic Signal Control System")
    controller = TrafficSignalController(lanes, update_signal_callback=lambda lane, color, remaining: print(f"{lane} is now {color} with {remaining} seconds left."),
                                          update_progress_callback=lambda lane, remaining, total: print(f"{lane} progress: {remaining}/{total}"))
    gui = TrafficSignalGUI(root, controller)
    root.mainloop()

if __name__ == "__main__":
    main()
