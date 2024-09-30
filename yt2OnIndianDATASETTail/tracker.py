import math


class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        self.center_points = {}

        # Keep the count of the IDs
        self.id_count = 0

        # Dictionary to store tracking history for each object
        self.track_history = {}

    def update(self, objects_rect):
        # Objects boxes and IDs
        objects_bbs_ids = []

        for rect in objects_rect:
            if len(rect) < 4:
                continue
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            # Check if object was detected already
            same_object_detected = False
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < 30:  # Distance threshold to match objects
                    self.center_points[id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, id])

                    # Append current position to history for drawing tail
                    if id in self.track_history:
                        self.track_history[id].append((cx, cy))
                    else:
                        self.track_history[id] = [(cx, cy)]

                    # Limit the tail to the last 10 positions
                    self.track_history[id] = self.track_history[id][-10:]

                    same_object_detected = True
                    break

            # If a new object is detected, assign a new ID
            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])

                # Start tracking history for the new object
                self.track_history[self.id_count] = [(cx, cy)]

                self.id_count += 1

        # Update the center points dictionary to keep only the objects currently being tracked
        self.center_points = {id: self.center_points[id] for id in self.track_history}

        return objects_bbs_ids
