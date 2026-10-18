"""Graph model and mathematical operations for Graph Lab."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Edge:
    id: int
    source: int
    target: int


class Graph:
    """A graph with stable vertex labels and edge IDs.

    In a directed graph, source -> target defines the arc direction.
    Loops and parallel edges are optional. An undirected loop contributes
    two to the degree, as required by the handshaking lemma.
    """

    MAX_VERTICES = 50

    def __init__(self, directed: bool = False, allow_loops: bool = False,
                 allow_parallel: bool = False) -> None:
        self.directed = directed
        self.allow_loops = allow_loops
        self.allow_parallel = allow_parallel
        self.vertices: dict[int, tuple[float, float]] = {}
        self.edges: list[Edge] = []
        self._next_vertex_id = 1
        self._next_edge_id = 1

    def add_vertex(self, x: float, y: float, label: int | None = None) -> int:
        if len(self.vertices) >= self.MAX_VERTICES:
            raise ValueError(f"Graph limit reached: maximum {self.MAX_VERTICES} vertices.")
        if label is None:
            label = self._next_vertex_id
            while label in self.vertices:
                label += 1
        if label in self.vertices:
            raise ValueError(f"Vertex {label} already exists.")
        self.vertices[label] = (float(x), float(y))
        self._next_vertex_id = max(self._next_vertex_id, label + 1)
        return label

    def move_vertex(self, vertex: int, x: float, y: float) -> None:
        self._require_vertex(vertex)
        self.vertices[vertex] = (float(x), float(y))

    def add_edge(self, source: int, target: int) -> int:
        self._require_vertex(source)
        self._require_vertex(target)
        if source == target and not self.allow_loops:
            raise ValueError("Loops are disabled.")
        if not self.allow_parallel:
            for edge in self.edges:
                if self.directed:
                    duplicate = edge.source == source and edge.target == target
                else:
                    duplicate = {edge.source, edge.target} == {source, target}
                if duplicate:
                    raise ValueError("Parallel edges are disabled.")
        edge_id = self._next_edge_id
        self._next_edge_id += 1
        self.edges.append(Edge(edge_id, source, target))
        return edge_id

    def remove_edge(self, edge_id: int) -> None:
        before = len(self.edges)
        self.edges = [edge for edge in self.edges if edge.id != edge_id]
        if len(self.edges) == before:
            raise ValueError(f"Edge e{edge_id} does not exist.")

    def remove_vertex(self, vertex: int) -> None:
        self._require_vertex(vertex)
        del self.vertices[vertex]
        self.edges = [e for e in self.edges if e.source != vertex and e.target != vertex]

    def clear(self) -> None:
        self.vertices.clear()
        self.edges.clear()
        self._next_vertex_id = 1
        self._next_edge_id = 1

    def set_directed(self, directed: bool) -> None:
        self.directed = bool(directed)

    def vertex_degrees(self) -> dict[int, int]:
        if self.directed:
            raise ValueError("Use in_degrees() and out_degrees() for a directed graph.")
        result = {v: 0 for v in self.vertices}
        for edge in self.edges:
            if edge.source == edge.target:
                result[edge.source] += 2
            else:
                result[edge.source] += 1
                result[edge.target] += 1
        return result

    def out_degrees(self) -> dict[int, int]:
        if not self.directed:
            raise ValueError("Out-degree is defined here for directed graphs.")
        result = {v: 0 for v in self.vertices}
        for edge in self.edges:
            result[edge.source] += 1
        return result

    def in_degrees(self) -> dict[int, int]:
        if not self.directed:
            raise ValueError("In-degree is defined here for directed graphs.")
        result = {v: 0 for v in self.vertices}
        for edge in self.edges:
            result[edge.target] += 1
        return result

    def adjacency_matrix(self) -> tuple[list[int], list[list[int]]]:
        labels = sorted(self.vertices)
        index = {label: i for i, label in enumerate(labels)}
        matrix = [[0 for _ in labels] for _ in labels]
        for edge in self.edges:
            i, j = index[edge.source], index[edge.target]
            matrix[i][j] += 1
            if not self.directed and i != j:
                matrix[j][i] += 1
        return labels, matrix

    def incidence_matrix(self) -> tuple[list[int], list[int], list[list[int]]]:
        labels = sorted(self.vertices)
        edge_ids = [edge.id for edge in self.edges]
        matrix = [[0 for _ in edge_ids] for _ in labels]
        row = {label: i for i, label in enumerate(labels)}
        for col, edge in enumerate(self.edges):
            if self.directed:
                if edge.source == edge.target:
                    # A directed loop has both its start and end at one vertex;
                    # the +1 and -1 cancel in the incidence matrix.
                    matrix[row[edge.source]][col] = 0
                else:
                    matrix[row[edge.source]][col] = 1
                    matrix[row[edge.target]][col] = -1
            elif edge.source == edge.target:
                # Common 0/1 convention: a loop is incident to its vertex.
                matrix[row[edge.source]][col] = 1
            else:
                matrix[row[edge.source]][col] = 1
                matrix[row[edge.target]][col] = 1
        return labels, edge_ids, matrix

    def handshaking(self) -> dict[str, Any]:
        if self.directed:
            out_sum = sum(self.out_degrees().values())
            in_sum = sum(self.in_degrees().values())
            return {
                "directed": True, "out_sum": out_sum, "in_sum": in_sum,
                "arc_count": len(self.edges),
                "valid": out_sum == len(self.edges) and in_sum == len(self.edges),
            }
        degrees = self.vertex_degrees()
        degree_sum = sum(degrees.values())
        odd_vertices = [v for v, degree in degrees.items() if degree % 2]
        return {
            "directed": False, "degree_sum": degree_sum,
            "twice_edges": 2 * len(self.edges), "odd_vertices": odd_vertices,
            "odd_count": len(odd_vertices),
            "odd_count_even": len(odd_vertices) % 2 == 0,
            "valid": degree_sum == 2 * len(self.edges),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "directed": self.directed,
            "allow_loops": self.allow_loops,
            "allow_parallel": self.allow_parallel,
            "vertices": [{"id": v, "x": xy[0], "y": xy[1]}
                         for v, xy in self.vertices.items()],
            "edges": [{"id": e.id, "source": e.source, "target": e.target}
                      for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Graph":
        graph = cls(bool(data.get("directed", False)),
                    bool(data.get("allow_loops", False)),
                    bool(data.get("allow_parallel", False)))
        for item in data.get("vertices", []):
            graph.add_vertex(item["x"], item["y"], int(item["id"]))
        for item in data.get("edges", []):
            source, target = int(item["source"]), int(item["target"])
            graph._require_vertex(source)
            graph._require_vertex(target)
            if source == target and not graph.allow_loops:
                raise ValueError("JSON contains a loop but loops are disabled.")
            if not graph.allow_parallel:
                for existing in graph.edges:
                    duplicate = (existing.source == source and existing.target == target)
                    if not graph.directed:
                        duplicate = {existing.source, existing.target} == {source, target}
                    if duplicate:
                        raise ValueError("JSON contains parallel edges but they are disabled.")
            edge_id = int(item["id"])
            if any(e.id == edge_id for e in graph.edges):
                raise ValueError(f"Duplicate edge ID e{edge_id}.")
            graph.edges.append(Edge(edge_id, source, target))
            graph._next_edge_id = max(graph._next_edge_id, edge_id + 1)
        return graph

    def _require_vertex(self, vertex: int) -> None:
        if vertex not in self.vertices:
            raise ValueError(f"Vertex {vertex} does not exist.")
