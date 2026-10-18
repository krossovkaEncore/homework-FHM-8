import pytest

from model.graph import Graph


def sample_graph():
    graph = Graph()
    for i in range(5):
        graph.add_vertex(0, 0)
    for source, target in [(1, 2), (1, 3), (2, 3), (3, 4), (4, 5)]:
        graph.add_edge(source, target)
    return graph


def test_undirected_degrees_and_handshaking():
    graph = sample_graph()
    assert graph.vertex_degrees() == {1: 2, 2: 2, 3: 3, 4: 2, 5: 1}
    result = graph.handshaking()
    assert result["degree_sum"] == 10
    assert result["twice_edges"] == 10
    assert result["odd_vertices"] == [3, 5]
    assert result["odd_count_even"] is True
    assert result["valid"] is True


def test_adjacency_matrix_is_symmetric():
    labels, matrix = sample_graph().adjacency_matrix()
    assert labels == [1, 2, 3, 4, 5]
    assert matrix == [
        [0, 1, 1, 0, 0],
        [1, 0, 1, 0, 0],
        [1, 1, 0, 1, 0],
        [0, 0, 1, 0, 1],
        [0, 0, 0, 1, 0],
    ]
    assert all(matrix[i][j] == matrix[j][i]
               for i in range(len(matrix)) for j in range(len(matrix)))


def test_incidence_matrix_has_two_ones_per_undirected_edge():
    _, edge_ids, matrix = sample_graph().incidence_matrix()
    assert edge_ids == [1, 2, 3, 4, 5]
    assert all(sum(matrix[row][col] != 0 for row in range(5)) == 2
               for col in range(5))


def test_directed_degrees_and_incidence():
    graph = Graph(directed=True)
    for _ in range(4):
        graph.add_vertex(0, 0)
    for source, target in [(1, 2), (2, 3), (3, 1), (3, 4), (4, 2)]:
        graph.add_edge(source, target)
    assert sum(graph.out_degrees().values()) == 5
    assert sum(graph.in_degrees().values()) == 5
    _, _, matrix = graph.incidence_matrix()
    for col in range(5):
        values = [row[col] for row in matrix]
        assert values.count(1) == 1
        assert values.count(-1) == 1


def test_remove_vertex_removes_incident_edges():
    graph = sample_graph()
    graph.remove_vertex(3)
    assert 3 not in graph.vertices
    assert len(graph.edges) == 2
    assert graph.vertex_degrees() == {1: 1, 2: 1, 4: 1, 5: 1}
    assert graph.handshaking()["valid"]


def test_loop_degree_is_two():
    graph = Graph(allow_loops=True)
    vertex = graph.add_vertex(0, 0)
    graph.add_edge(vertex, vertex)
    assert graph.vertex_degrees()[vertex] == 2
    assert graph.handshaking()["valid"]


def test_duplicate_edges_and_loops_are_blocked_by_default():
    graph = Graph()
    a, b = graph.add_vertex(0, 0), graph.add_vertex(1, 1)
    graph.add_edge(a, b)
    with pytest.raises(ValueError):
        graph.add_edge(a, b)
    with pytest.raises(ValueError):
        graph.add_edge(a, a)


def test_json_round_trip():
    graph = sample_graph()
    restored = Graph.from_dict(graph.to_dict())
    assert restored.to_dict() == graph.to_dict()


def test_vertex_limit():
    graph = Graph()
    for i in range(50):
        graph.add_vertex(i, i)
    with pytest.raises(ValueError, match="maximum 50"):
        graph.add_vertex(51, 51)
