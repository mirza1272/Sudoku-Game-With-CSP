# ============================================================
#  Sudoku Solver using CSP (Constraint Satisfaction Problem)
#  Techniques: Backtracking + Forward Checking + AC-3
# ============================================================

import copy

# --------------- Global Counters ---------------
backtrack_calls = 0   # how many times backtrack() is called
failures = 0          # how many times we hit a dead end


# ============================================================
#  SECTION 1: Reading the board from a file
# ============================================================

def read_board(filename):
    """
    Read a 9x9 Sudoku board from a text file.
    Each line has 9 digits; 0 means the cell is empty.
    Returns a 9x9 list of integers.
    """
    board = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:                          # skip blank lines
                row = [int(ch) for ch in line]
                board.append(row)
    return board


# ============================================================
#  SECTION 2: CSP Representation
# ============================================================
# We represent the Sudoku puzzle as a CSP where:
#   - Variables  : every cell (row, col)  → 81 variables
#   - Domain     : digits 1-9 for empty cells, {given digit} for filled cells
#   - Constraints: no two cells in the same row / column / 3×3 box share
#                  the same digit

def build_domains(board):
    """
    Build the initial domain (set of possible values) for every cell.
    - If the cell is already filled (non-zero), its domain is just that digit.
    - If the cell is empty (0), its domain is {1, 2, ..., 9}.
    Returns a 9×9 list of sets.
    """
    domains = []
    for r in range(9):
        row_domains = []
        for c in range(9):
            if board[r][c] != 0:
                row_domains.append({board[r][c]})   # fixed digit
            else:
                row_domains.append(set(range(1, 10)))  # all digits possible
        domains.append(row_domains)
    return domains


def get_peers(row, col):
    """
    Return a list of all cells that share a constraint with (row, col).
    A 'peer' is any cell in the same row, column, or 3×3 box.
    """
    peers = set()

    # Same row
    for c in range(9):
        if c != col:
            peers.add((row, c))

    # Same column
    for r in range(9):
        if r != row:
            peers.add((r, col))

    # Same 3×3 box
    box_row = (row // 3) * 3   # top-left corner of the box
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if (r, c) != (row, col):
                peers.add((r, c))

    return list(peers)


# Pre-compute peers for every cell (this speeds things up)
PEERS = {}
for r in range(9):
    for c in range(9):
        PEERS[(r, c)] = get_peers(r, c)


# ============================================================
#  SECTION 3: AC-3 Algorithm (Arc Consistency)
# ============================================================
# AC-3 removes values from domains that cannot possibly be correct.
# An "arc" (Xi → Xj) is consistent if, for every value in Xi's domain,
# there exists at least one value in Xj's domain that does not conflict.
# For Sudoku the constraint is simply: Xi ≠ Xj.

def ac3(domains):
    """
    Run the AC-3 algorithm to reduce domains before/during search.
    Modifies 'domains' in place.
    Returns False if any domain becomes empty (puzzle is unsolvable from
    this state), True otherwise.
    """
    # Start with every arc in the puzzle
    queue = []
    for r in range(9):
        for c in range(9):
            for (pr, pc) in PEERS[(r, c)]:
                queue.append(((r, c), (pr, pc)))

    while queue:
        (xi_r, xi_c), (xj_r, xj_c) = queue.pop(0)

        # Try to make arc (Xi → Xj) consistent
        if revise(domains, xi_r, xi_c, xj_r, xj_c):
            # Xi's domain shrank — check if it's now empty
            if len(domains[xi_r][xi_c]) == 0:
                return False   # dead end

            # Xi changed, so re-check all arcs pointing TO Xi
            for (pr, pc) in PEERS[(xi_r, xi_c)]:
                if (pr, pc) != (xj_r, xj_c):
                    queue.append(((pr, pc), (xi_r, xi_c)))

    return True   # all arcs are consistent


def revise(domains, xi_r, xi_c, xj_r, xj_c):
    """
    Remove values from domains[xi_r][xi_c] that have no valid match in
    domains[xj_r][xj_c].
    For Sudoku: a value v in Xi is valid as long as Xj still has at least
    one value different from v.
    Returns True if we removed anything, False otherwise.
    """
    revised = False
    to_remove = set()

    for v in domains[xi_r][xi_c]:
        # Is there any value in Xj's domain that is different from v?
        if all(w == v for w in domains[xj_r][xj_c]):
            # The only option in Xj is the same as v → conflict
            to_remove.add(v)
            revised = True

    domains[xi_r][xi_c] -= to_remove
    return revised


# ============================================================
#  SECTION 4: Forward Checking
# ============================================================
# After we assign a digit to a cell, forward checking immediately removes
# that digit from the domains of all peers.  This catches failures early.

def forward_check(domains, row, col, value):
    """
    Remove 'value' from the domains of every peer of (row, col).
    Returns False if any peer's domain becomes empty (dead end),
    True otherwise.
    Also returns the list of (cell, value) pairs we pruned so we can
    undo them later (backtracking).
    """
    pruned = []   # track what we removed so we can undo

    for (pr, pc) in PEERS[(row, col)]:
        if value in domains[pr][pc]:
            domains[pr][pc].remove(value)
            pruned.append((pr, pc, value))

            if len(domains[pr][pc]) == 0:
                return False, pruned   # a peer has no options left

    return True, pruned


def undo_pruning(domains, pruned):
    """
    Restore all values that were removed by forward checking.
    Called when we backtrack.
    """
    for (pr, pc, value) in pruned:
        domains[pr][pc].add(value)


# ============================================================
#  SECTION 5: Backtracking Search
# ============================================================

def select_unassigned_variable(domains, board):
    """
    Choose the next empty cell to try.
    We use the MRV (Minimum Remaining Values) heuristic:
    pick the empty cell with the FEWEST values still in its domain.
    This reduces the branching factor and finds failures sooner.
    """
    min_size = 10        # anything bigger than 9
    best_cell = None

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:   # empty cell
                size = len(domains[r][c])
                if size < min_size:
                    min_size = size
                    best_cell = (r, c)

    return best_cell   # None if board is fully assigned


def backtrack(board, domains):
    """
    The main recursive backtracking function.
    Returns True if the puzzle is solved, False if we hit a dead end.
    """
    global backtrack_calls, failures
    backtrack_calls += 1

    # --- Base case: is the board completely filled? ---
    cell = select_unassigned_variable(domains, board)
    if cell is None:
        return True   # every cell is assigned → solved!

    row, col = cell

    # --- Try each value in the domain of this cell ---
    for value in sorted(domains[row][col]):   # sorted for determinism

        # Tentatively place 'value'
        board[row][col] = value

        # Save a snapshot of the domain for this cell, then set it to {value}
        saved_domain = domains[row][col].copy()
        domains[row][col] = {value}

        # Forward checking: remove 'value' from peers' domains
        ok, pruned = forward_check(domains, row, col, value)

        if ok:
            # Recurse deeper
            result = backtrack(board, domains)
            if result:
                return True   # solution found!

        # --- Dead end — undo and try the next value ---
        failures += 1
        board[row][col] = 0
        domains[row][col] = saved_domain
        undo_pruning(domains, pruned)

    # No value worked for this cell
    return False


# ============================================================
#  SECTION 6: Printing the Board
# ============================================================

def print_board(board, title=""):
    """
    Print the Sudoku board in a nice grid format.
    """
    if title:
        print(f"\n{'='*37}")
        print(f"  {title}")
        print(f"{'='*37}")

    print("  +---------+---------+---------+")
    for r in range(9):
        if r > 0 and r % 3 == 0:
            print("  +---------+---------+---------+")
        row_str = "  |"
        for c in range(9):
            val = board[r][c]
            cell = str(val) if val != 0 else "."
            row_str += f" {cell}"
            if c % 3 == 2:
                row_str += " |"
        print(row_str)
    print("  +---------+---------+---------+")


# ============================================================
#  SECTION 7: Main Solver Function
# ============================================================

def solve(filename):
    """
    Read a puzzle from 'filename', solve it, and print the results.
    """
    global backtrack_calls, failures
    backtrack_calls = 0   # reset counters for each puzzle
    failures = 0

    print(f"\n{'#'*37}")
    print(f"  Solving: {filename}")
    print(f"{'#'*37}")

    # Step 1 – Read the board
    board = read_board(filename)
    print_board(board, "Puzzle (input)")

    # Step 2 – Build CSP domains
    domains = build_domains(board)

    # Step 3 – Run AC-3 first to prune domains
    possible = ac3(domains)
    if not possible:
        print("  ✗ AC-3 detected no solution exists!")
        return

    # Step 4 – Backtracking with forward checking
    solved = backtrack(board, domains)

    # Step 5 – Show results
    if solved:
        print_board(board, "Solution (output)")
        print(f"\n  ✓ Solved successfully!")
    else:
        print("  ✗ No solution found.")

    print(f"  Backtrack calls : {backtrack_calls}")
    print(f"  Failures        : {failures}")


# ============================================================
#  SECTION 8: Entry Point
# ============================================================

if __name__ == "__main__":
    puzzles = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]

    for puzzle_file in puzzles:
        solve(puzzle_file)

    print(f"\n{'='*37}")
    print("  All puzzles finished!")
    print(f"{'='*37}\n")