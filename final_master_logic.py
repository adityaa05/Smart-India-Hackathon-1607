import random

class TrafficSignalController:
    def __init__(self, lanes, total_cycle_time=120):
        self.lanes = lanes  # Dictionary with lane names as keys and vehicle count as values
        self.total_cycle_time = total_cycle_time  # Total time for one full cycle (T_all), fixed at 120 seconds
        self.last_green_lane = None  # To keep track of the last green lane in the previous cycle
        self.omitted_lanes = []  # List of lanes that have been green in the current round

    def update_vehicle_counts(self):
        """Simulate new vehicle counts for each lane in every cycle."""
        for lane in self.lanes:
            self.lanes[lane] = random.randint(0, 30)  # Simulate vehicle counts between 0 and 30

    def calculate_total_vehicle_count(self, active_lanes):
        """Calculate the total number of vehicles across the active lanes."""
        return sum(self.lanes[lane] for lane in active_lanes)

    def calculate_time_per_vehicle(self, active_lanes, current_Tall):
        """Calculate time per vehicle dynamically based on current vehicle count in the active lanes and remaining Tall."""
        total_vehicles = self.calculate_total_vehicle_count(active_lanes)
        if total_vehicles == 0:
            return 0
        return current_Tall / total_vehicles

    def calculate_time_per_lane(self, lane, time_per_vehicle):
        """Calculate time for each lane based on vehicle count in that lane."""
        return time_per_vehicle * self.lanes[lane]

    def get_active_lanes(self):
        """Get the list of lanes eligible for selection (omitting the recently green lanes)."""
        return [lane for lane in self.lanes if lane not in self.omitted_lanes]

    def find_highest_priority_lane(self, active_lanes):
        """Find the lane with the highest vehicle count among the active lanes."""
        if not active_lanes:
            return None  # No active lanes left
        # Sort active lanes by vehicle count and return the one with the highest count
        sorted_lanes = sorted(active_lanes, key=lambda lane: self.lanes[lane], reverse=True)
        return sorted_lanes[0]

    def update_signals(self, current_Tall):
        """Update the traffic signal for the current cycle, omitting the previous green lane."""
        # Get the active lanes (those that haven't been green in the current round)
        active_lanes = self.get_active_lanes()
        
        # Calculate time per vehicle based on current Tall
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes, current_Tall)
        
        # Get the lane with the highest priority (most vehicles) from active lanes
        green_lane = self.find_highest_priority_lane(active_lanes)

        # If no eligible lane is left, skip
        if not green_lane:
            print("No active lanes available for this cycle.")
            return None, 0

        # Calculate the time required for the green lane
        green_lane_time = self.calculate_time_per_lane(green_lane, time_per_vehicle)

        # After choosing the green lane, add it to the omitted lanes
        self.omitted_lanes.append(green_lane)

        # If all lanes have had their turn, reset the omitted lanes for fairness
        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]  # Reset and start a new round with the last green lane omitted
        
        return green_lane, green_lane_time

    def run_cycle(self):
        """Run one complete traffic signal cycle."""
        current_Tall = self.total_cycle_time  # Initialize the total available time at the start of the cycle

        print("=== Starting New Traffic Signal Cycle ===")

        # Add the last green lane to omitted lanes at the beginning of the cycle (if there was one)
        if self.last_green_lane:
            self.omitted_lanes = [self.last_green_lane]
        else:
            self.omitted_lanes = []

        while current_Tall > 0:
            # Simulate new vehicle counts for all lanes in every round
            self.update_vehicle_counts()

            # Display new vehicle counts
            print("\nVehicle Counts:")
            for lane, count in self.lanes.items():
                print(f"  Lane {lane}: {count} vehicles")

            # Update signals (find the lane with the highest priority and allocate time)
            green_lane, allocated_time = self.update_signals(current_Tall)

            # If no lane could be selected, break the loop
            if not green_lane:
                break

            print(f"\nSignal Status:")
            for lane in self.lanes:
                if lane == green_lane:
                    print(f"  Lane {lane} is GREEN (Priority Lane)")
                else:
                    print(f"  Lane {lane} is RED")

            # Display time allocation for the current round
            print(f"\nTime Allocated for Lane {green_lane}: {allocated_time:.2f} seconds")
            current_Tall -= allocated_time
            print(f"Remaining Time in the Cycle: {current_Tall:.2f} seconds")

        # Store the last green lane so it can be omitted in the next cycle
        self.last_green_lane = self.omitted_lanes[-1] if self.omitted_lanes else None

        print("\n=== Cycle Complete ===\n")

# Example usage
if __name__ == "__main__":
    # Define the initial state of lanes with vehicle counts
    lanes = {
        "North": 10,
        "East": 5,
        "South": 20,
        "West": 7
    }

    # Total cycle time is fixed at 120 seconds
    total_cycle_time = 120

    # Initialize the traffic signal controller
    controller = TrafficSignalController(lanes, total_cycle_time)

    # Simulate multiple cycles with dynamic vehicle count updates and lane omission
    for cycle in range(8):  # Run 8 cycles to demonstrate the dynamic update
        print(f"--- Cycle {cycle+1} ---")
        controller.run_cycle()
    