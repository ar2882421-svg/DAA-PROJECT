import tkinter as tk
from tkinter import ttk, messagebox
import random
import heapq

# -------------------- CONFIG --------------------
ROWS, COLS = 28, 48
CELL = 22
PADDING = 6
WALL_RATE = 0.27

COLOR_BG = "#0f172a"
COLOR_GRID = "#1e293b"
COLOR_WALL = "#0ea5e9"
COLOR_START = "#22c55e"
COLOR_END = "#ef4444"
COLOR_OPEN = "#fde047"
COLOR_CLOSED = "#a78bfa"
COLOR_PATH = "#fb7185"
COLOR_TEXT = "#e2e8f0"

# -------------------- MODEL --------------------
class Cell:
    __slots__ = ("r", "c", "wall", "start", "end", "rect")
    def __init__(self, r, c):
        self.r, self.c = r, c
        self.wall = False
        self.start = False
        self.end = False
        self.rect = None

class Grid:
    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.cells = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
        self.start = None
        self.end = None

    def neighbors4(self, r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if not self.cells[nr][nc].wall:
                    yield nr, nc

# -------------------- TK UI --------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Graph Pathfinding Visualizer — Dijkstra Algorithm")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        self.g = Grid(ROWS, COLS)
        w = COLS * CELL + PADDING * 2
        h = ROWS * CELL + PADDING * 2

        # canvas
        self.canvas = tk.Canvas(self, width=w, height=h, bg=COLOR_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=12, pady=12, columnspan=1)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        # controls
        ctrl = tk.Frame(self, bg=COLOR_BG)
        ctrl.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

        tk.Label(ctrl, text="Algorithm: Dijkstra", fg=COLOR_TEXT, bg=COLOR_BG,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        self.btn_run = ttk.Button(ctrl, text="Run", command=self.run)
        self.btn_run.pack(fill="x", pady=4)

        ttk.Button(ctrl, text="Clear Paths", command=self.clear_paths)\
            .pack(fill="x", pady=4)
        ttk.Button(ctrl, text="Clear All", command=self.clear_all)\
            .pack(fill="x", pady=4)
        ttk.Button(ctrl, text="Random Maze", command=self.random_maze)\
            .pack(fill="x", pady=4)

        tk.Label(ctrl, text="Speed", fg=COLOR_TEXT, bg=COLOR_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.speed = tk.DoubleVar(value=0.5)
        tk.Scale(ctrl, from_=0.05, to=1.0, resolution=0.05,
                 orient="horizontal", variable=self.speed,
                 showvalue=True, length=170, bg=COLOR_BG, fg=COLOR_TEXT,
                 highlightthickness=0, troughcolor="#334155").pack(anchor="w")

        tk.Label(ctrl, text="\nLeft-click: Wall | Right-click: Start → End → Clear",
                 fg=COLOR_TEXT, bg=COLOR_BG, justify="left", wraplength=180).pack(anchor="w")

        self.draw_grid()
        self.running = False
        self.after_id = None

    # ---------- drawing ----------
    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(self.g.rows):
            for c in range(self.g.cols):
                x0 = PADDING + c * CELL
                y0 = PADDING + r * CELL
                x1 = x0 + CELL - 1
                y1 = y0 + CELL - 1
                rect = self.canvas.create_rectangle(
                    x0, y0, x1, y1, outline=COLOR_GRID, width=1, fill=COLOR_BG
                )
                self.g.cells[r][c].rect = rect

    def paint(self, r, c, color):
        self.canvas.itemconfig(self.g.cells[r][c].rect, fill=color)

    def redraw_all(self):
        for r in range(self.g.rows):
            for c in range(self.g.cols):
                cell = self.g.cells[r][c]
                col = COLOR_BG
                if cell.wall: col = COLOR_WALL
                if cell.start: col = COLOR_START
                if cell.end: col = COLOR_END
                self.paint(r, c, col)

    # ---------- mouse ----------
    def grid_at(self, event):
        c = (event.x - PADDING) // CELL
        r = (event.y - PADDING) // CELL
        if 0 <= r < self.g.rows and 0 <= c < self.g.cols:
            return r, c
        return None

    def on_left_click(self, e):
        pos = self.grid_at(e)
        if not pos or self.running: return
        r, c = pos
        cell = self.g.cells[r][c]
        if cell.start or cell.end: return
        cell.wall = not cell.wall
        self.paint(r, c, COLOR_WALL if cell.wall else COLOR_BG)

    def on_drag(self, e):
        self.on_left_click(e)

    def on_right_click(self, e):
        pos = self.grid_at(e)
        if not pos or self.running: return
        r, c = pos
        cell = self.g.cells[r][c]
        if cell.wall: return

        # cycle: empty -> start -> end -> empty
        if not cell.start and not cell.end:
            if self.g.start is None:
                cell.start = True; self.g.start = (r, c); self.paint(r, c, COLOR_START)
            elif self.g.end is None:
                cell.end = True; self.g.end = (r, c); self.paint(r, c, COLOR_END)
        elif cell.start:
            cell.start = False; self.g.start = None; self.paint(r, c, COLOR_BG)
        elif cell.end:
            cell.end = False; self.g.end = None; self.paint(r, c, COLOR_BG)

    # ---------- controls ----------
    def clear_paths(self):
        if self.running: return
        for r in range(self.g.rows):
            for c in range(self.g.cols):
                if not (self.g.cells[r][c].wall or self.g.cells[r][c].start or self.g.cells[r][c].end):
                    self.paint(r, c, COLOR_BG)

    def clear_all(self):
        if self.running: return
        for r in range(self.g.rows):
            for c in range(self.g.cols):
                cell = self.g.cells[r][c]
                cell.wall = cell.start = cell.end = False
        self.g.start = self.g.end = None
        self.redraw_all()

    def random_maze(self):
        if self.running: return
        self.clear_all()
        for r in range(self.g.rows):
            for c in range(self.g.cols):
                if random.random() < WALL_RATE:
                    self.g.cells[r][c].wall = True
        self.redraw_all()

    # ---------- run Dijkstra ----------
    def run(self):
        if self.running: return
        if not self.g.start or not self.g.end:
            messagebox.showinfo("Info", "Right-click to set Start and End first.")
            return
        self.clear_paths()
        self.running = True
        self.visualize_dijkstra()

    def finish(self):
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def schedule(self, fn, delay=None):
        delay_ms = int(120 * (1.05 - float(self.speed.get()))) if delay is None else delay
        self.after_id = self.after(delay_ms, fn)

    # ---------- Dijkstra ----------
    def visualize_dijkstra(self):
        start = self.g.start; goal = self.g.end
        dist = {start: 0}
        prev = {}
        pq = [(0, start)]
        visited = set()

        def step():
            if not pq:
                self.finish()
                messagebox.showinfo("Result", "No path found.")
                return

            d, u = heapq.heappop(pq)
            if u in visited:
                return self.schedule(step)
            visited.add(u)

            r, c = u
            if u != start and u != goal:
                self.paint(r, c, COLOR_CLOSED)

            if u == goal:
                p = u; length = 0
                while p in prev:
                    pr, pc = p
                    if p != goal and p != start:
                        self.paint(pr, pc, COLOR_PATH)
                    p = prev[p]; length += 1
                self.finish()
                messagebox.showinfo("Result", f"Dijkstra — Path length: {length}")
                return

            for nr, nc in self.g.neighbors4(r, c):
                v = (nr, nc)
                nd = d + 1
                if nd < dist.get(v, 1e18):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
                    if v != start and v != goal:
                        self.paint(nr, nc, COLOR_OPEN)

            self.schedule(step)

        step()

# -------------------- MAIN --------------------
if __name__ == "__main__":
    try:
        from ttkthemes import ThemedStyle
        has_theme = True
    except Exception:
        has_theme = False

    app = App()
    if has_theme:
        style = ThemedStyle(app)
        style.set_theme("adapta")
    app.mainloop()
