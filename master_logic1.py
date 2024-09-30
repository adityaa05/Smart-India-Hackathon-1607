import time

class TrafficSignalController:
    def __init__(self, lanes, total_cycle_time=120):
        self.lanes = lanes  # Dictionary with lane names as keys and vehicle count as values
        self.total_cycle_time = total_cycle_time  # Total time for one full cycle (T_all), fixed at 120 seconds
        self.last_green_lane = None  # The lane that was green in the last cycle
        self.omitted_lanes = []  # List of lanes that have been green in the current round

    def ask_vehicle_counts(self):
        """Ask user for the vehicle counts manually for each lane in every round."""
        print("\n--- Enter new vehicle counts for all lanes ---")
        for lane in self.lanes:
            self.lanes[lane] = int(input(f"Enter vehicle count for lane {lane}: "))

    def calculate_total_vehicle_count(self, active_lanes):
        """Calculate the total number of vehicles across the active lanes."""
        return sum(self.lanes[lane] for lane in active_lanes)

    def calculate_time_per_vehicle(self, active_lanes, remaining_time):
        """Calculate time per vehicle dynamically based on current vehicle count in the active lanes."""
        total_vehicles = self.calculate_total_vehicle_count(active_lanes)
        if total_vehicles == 0:
            return 0
        return remaining_time / total_vehicles

    def calculate_time_per_lane(self, lane, time_per_vehicle):
        """Calculate time for each lane based on vehicle count in that lane."""
        return time_per_vehicle * self.lanes[lane]

    def get_active_lanes(self):
        """Get the list of lanes eligible for selection (omitting the last green lane and recently green lanes)."""
        # Active lanes are those that are not in the omitted lanes list
        return [lane for lane in self.lanes if lane not in self.omitted_lanes]

    def find_highest_priority_lane(self):
        """Find the lane with the highest vehicle count among the active lanes."""
        active_lanes = self.get_active_lanes()
        if not active_lanes:
            return None  # No active lanes left
        # Sort active lanes by vehicle count and return the one with the highest count
        sorted_lanes = sorted(active_lanes, key=lambda lane: self.lanes[lane], reverse=True)
        return sorted_lanes[0]

    def update_signals(self, remaining_time):
        """Update the traffic signal for the current cycle, omitting the previous green lane."""
        # Get the lane with the highest priority (most vehicles) from active lanes
        green_lane = self.find_highest_priority_lane()

        # If no eligible lane is left (shouldn't happen), keep all red
        if not green_lane:
            print("No active lanes available for this cycle.")
            return 0

        # Calculate time per vehicle for the remaining time
        active_lanes = self.get_active_lanes()
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, remaining_time)

        # Calculate the time required for the green lane
        allocated_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        # Print signal status
        print(f"\nLane {green_lane} is Green (Highest Priority) for {allocated_time:.2f} seconds")
        for lane in self.lanes:
            if lane != green_lane:
                print(f"Lane {lane} is Red")

        # Simulate the green light with interaction 5 seconds before green time ends
        if allocated_time > 5:
            time.sleep(allocated_time - 5)
            print("\n--- 5 seconds remaining ---")
            self.ask_vehicle_counts()  # Ask for new counts before 5 seconds remaining
            time.sleep(5)
        else:
            time.sleep(allocated_time)

        # After choosing the green lane, add it to the omitted lanes
        self.last_green_lane = green_lane
        self.omitted_lanes.append(green_lane)

        # If all lanes have had their turn, reset the omitted lanes (but keep the last green lane)
        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]  # Start a new round omitting only the last green lane

        return allocated_time

    def run_cycle(self):
        """Run one complete traffic signal cycle."""
        print("\nStarting Traffic Signal Cycle")

        remaining_time = self.total_cycle_time

        # Keep running rounds until all lanes have had their turn
        while remaining_time > 0 and len(self.omitted_lanes) < len(self.lanes):
            # Ask for new vehicle counts in each round
            if len(self.omitted_lanes) == 0:    
                self.ask_vehicle_counts()  # Ask for vehicle counts at the start of the cycle

            active_lanes = self.get_active_lanes()

            # Update the signals and allocate time to the green lane
            allocated_time = self.update_signals(remaining_time)

            # Deduct the time allocated from the remaining cycle time
            remaining_time -= allocated_time

            print(f"Remaining time in the cycle: {remaining_time:.2f} seconds\n")

        print("Cycle complete\n")

    def start(self):
        """Start the traffic signal system, running endlessly until stopped."""
        while True:
            self.run_cycle()


# Example usage
if __name__ == "__main__":
    # Define the initial state of lanes with vehicle counts (dummy values, to be updated manually)
    lanes = {
        "North": 0,
        "East": 0,
        "South": 0,
        "West": 0
    }

    # Initialize the traffic signal controller
    controller = TrafficSignalController(lanes)

    # Start the traffic signal system (it will run endlessly)
    controller.start()
