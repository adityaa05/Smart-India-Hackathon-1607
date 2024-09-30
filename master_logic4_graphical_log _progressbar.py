import tkinter as tk
from tkinter import ttk
import time
import threading

class TrafficSignalController:
    def __init__(self, lanes, total_cycle_time=120):
        self.lanes = lanes
        self.total_cycle_time = total_cycle_time
        self.last_green_lane = None
        self.omitted_lanes = []

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

    def update_signals(self, remaining_time, signal_callback, countdown_callback, prompt_vehicle_counts):
        green_lane = self.find_highest_priority_lane()

        if not green_lane:
            print("No active lanes available for this cycle.")
            return 0

        active_lanes = self.get_active_lanes()
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, remaining_time)
        allocated_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        # Countdown for the green signal
        for remaining in range(int(allocated_time), 0, -1):
            countdown_callback(green_lane, remaining, allocated_time)
            if remaining <= 5:  # Last 5 seconds will turn yellow
                signal_callback(green_lane, "yellow", remaining)
            else:
                signal_callback(green_lane, "green", remaining)

            time.sleep(1)

        # After the loop, turn the signal red (not needed explicitly)
        signal_callback(green_lane, "red")

        # Prompt for vehicle counts after yellow signal ends
        prompt_vehicle_counts()

        self.last_green_lane = green_lane
        self.omitted_lanes.append(green_lane)

        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]

        return allocated_time

    def run_cycle(self, signal_callback, countdown_callback, prompt_vehicle_counts):
        remaining_time = self.total_cycle_time

        while remaining_time > 0 and len(self.omitted_lanes) < len(self.lanes):
            allocated_time = self.update_signals(remaining_time, signal_callback, countdown_callback, prompt_vehicle_counts)
            remaining_time -= allocated_time

    def start(self, signal_callback, countdown_callback, prompt_vehicle_counts):
        while True:
            self.run_cycle(signal_callback, countdown_callback, prompt_vehicle_counts)

class TrafficSignalGUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.lanes = controller.lanes
        self.lane_frames = {}
        self.count_entries = {}
        self.progress_bars = {}
        self.create_widgets()
        self.is_running = False

    def create_widgets(self):
        for idx, lane in enumerate(self.lanes):
            frame = tk.Frame(self.root, borderwidth=2, relief="groove")
            frame.grid(row=0, column=idx, padx=5, pady=5)
            label = tk.Label(frame, text=lane, font=("Arial", 16))
            label.pack()
            signal_label = tk.Label(frame, text="Red", bg="red", width=10, height=2, font=("Arial", 16))
            signal_label.pack()
            self.lane_frames[lane] = signal_label

            # Create a progress bar for each lane
            progress = ttk.Progressbar(frame, orient="horizontal", length=100, mode='determinate')
            progress.pack(pady=5)
            self.progress_bars[lane] = progress

            label = tk.Label(self.root, text=f"{lane} count:")
            label.grid(row=1, column=idx)
            entry = tk.Entry(self.root)
            entry.grid(row=2, column=idx)
            self.count_entries[lane] = entry

        self.submit_button = tk.Button(self.root, text="Submit Counts", command=self.submit_counts)
        self.submit_button.grid(row=3, column=0, columnspan=4)

    def prompt_vehicle_counts(self):
        self.display_message("Please enter vehicle counts and click Submit")

    def submit_counts(self):
        for lane in self.lanes:
            try:
                count = int(self.count_entries[lane].get())
                self.lanes[lane] = count
            except ValueError:
                self.lanes[lane] = 0

        self.display_message("Vehicle counts submitted")

        if not self.is_running:  # Start the cycle only after first input
            self.is_running = True
            self.start_traffic_signal()

    def update_signal(self, lane, color, remaining=None):
        """Update the traffic signal color for a given lane."""
        if remaining is not None:
            self.lane_frames[lane].config(bg=color, text=f"{color.capitalize()} ({remaining}s)")
        else:
            self.lane_frames[lane].config(bg=color, text=color.capitalize())

    def update_progress(self, lane, remaining, allocated_time):
        """Update the progress bar for the given lane."""
        progress_value = (allocated_time - remaining) / allocated_time * 100
        self.progress_bars[lane].config(value=progress_value)

    def display_message(self, message):
        """Display a message to the user."""
        print(message)

    def start_traffic_signal(self):
        """Start the traffic signal cycle in a separate thread."""
        def run_signal():
            self.controller.start(self.update_signal, self.update_progress, self.prompt_vehicle_counts)

        signal_thread = threading.Thread(target=run_signal, daemon=True)
        signal_thread.start()

def run_gui():
    root = tk.Tk()
    root.title("Traffic Signal Controller")
    
    # Alternative for maximizing window on Linux/Wayland
    root.attributes('-zoomed', True)  # Start in maximized mode

    lanes = {"North": 0, "East": 0, "South": 0, "West": 0}
    controller = TrafficSignalController(lanes)

    gui = TrafficSignalGUI(root, controller)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
