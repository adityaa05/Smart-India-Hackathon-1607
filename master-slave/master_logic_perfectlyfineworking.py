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
import socket
import json

class MasterServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.clients = []
        self.vehicle_counts = {}

    def start(self):
        self.sock.listen(5)
        print(f"Master server listening on {self.host}:{self.port}")
        while True:
            client, address = self.sock.accept()
            print(f"New connection from {address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client,))
            client_thread.start()

    def handle_client(self, client):
        self.clients.append(client)
        while True:
            try:
                data = client.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.update_vehicle_count(message)
            except Exception as e:
                print(f"Error handling client: {e}")
                break
        client.close()
        self.clients.remove(client)

    def update_vehicle_count(self, message):
        lane = message['lane']
        count = message['count']
        self.vehicle_counts[lane] = count
        print(f"Updated vehicle count for {lane}: {count}")

    def get_vehicle_counts(self):
        return self.vehicle_counts

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
        with open('historical_data1.csv', 'a', newline='') as csvfile:
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

    def update_vehicle_counts(self, new_counts):
        self.lanes.update(new_counts)

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

        # Initialize MasterServer
        self.master_server = MasterServer()
        self.server_thread = threading.Thread(target=self.master_server.start)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Start updating vehicle counts from the server
        self.update_counts_thread = threading.Thread(target=self.update_vehicle_counts_from_server)
        self.update_counts_thread.daemon = True
        self.update_counts_thread.start()

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
        self.memory_usage_label.grid(row=6, column=0, columnspan=2)

        self.cpu_usage_label = tk.Label(self.root, text="CPU Usage: N/A", font=("Arial", 12))
        self.cpu_usage_label.grid(row=6, column=2, columnspan=2)

        self.active_threads_label = tk.Label(self.root, text="Active Threads: N/A", font=("Arial", 12))
        self.active_threads_label.grid(row=7, column=0, columnspan=4)

        self.log_display = scrolledtext.ScrolledText(self.root, height=10, width=80, font=("Consolas", 10))
        self.log_display.grid(row=9, column=0, columnspan=4, padx=5, pady=5)
        self.log_display.config(state=tk.DISABLED)

    def create_developer_panel(self):
        dev_frame = ttk.LabelFrame(self.root, text="Developer Controls")
        dev_frame.grid(row=10, column=0, columnspan=4, padx=5, pady=5, sticky="we")

        ttk.Button(dev_frame, text="Toggle Debug Mode", command=self.toggle_debug_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(dev_frame, text="Export Logs", command=self.export_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(dev_frame, text="Simulate Traffic Spike", command=self.simulate_traffic_spike).pack(side=tk.LEFT, padx=5)
        ttk.Button(dev_frame, text="Clear Historical Data", command=self.clear_historical_data).pack(side=tk.LEFT, padx=5)

    def toggle_debug_mode(self):
        self.controller.set_debug_mode(not self.controller.debug_mode)
        self.display_message(f"Debug mode {'enabled' if self.controller.debug_mode else 'disabled'}")

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".log")
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.log_display.get("1.0", tk.END))
            self.display_message(f"Logs exported to {file_path}")
            
    def simulate_traffic_spike(self):
        for lane in self.lanes:
            # Simulate traffic spike using a factor based on CPU usage
            spike = int(psutil.cpu_percent() * 2)  # Scaled up by a factor of 2
            self.lanes[lane] += spike  # Increase vehicle count by the spike amount
            self.display_message(f"Traffic spike on {lane}: +{spike} vehicles")

        # After updating the lane counts, refresh the entry fields and submit
        self.update_entry_fields()
        self.submit_counts()

    def update_entry_fields(self):
        for lane in self.lanes:
            self.count_entries[lane].delete(0, tk.END)
            self.count_entries[lane].insert(0, str(self.lanes[lane]))

    def clear_historical_data(self):
        self.controller.historical_data.clear()
        open('historical_data1.csv', 'w').close()  # Clear the CSV file
        self.display_message("Historical data cleared")

    def write(self, message):
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, message)
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)

    def prompt_vehicle_counts(self):
        self.display_message("Enter new vehicle counts and click Submit")

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

    def set_cycle_time(self):
        try:
            cycle_time = int(self.cycle_time_entry.get())
            if cycle_time > 0:
                self.controller.set_cycle_time(cycle_time)
                self.display_message(f"Cycle time set to {cycle_time} seconds")
            else:
                self.display_message("Cycle time must be a positive integer")
        except ValueError:
            self.display_message("Invalid cycle time. Please enter a positive integer.")

    def update_signal(self, lane, color, remaining=None):
        if self.root.winfo_exists():
            if remaining is not None:
                self.lane_frames[lane].config(bg=color, text=f"{color.capitalize()} ({remaining}s)")
            else:
                self.lane_frames[lane].config(bg=color, text=color.capitalize())

    def update_progress(self, lane, remaining, allocated_time):
        if self.root.winfo_exists():
            progress_value = (allocated_time - remaining) / allocated_time * 100
            self.progress_bars[lane]['value'] = progress_value


    def display_message(self, message):
        logging.info(message)

    def start_traffic_signal(self):
        self.traffic_thread = threading.Thread(target=self.controller.start, args=(self.prompt_vehicle_counts,))
        self.traffic_thread.daemon = True
        self.traffic_thread.start()

    def start_memory_monitoring(self):
        self.memory_thread = threading.Thread(target=self.monitor_memory_usage)
        self.memory_thread.daemon = True
        self.memory_thread.start()


    def monitor_memory_usage(self):
        while self.running:
            memory_usage = psutil.virtual_memory().percent
            self.memory_usage_data.append(memory_usage)
            self.root.after(1000, self.update_memory_label, memory_usage)
            time.sleep(1)

    def update_memory_label(self, memory_usage):
        if self.root.winfo_exists():
            self.memory_usage_label.config(text=f"Memory Usage: {memory_usage:.1f}%")

    def start_cpu_monitoring(self):
        self.cpu_thread = threading.Thread(target=self.monitor_cpu_usage)
        self.cpu_thread.daemon = True
        self.cpu_thread.start()

    def monitor_cpu_usage(self):
        while self.running:
            cpu_usage = psutil.cpu_percent(interval=1)
            self.cpu_usage_data.append(cpu_usage)
            self.root.after(1000, self.update_cpu_label, cpu_usage)
            time.sleep(1)

    def update_cpu_label(self, cpu_usage):
        if self.root.winfo_exists():
            self.cpu_usage_label.config(text=f"CPU Usage: {cpu_usage:.1f}%")

    def start_thread_monitoring(self):
        self.thread_monitor = threading.Thread(target=self.monitor_threads)
        self.thread_monitor.daemon = True
        self.thread_monitor.start()


    def monitor_threads(self):
        while self.running:
            active_threads = threading.active_count()
            self.root.after(1000, self.update_thread_label, active_threads)
            time.sleep(1)


    def update_thread_label(self, active_threads):
        if self.root.winfo_exists():
            self.active_threads_label.config(text=f"Active Threads: {active_threads}")

    def start_graph_updates(self):
        self.update_graph()

    def update_graph(self):
        if self.running and self.root.winfo_exists():
            self.ax[0].clear()
            self.ax[0].plot(self.memory_usage_data[-60:], label='Memory Usage', color='blue')
            self.ax[0].set_title('Memory and CPU Usage Over Time')
            self.ax[0].set_xlabel('Time (seconds)')
            self.ax[0].set_ylabel('Usage (%)')
            self.ax[0].legend()

            self.ax[1].clear()
            self.ax[1].plot(self.cpu_usage_data[-60:], label='CPU Usage', color='red')
            
            self.ax[1].set_xlabel('Time (seconds)')
            self.ax[1].set_ylabel('Usage (%)')
            self.ax[1].legend()

            self.canvas.draw()
            self.root.after(1000, self.update_graph)

    def update_vehicle_counts_from_server(self):
        while self.running:
            new_counts = self.master_server.get_vehicle_counts()
            self.controller.update_vehicle_counts(new_counts)
            self.update_entry_fields()
            time.sleep(1)  # Update every second

    def on_closing(self):
        self.running = False
        self.controller.stop()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    lanes = {
        "North": 0,
        "South": 0,
        "East": 0,
        "West": 0
    }
    root = tk.Tk()
    root.title("Traffic Signal Controller - Master System")
    controller = TrafficSignalController(lanes, lambda *args: None, lambda *args: None)
    gui = TrafficSignalGUI(root, controller)
    controller.update_signal_callback = gui.update_signal
    controller.update_progress_callback = gui.update_progress
    root.mainloop()