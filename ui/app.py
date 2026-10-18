"""Tkinter interface for Graph Lab."""
from __future__ import annotations

import csv
import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from model.graph import Graph, Edge


RADIUS = 22


class GraphLabApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Graph Lab — Discrete Mathematics")
        self.geometry("1180x760")
        self.minsize(920, 600)
        self.graph = Graph()
        self.mode = tk.StringVar(value="Vertex")
        self.directed_var = tk.BooleanVar(value=False)
        self.loops_var = tk.BooleanVar(value=False)
        self.parallel_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Choose a mode and click the canvas.")
        self.selected_vertex: int | None = None
        self.selected_edge: int | None = None
        self.drag_vertex: int | None = None
        self.drag_offset = (0, 0)
        self.undo_stack: list[dict] = []
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        for label in ("Vertex", "Edge", "Delete", "Move"):
            ttk.Radiobutton(toolbar, text=label, value=label, variable=self.mode,
                            command=self._mode_changed).pack(side=tk.LEFT, padx=3)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Checkbutton(toolbar, text="Directed", variable=self.directed_var,
                        command=self._toggle_directed).pack(side=tk.LEFT, padx=3)
        ttk.Checkbutton(toolbar, text="Allow loops", variable=self.loops_var,
                        command=self._toggle_options).pack(side=tk.LEFT, padx=3)
        ttk.Checkbutton(toolbar, text="Allow parallel edges", variable=self.parallel_var,
                        command=self._toggle_options).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Auto layout", command=self._auto_layout).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Undo (Ctrl+Z)", command=self._undo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Clear all", command=self._clear).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Open JSON", command=self._load_json).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Save JSON", command=self._save_json).pack(side=tk.LEFT, padx=3)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        left = ttk.Frame(body)
        right = ttk.Frame(body, width=390)
        body.add(left, weight=3)
        body.add(right, weight=2)
        self.canvas = tk.Canvas(left, bg="#fbfcfe", highlightthickness=1,
                                highlightbackground="#ccd4df")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._canvas_click)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Delete>", lambda _e: self._delete_selected())
        self.canvas.focus_set()

        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self.stats_tab = ttk.Frame(self.tabs, padding=8)
        self.adj_tab = ttk.Frame(self.tabs, padding=6)
        self.inc_tab = ttk.Frame(self.tabs, padding=6)
        self.tabs.add(self.stats_tab, text="Degrees & Lemma")
        self.tabs.add(self.adj_tab, text="Adjacency")
        self.tabs.add(self.inc_tab, text="Incidence")
        self.stats_text = tk.Text(self.stats_tab, height=10, wrap=tk.WORD,
                                  font=("TkDefaultFont", 10), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.lemma_label = ttk.Label(self.stats_tab, text="", padding=6)
        self.lemma_label.pack(fill=tk.X)
        ttk.Button(self.stats_tab, text="Export degrees CSV",
                   command=self._export_degrees).pack(anchor=tk.W, pady=(6, 0))
        self.adj_frame = ttk.Frame(self.adj_tab)
        self.adj_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(self.adj_tab, text="Copy adjacency CSV",
                   command=lambda: self._copy_matrix("adjacency")).pack(anchor=tk.W, pady=5)
        self.inc_frame = ttk.Frame(self.inc_tab)
        self.inc_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(self.inc_tab, text="Copy incidence CSV",
                   command=lambda: self._copy_matrix("incidence")).pack(anchor=tk.W, pady=5)
        ttk.Label(self, textvariable=self.status_var, anchor=tk.W, padding=(8, 4)).pack(
            side=tk.BOTTOM, fill=tk.X)
        self.bind("<Control-z>", lambda _e: self._undo())
        self.bind("<Delete>", lambda _e: self._delete_selected())

    def _snapshot(self) -> None:
        self.undo_stack.append(self.graph.to_dict())
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def _undo(self) -> None:
        if not self.undo_stack:
            self.status_var.set("Nothing to undo.")
            return
        try:
            self.graph = Graph.from_dict(self.undo_stack.pop())
            self.directed_var.set(self.graph.directed)
            self.loops_var.set(self.graph.allow_loops)
            self.parallel_var.set(self.graph.allow_parallel)
            self.selected_vertex = self.selected_edge = None
            self._refresh()
            self.status_var.set("Last action undone.")
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Undo failed", str(exc))

    def _mode_changed(self) -> None:
        self.selected_vertex = None
        self.status_var.set(f"Mode: {self.mode.get()}.")
        self._draw()

    def _toggle_directed(self) -> None:
        self._snapshot()
        self.graph.set_directed(self.directed_var.get())
        self.selected_vertex = None
        self._refresh()

    def _toggle_options(self) -> None:
        self._snapshot()
        self.graph.allow_loops = self.loops_var.get()
        self.graph.allow_parallel = self.parallel_var.get()
        self._refresh()

    def _canvas_click(self, event) -> None:
        self.canvas.focus_set()
        mode = self.mode.get()
        vertex = self._hit_vertex(event.x, event.y)
        edge = self._hit_edge(event.x, event.y)
        if mode == "Vertex":
            if vertex is None:
                self._snapshot()
                try:
                    self.graph.add_vertex(event.x, event.y)
                    self._refresh()
                except ValueError as exc:
                    messagebox.showwarning("Cannot add vertex", str(exc))
        elif mode == "Edge":
            if vertex is None:
                self.status_var.set("Choose a vertex, then choose the second vertex.")
                return
            if self.selected_vertex is None:
                self.selected_vertex = vertex
                self.status_var.set(f"Vertex {vertex} selected. Choose the target vertex.")
                self._draw()
            else:
                source = self.selected_vertex
                target = vertex
                self.selected_vertex = None
                self._snapshot()
                try:
                    edge_id = self.graph.add_edge(source, target)
                    self.selected_edge = edge_id
                    self.status_var.set(f"Added e{edge_id}: {source} {'→' if self.graph.directed else '—'} {target}.")
                    self._refresh()
                except ValueError as exc:
                    messagebox.showwarning("Cannot add edge", str(exc))
                    self._draw()
        elif mode == "Delete":
            if vertex is not None:
                self._snapshot()
                self.graph.remove_vertex(vertex)
                self.selected_vertex = self.selected_edge = None
                self._refresh()
            elif edge is not None:
                self._snapshot()
                self.graph.remove_edge(edge)
                self.selected_edge = None
                self._refresh()
        elif mode == "Move":
            if vertex is not None:
                self._snapshot()
                self.drag_vertex = vertex
                x, y = self.graph.vertices[vertex]
                self.drag_offset = (x - event.x, y - event.y)
                self.selected_vertex = vertex
                self._draw()
            elif edge is not None:
                self.selected_edge = edge
                self._draw()

    def _drag(self, event) -> None:
        if self.mode.get() == "Move" and self.drag_vertex is not None:
            x = max(RADIUS, event.x + self.drag_offset[0])
            y = max(RADIUS, event.y + self.drag_offset[1])
            self.graph.move_vertex(self.drag_vertex, x, y)
            self._draw()

    def _release(self, _event) -> None:
        if self.drag_vertex is not None:
            self.drag_vertex = None
            self._refresh()

    def _delete_selected(self) -> None:
        if self.selected_vertex is not None and self.selected_vertex in self.graph.vertices:
            self._snapshot()
            self.graph.remove_vertex(self.selected_vertex)
            self.selected_vertex = None
            self._refresh()
        elif self.selected_edge is not None and any(e.id == self.selected_edge for e in self.graph.edges):
            self._snapshot()
            self.graph.remove_edge(self.selected_edge)
            self.selected_edge = None
            self._refresh()

    def _clear(self) -> None:
        if not self.graph.vertices and not self.graph.edges:
            return
        if messagebox.askyesno("Clear graph", "Delete all vertices and edges?"):
            self._snapshot()
            self.graph.clear()
            self.selected_vertex = self.selected_edge = None
            self._refresh()

    def _auto_layout(self) -> None:
        vertices = sorted(self.graph.vertices)
        if not vertices:
            return
        self._snapshot()
        self.update_idletasks()
        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 300)
        cx, cy = width / 2, height / 2
        radius = max(70, min(width, height) * 0.36)
        for i, vertex in enumerate(vertices):
            angle = -math.pi / 2 + 2 * math.pi * i / len(vertices)
            self.graph.move_vertex(vertex, cx + radius * math.cos(angle),
                                   cy + radius * math.sin(angle))
        self._refresh()

    def _hit_vertex(self, x: float, y: float) -> int | None:
        for vertex, (vx, vy) in reversed(list(self.graph.vertices.items())):
            if math.hypot(vx - x, vy - y) <= RADIUS + 3:
                return vertex
        return None

    def _hit_edge(self, x: float, y: float) -> int | None:
        best = (9.0, None)
        for edge in self.graph.edges:
            x1, y1 = self.graph.vertices[edge.source]
            x2, y2 = self.graph.vertices[edge.target]
            if edge.source == edge.target:
                distance = abs(math.hypot(x - x1, y - y1) - RADIUS - 10)
            else:
                dx, dy = x2 - x1, y2 - y1
                denom = dx * dx + dy * dy
                t = 0 if denom == 0 else max(0, min(1, ((x-x1)*dx+(y-y1)*dy)/denom))
                distance = math.hypot(x - (x1+t*dx), y - (y1+t*dy))
            if distance < best[0]:
                best = (distance, edge.id)
        return best[1]

    def _draw(self) -> None:
        self.canvas.delete("all")
        # Draw edges first so vertices stay above them.
        for edge in self.graph.edges:
            x1, y1 = self.graph.vertices[edge.source]
            x2, y2 = self.graph.vertices[edge.target]
            color = "#d9485f" if edge.id == self.selected_edge else "#526174"
            width = 3 if edge.id == self.selected_edge else 2
            if edge.source == edge.target:
                self.canvas.create_oval(x1 + 5, y1 - 34, x1 + 35, y1 - 4,
                                        outline=color, width=width)
                tx, ty = x1 + 28, y1 - 30
            else:
                dx, dy = x2 - x1, y2 - y1
                length = max(math.hypot(dx, dy), 1)
                ux, uy = dx / length, dy / length
                sx, sy = x1 + ux * RADIUS, y1 + uy * RADIUS
                ex, ey = x2 - ux * RADIUS, y2 - uy * RADIUS
                # Slight offset for parallel edges.
                parallel_index = [e for e in self.graph.edges
                                  if {e.source, e.target} == {edge.source, edge.target}].index(edge)
                if parallel_index:
                    offset = (parallel_index - 0.5) * 9
                    sx -= uy * offset; sy += ux * offset
                    ex -= uy * offset; ey += ux * offset
                self.canvas.create_line(sx, sy, ex, ey, fill=color, width=width,
                                        arrow=tk.LAST if self.graph.directed else tk.NONE,
                                        arrowshape=(10, 12, 4))
                tx, ty = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_text(tx, ty - 8, text=f"e{edge.id}", fill="#374151",
                                    font=("TkDefaultFont", 8), tags=("edge_label",))
        degrees = (self.graph.out_degrees() if self.graph.directed else self.graph.vertex_degrees())
        indegrees = self.graph.in_degrees() if self.graph.directed else {}
        for vertex, (x, y) in self.graph.vertices.items():
            fill = "#dbeafe" if vertex == self.selected_vertex else "#ffffff"
            outline = "#2563eb" if vertex == self.selected_vertex else "#334155"
            self.canvas.create_oval(x-RADIUS, y-RADIUS, x+RADIUS, y+RADIUS,
                                    fill=fill, outline=outline, width=2)
            self.canvas.create_text(x, y-4, text=str(vertex), font=("TkDefaultFont", 11, "bold"))
            label = (f"+{degrees[vertex]} / −{indegrees[vertex]}" if self.graph.directed
                     else f"deg {degrees[vertex]}")
            self.canvas.create_text(x, y+RADIUS+10, text=label, fill="#475569",
                                    font=("TkDefaultFont", 8))
        if not self.graph.vertices:
            self.canvas.create_text(220, 80, text="Select Vertex mode, then click to add a vertex.",
                                    fill="#64748b", font=("TkDefaultFont", 11))
        self._render_stats()
        self._render_matrices()

    def _refresh(self) -> None:
        self._draw()

    def _render_stats(self) -> None:
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, f"|V| = {len(self.graph.vertices)}\n|E| = {len(self.graph.edges)}\n\n")
        if self.graph.directed:
            outd, ind = self.graph.out_degrees(), self.graph.in_degrees()
            self.stats_text.insert(tk.END, "Vertex     deg+     deg−\n")
            for v in sorted(self.graph.vertices):
                self.stats_text.insert(tk.END, f"{v:<10}{outd[v]:<9}{ind[v]}\n")
            result = self.graph.handshaking()
            self.stats_text.insert(tk.END, f"\nΣ deg+ = {result['out_sum']}\n")
            self.stats_text.insert(tk.END, f"Σ deg− = {result['in_sum']}\n")
            self.stats_text.insert(tk.END, f"|A| = {result['arc_count']}\n")
            text = "✓ Directed handshaking identities hold" if result["valid"] else "✗ Identity violated"
        else:
            degrees = self.graph.vertex_degrees()
            self.stats_text.insert(tk.END, "Vertex     Degree\n")
            for v in sorted(self.graph.vertices):
                self.stats_text.insert(tk.END, f"{v:<11}{degrees[v]}\n")
            result = self.graph.handshaking()
            self.stats_text.insert(tk.END, f"\nΣ deg(v) = {result['degree_sum']}\n")
            self.stats_text.insert(tk.END, f"2|E| = {result['twice_edges']}\n")
            self.stats_text.insert(tk.END, f"Odd-degree vertices: {result['odd_vertices']}\n")
            self.stats_text.insert(tk.END, f"Odd-degree count is even: {result['odd_count_even']}\n")
            text = "✓ Handshaking lemma holds" if result["valid"] else "✗ Handshaking lemma violated"
        self.stats_text.configure(state=tk.DISABLED)
        self.lemma_label.configure(text=text, foreground="#167444" if result["valid"] else "#c62828")

    def _matrix_widget(self, parent, headers, rows) -> None:
        for child in parent.winfo_children():
            child.destroy()
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(container, columns=[str(h) for h in headers], show="headings",
                            height=16)
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        xscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1); container.columnconfigure(0, weight=1)
        for h in headers:
            tree.heading(str(h), text=str(h))
            tree.column(str(h), width=42, minwidth=35, anchor=tk.CENTER, stretch=False)
        for label, values in rows:
            tree.insert("", tk.END, iid=str(label), values=values)
        tree.bind("<<TreeviewSelect>>", lambda _e: self._matrix_selected(tree, headers, rows))

    def _matrix_selected(self, tree, headers, rows) -> None:
        selection = tree.selection()
        if not selection:
            return
        row_label = selection[0]
        column = tree.identify_column(tree.winfo_pointerx() - tree.winfo_rootx())
        try:
            col_index = int(column[1:]) - 1
            if col_index < 0:
                return
            if self.tabs.index(self.tabs.select()) == 1:
                source, target = int(row_label), int(headers[col_index])
                found = next((e for e in self.graph.edges if
                              (e.source == source and e.target == target) or
                              (not self.graph.directed and e.source == target and e.target == source)), None)
                self.selected_edge = found.id if found else None
            else:
                edge_id = int(headers[col_index][1:])
                self.selected_edge = edge_id if any(e.id == edge_id for e in self.graph.edges) else None
            self._draw()
        except (ValueError, IndexError):
            return

    def _render_matrices(self) -> None:
        labels, matrix = self.graph.adjacency_matrix()
        self._matrix_widget(self.adj_frame, labels,
                            [(labels[i], matrix[i]) for i in range(len(labels))])
        labels, edge_ids, incidence = self.graph.incidence_matrix()
        headers = [f"e{edge_id}" for edge_id in edge_ids]
        self._matrix_widget(self.inc_frame, headers,
                            [(labels[i], incidence[i]) for i in range(len(labels))])

    def _copy_matrix(self, kind: str) -> None:
        if kind == "adjacency":
            labels, matrix = self.graph.adjacency_matrix()
            rows = [["vertex", *labels]]
            rows.extend([[label, *matrix[i]] for i, label in enumerate(labels)])
        else:
            labels, edge_ids, matrix = self.graph.incidence_matrix()
            rows = [["vertex", *[f"e{x}" for x in edge_ids]]]
            rows.extend([[label, *matrix[i]] for i, label in enumerate(labels)])
        from io import StringIO
        stream = StringIO()
        csv.writer(stream, lineterminator="\n").writerows(rows)
        self.clipboard_clear()
        self.clipboard_append(stream.getvalue())
        self.status_var.set(f"{kind.title()} matrix copied as CSV to clipboard.")

    def _export_degrees(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")], title="Export vertex degrees")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if self.graph.directed:
                writer.writerow(["vertex", "out_degree", "in_degree"])
                outd, ind = self.graph.out_degrees(), self.graph.in_degrees()
                for v in sorted(self.graph.vertices):
                    writer.writerow([v, outd[v], ind[v]])
            else:
                writer.writerow(["vertex", "degree"])
                for v, degree in sorted(self.graph.vertex_degrees().items()):
                    writer.writerow([v, degree])
        self.status_var.set(f"Degrees exported to {path}")

    def _save_json(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json",
                    filetypes=[("JSON files", "*.json")], title="Save graph")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.graph.to_dict(), file, indent=2)
        self.status_var.set(f"Graph saved to {path}")

    def _load_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")],
                                          title="Open graph")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as file:
                graph = Graph.from_dict(json.load(file))
            self._snapshot()
            self.graph = graph
            self.directed_var.set(graph.directed)
            self.loops_var.set(graph.allow_loops)
            self.parallel_var.set(graph.allow_parallel)
            self.selected_vertex = self.selected_edge = None
            self._refresh()
            self.status_var.set(f"Loaded {path}")
        except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            messagebox.showerror("Cannot open graph", str(exc))


def main() -> None:
    GraphLabApp().mainloop()


if __name__ == "__main__":
    main()
