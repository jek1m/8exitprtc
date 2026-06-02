import math


def flat_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class CorridorNavigation:
    def __init__(self):
        self.segments = [
            ((0, -50), (0, 50)),
            ((0, 50), (0, 55)),
            ((0, 55), (-50, 55)),
            ((-50, 55), (-50, 105)),
            ((0, -50), (0, -55)),
            ((0, -55), (50, -55)),
            ((50, -55), (50, -105)),
        ]

        self.nodes = sorted({point for segment in self.segments for point in segment})
        self.base_graph = {node: [] for node in self.nodes}

        for start, end in self.segments:
            distance = flat_distance(start, end)
            self.base_graph[start].append((end, distance))
            self.base_graph[end].append((start, distance))

    def find_path(self, start_position, target_position):
        start_point, start_segment = self._nearest_point_on_path(start_position)
        target_point, target_segment = self._nearest_point_on_path(target_position)

        if start_segment == target_segment:
            return [start_position, target_position]

        start_key = ('start', start_point)
        target_key = ('target', target_point)

        graph = {node: neighbors[:] for node, neighbors in self.base_graph.items()}
        graph[start_key] = []
        graph[target_key] = []

        self._connect_dynamic_point(graph, start_key, start_point, start_segment)
        self._connect_dynamic_point(graph, target_key, target_point, target_segment)

        path = self._shortest_path(graph, start_key, target_key)

        if path and flat_distance(path[-1], target_position) > 0.05:
            path.append(target_position)

        return path

    def clamp_to_path(self, position, radius):
        nearest_point, _ = self._nearest_point_on_path(position)
        distance = flat_distance(position, nearest_point)

        if distance <= radius or distance == 0:
            return position

        dx = position[0] - nearest_point[0]
        dz = position[1] - nearest_point[1]

        return (
            nearest_point[0] + dx / distance * radius,
            nearest_point[1] + dz / distance * radius,
        )

    def _nearest_point_on_path(self, position):
        best_point = None
        best_segment_index = 0
        best_distance = float('inf')

        for index, segment in enumerate(self.segments):
            point = self._project_to_segment(position, *segment)
            distance = flat_distance(position, point)

            if distance < best_distance:
                best_point = point
                best_segment_index = index
                best_distance = distance

        return best_point, best_segment_index

    def _project_to_segment(self, position, start, end):
        px, pz = position
        ax, az = start
        bx, bz = end

        dx = bx - ax
        dz = bz - az
        length_squared = dx * dx + dz * dz

        if length_squared == 0:
            return start

        t = ((px - ax) * dx + (pz - az) * dz) / length_squared
        t = max(0, min(1, t))

        return (ax + dx * t, az + dz * t)

    def _connect_dynamic_point(self, graph, key, point, segment_index):
        start, end = self.segments[segment_index]

        for node in (start, end):
            distance = flat_distance(point, node)
            graph[key].append((node, distance))
            graph[node].append((key, distance))

    def _shortest_path(self, graph, start_key, target_key):
        distances = {start_key: 0}
        previous = {}
        unvisited = set(graph.keys())

        while unvisited:
            current = min(unvisited, key=lambda node: distances.get(node, float('inf')))

            if distances.get(current, float('inf')) == float('inf'):
                break

            unvisited.remove(current)

            if current == target_key:
                break

            for neighbor, edge_distance in graph[current]:
                new_distance = distances[current] + edge_distance
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

        if target_key not in distances:
            return []

        path = []
        current = target_key

        while current != start_key:
            path.append(current)
            current = previous[current]

        path.append(start_key)
        path.reverse()

        return [self._node_position(node) for node in path]

    def _node_position(self, node):
        if isinstance(node, tuple) and len(node) == 2 and isinstance(node[0], str):
            return node[1]

        return node
