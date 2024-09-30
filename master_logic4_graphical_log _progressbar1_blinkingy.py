import tkinter as tk
from tkinter import ttk
import time
import threading

class TrafficSignalController:
    def __init__(self, lanes, update_signal_callback, total_cycle_time=120):
        self.lanes = lanes
        self.update_signal_callback = update_signal_callback  # Store the callback
        self.total_cycle_time = total_cycle_time
        self.last_green_lane = None
        self.omitted_lanes = []
        self.blinking_thread = None
        self.stop_blinking_event = threading.Event()

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
            print("No active lanes available for this cycle.")
            return 0

        active_lanes = self.get_active_lanes()
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, remaining_time)
        allocated_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        # Countdown for the green signal
        for remaining in range(int(allocated_time), 0, -1):
            self.update_signal_callback(green_lane, "green", remaining)
            if remaining <= 5:  # Last 5 seconds will turn yellow
                self.start_blinking(green_lane)  # Start blinking
                time.sleep(5)  # Wait for 5 seconds
                self.stop_blinking_event.set()  # Stop blinking after 5 seconds
                self.update_signal_callback(green_lane, "red")
                break  # Exit after yellow period

            time.sleep(1)

        # Prompt for vehicle counts after the signal ends
        prompt_vehicle_counts()

        self.last_green_lane = green_lane
        self.omitted_lanes.append(green_lane)

        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]

        return allocated_time

    def run_cycle(self, prompt_vehicle_counts):
        remaining_time = self.total_cycle_time

        while remaining_time > 0 and len(self.omitted_lanes) < len(self.lanes):
            allocated_time = self.update_signals(remaining_time, prompt_vehicle_counts)
            remaining_time -= allocated_time

    def start(self, prompt_vehicle_counts):
        while True:
            self.run_cycle(prompt_vehicle_counts)

    def start_blinking(self, lane):
        """Start the blinking yellow signal in a separate thread."""
        self.stop_blinking_event.clear()  # Reset the event
        self.blinking_thread = threading.Thread(target=self.blink_yellow, args=(lane,))
        self.blinking_thread.start()

    def blink_yellow(self, lane):
        """Blink the yellow signal until stopped."""
        while not self.stop_blinking_event.is_set():
            self.update_signal_callback(lane, "yellow")  # Update to yellow
            time.sleep(0.5)  # Time between blinks
            self.update_signal_callback(lane, "red")  # Turn back to red
            time.sleep(0.5)  # Time between blinks

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
            self.controller.start(self.prompt_vehicle_counts)

        signal_thread = threading.Thread(target=run_signal, daemon=True)
        signal_thread.start()

def run_gui():
    root = tk.Tk()
    root.title("Traffic Signal Controller")
    root.geometry("600x400")  # Set a fixed size for the window

    lanes = {"North": 0, "East": 0, "South": 0, "West": 0}
    controller = TrafficSignalController(lanes, None)  # Initialize without a callback first

    gui = TrafficSignalGUI(root, controller)

    # Pass the update_signal method to the controller
    controller.update_signal_callback = gui.update_signal

    root.mainloop()

if __name__ == "__main__":
    run_gui()
