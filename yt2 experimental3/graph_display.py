# graph_display.py
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process, Queue

class GraphDisplay(Process):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.fig, self.ax = plt.subplots()
        self.x_data = []
        self.y_data = []

    def run(self):
        ani = animation.FuncAnimation(self.fig, self.update_graph, interval=1000)
        plt.show()

    def update_graph(self, frame):
        while not self.queue.empty():
            data = self.queue.get()
            self.x_data.append(data[0])
            self.y_data.append(data[1])
        
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, label='Vehicle Count')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Vehicle Count')
        self.ax.set_title('Real-time Vehicle Count')
        self.ax.legend()
        self.ax.grid(True)

