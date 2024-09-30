import random

class TrafficSignalController:
    def __init__(self, lanes, total_cycle_time=120):
        self.lanes = lanes  # Dictionary with lane names as keys and vehicle count as values
        self.total_cycle_time = total_cycle_time  # Total time for one full cycle (T_all), fixed at 120 seconds
        self.last_green_lane = None  # The lane that was green in the last cycle
        self.omitted_lanes = []  # List of lanes that have been green in the current round

    def update_vehicle_counts(self):
        """Simulate new vehicle counts for each lane in every cycle."""
        # In a real scenario, this would come from sensors or cameras, but here we simulate random values
        for lane in self.lanes:
            self.lanes[lane] = random.randint(0, 30)  # Simulate vehicle counts between 0 and 30

    def calculate_total_vehicle_count(self, active_lanes):
        """Calculate the total number of vehicles across the active lanes."""
        return sum(self.lanes[lane] for lane in active_lanes)

    def calculate_time_per_vehicle(self, active_lanes):
        """Calculate time per vehicle dynamically based on current vehicle count in the active lanes."""
        total_vehicles = self.calculate_total_vehicle_count(active_lanes)
        if total_vehicles == 0:
            return 0
        return self.total_cycle_time / total_vehicles

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

    def update_signals(self):
        """Update the traffic signal for the current cycle, omitting the previous green lane."""
        # Get the lane with the highest priority (most vehicles) from active lanes
        green_lane = self.find_highest_priority_lane()

        # If no eligible lane is left (shouldn't happen), keep all red
        if not green_lane:
            print("No active lanes available for this cycle.")
            return

        # Print signal status
        for lane in self.lanes:
            if lane == green_lane:
                print(f"Lane {lane} is Green (Highest Priority)")
            else:
                print(f"Lane {lane} is Red")

        # After choosing the green lane, add it to the omitted lanes
        self.last_green_lane = green_lane
        self.omitted_lanes.append(green_lane)

        # If all lanes have had their turn, reset the omitted lanes (but keep the last green lane)
        if len(self.omitted_lanes) == len(self.lanes):
            self.omitted_lanes = [green_lane]  # Start a new round omitting only the last green lane

    def run_cycle(self):
        """Run one complete traffic signal cycle."""
        print("Starting Traffic Signal Cycle")

        # Simulate new vehicle counts for all lanes
        self.update_vehicle_counts()

        # Display new vehicle counts
        for lane, count in self.lanes.items():
            print(f"Vehicle count for lane {lane}: {count}")

        active_lanes = self.get_active_lanes()

        # Calculate time per vehicle only for active lanes
        time_per_vehicle = self.calculate_time_per_vehicle(active_lanes)

        # Update the signals (turn the highest priority lane green)
        self.update_signals()

        # Calculate and display the time per lane for the current cycle
        for lane in self.lanes:
            if lane in active_lanes:
                lane_time = self.calculate_time_per_lane(lane, time_per_vehicle)
                print(f"Time allocated for lane {lane}: {lane_time:.2f} seconds")
            else:
                print(f"Lane {lane} is omitted in this cycle.")

        print("Cycle complete\n")


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