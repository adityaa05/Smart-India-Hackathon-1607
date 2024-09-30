import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Initialize the figure and axis for the graph
fig, ax = plt.subplots()
x_data, y_data = [], []

def plot_graph(queue):
    global x_data, y_data

    # Retrieve data from the queue
    while not queue.empty():
        elapsed_time, vehicle_count = queue.get()
        x_data.append(elapsed_time)
        y_data.append(vehicle_count)

    # Clear the previous plot
    ax.clear()

    # Plot the new data
    ax.plot(x_data, y_data, label='Vehicle Count')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Vehicle Count')
    ax.set_title('Real-Time Vehicle Count')
    ax.legend()

    # Pause the plot for a brief moment to update the graph
    plt.pause(0.1)
