# homework-FHM-8

написано с помощью ChatGPT

# Graph Lab

Graph Lab is a local desktop graph editor for a Discrete Mathematics course. It uses Python 3.11+ and Tkinter, with no external services or runtime dependencies.

## Features

- Add vertices, edges/arcs, move vertices, delete objects, undo (`Ctrl+Z`) and clear the graph.
- Switch between undirected and directed graphs without removing graph data.
- Optional loops and parallel edges. In an undirected graph, a loop contributes 2 to the degree.
- Live vertex/edge counts, degree table, handshaking checks and odd-degree vertex count.
- Adjacency and incidence matrices.
- Save/load JSON; copy matrices to the clipboard as CSV; export degrees to CSV.
- Circular automatic layout and a 50-vertex limit.

## Requirements

- Python 3.11 or newer.
- Tkinter (usually included with Python; on some Linux distributions install the system package, e.g. `python3-tk`).
- `pytest` is needed only to run tests.

## Run

From the project root:

```bash
python main.py
```

Install the test dependency and run tests:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## Project layout

```text
graph_lab/
├── main.py
├── model/
│   ├── __init__.py
│   └── graph.py
├── ui/
│   ├── __init__.py
│   └── app.py
├── tests/
│   └── test_graph.py
├── requirements.txt
└── README.md
```

## Usage

1. Select **Vertex** and click empty canvas space to add vertices.
2. Select **Edge**, click the source vertex and then the target. For directed graphs, this order defines the arrow.
3. Use **Move** to drag vertices, or **Delete** to remove a vertex or edge.
4. Enable **Directed** for an oriented graph. Enable loops/parallel edges only when needed.
5. Inspect **Degrees & Lemma**, **Adjacency**, and **Incidence** tabs.
6. Use **Save JSON** / **Open JSON** to persist a graph.

Keyboard shortcuts: `Ctrl+Z` undoes the last recorded change; `Delete` removes the selected vertex/edge.

## Matrix conventions

- Adjacency matrix: rows/columns use ascending vertex labels. For undirected graphs, entries are symmetric. Parallel edges are represented by their multiplicity.
- Undirected incidence matrix: each ordinary edge column contains two `1` values. A loop is represented by one `1` in its vertex row; its degree contribution is still 2.
- Directed incidence matrix: `+1` at the source and `-1` at the target. For a directed loop, the two contributions cancel, so the matrix entry is `0`.
- The directed handshaking identities are `sum(out-degree) = |A|` and `sum(in-degree) = |A|`.

## Acceptance example

Build vertices `1..5` and edges `12, 13, 23, 34, 45`. The degree sequence is `2, 2, 3, 2, 1`, the degree sum is `10 = 2 × 5`, and the odd-degree vertices are `3` and `5`.

## Notes

The interface uses native Tkinter widgets and should work on Windows and Linux. The matrix tables have horizontal and vertical scrollbars for larger graphs.

