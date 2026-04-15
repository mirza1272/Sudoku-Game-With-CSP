backtrack_calls = 0
failures = 0
def read_puzzle(filename):
    board = []
    file = open(filename, "r")
    for line in file:
        line = line.strip()
        if line == "":
            continue
        row = []
        for ch in line:
            row.append(int(ch))
        board.append(row)
    file.close()
    return board
def print_board(board):
    print("+-------+-------+-------+")
    for i in range(9):
        row_str = "| "
        for j in range(9):
            val = board[i][j]
            if val == 0:
                row_str += ". "
            else:
                row_str += str(val) + " "
            if j == 2 or j == 5:
                row_str += "| "
        row_str += "|"
        print(row_str)
        if i == 2 or i == 5:
            print("+-------+-------+-------+")
    print("+-------+-------+-------+")
def setup_domains(board):
    domains = {}
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                domains[(i, j)] = set(range(1, 10))
            else:
                domains[(i, j)] = set([board[i][j]])
    return domains
def get_neighbors(row, col):
    neighbors = set()
    for j in range(9):
        if j != col:
            neighbors.add((row, j))
    for i in range(9):
        if i != row:
            neighbors.add((i, col))
    box_row = (row // 3) * 3  
    box_col = (col // 3) * 3
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if (i, j) != (row, col):
                neighbors.add((i, j))

    return neighbors
def get_all_arcs():
    arcs = []
    for i in range(9):
        for j in range(9):
            for neighbor in get_neighbors(i, j):
                arcs.append(((i, j), neighbor))
    return arcs
def ac3(domains):
    queue = get_all_arcs()
    while len(queue) > 0:
        arc = queue.pop(0)
        xi = arc[0]
        xj = arc[1]
        if revise(domains, xi, xj):
            if len(domains[xi]) == 0:
                return False
            for xk in get_neighbors(xi[0], xi[1]):
                if xk != xj:
                    queue.append((xk, xi))
            for xk in get_neighbors(xi[0], xi[1]):
                if xk != xj:
                    queue.append((xk, xi))

    return True
def revise(domains, xi, xj):
    revised = False
    values_to_remove = []
    for val in domains[xi]:
        has_support = False
        for other_val in domains[xj]:
            if other_val != val:
                has_support = True
                break
        if not has_support:
            values_to_remove.append(val)
            revised = True
    for val in values_to_remove:
        domains[xi].remove(val)

    return revised
def forward_check(domains, cell, value):
    row, col = cell
    for neighbor in get_neighbors(row, col):
        if value in domains[neighbor]:
            domains[neighbor].remove(value)
            if len(domains[neighbor]) == 0:
                return False

    return True
def pick_unassigned(board, domains):
    best_cell = None
    best_count = 10 
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:  
                count = len(domains[(i, j)])
                if count < best_count:
                    best_count = count
                    best_cell = (i, j)

    return best_cell

def is_consistent(board, row, col, value):
    for j in range(9):
        if board[row][j] == value:
            return False
    for i in range(9):
        if board[i][col] == value:
            return False
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if board[i][j] == value:
                return False

    return True
def copy_domains(domains):
    new_domains = {}
    for key in domains:
        new_domains[key] = set(domains[key])  
    return new_domains
def backtrack(board, domains):
    global backtrack_calls, failures
    backtrack_calls += 1
    cell = pick_unassigned(board, domains)
    if cell is None:
        return True
    row, col = cell
    for value in sorted(domains[(row, col)]):
        if is_consistent(board, row, col, value):
            board[row][col] = value
            saved_domains = copy_domains(domains)
            domains[(row, col)] = set([value])
            if forward_check(domains, (row, col), value):
                if backtrack(board, domains):
                    return True  
            board[row][col] = 0
            failures += 1
            for key in saved_domains:
                domains[key] = saved_domains[key]
    return False

def solve_puzzle(filename):
    global backtrack_calls, failures
    backtrack_calls = 0
    failures = 0
    print("=" * 41)
    print("  Solving: " + filename)
    print("=" * 41)
    board = read_puzzle(filename)
    print("\nOriginal Puzzle:")
    print_board(board)
    domains = setup_domains(board)
    print("\nRunning AC-3 (Arc Consistency)...")
    ac3_result = ac3(domains)
    if not ac3_result:
        print("AC-3 found no solution possible!")
        return
    ac3_solved = 0
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0 and len(domains[(i, j)]) == 1:
                ac3_solved += 1
    print("AC-3 reduced " + str(ac3_solved) + " cell(s) to one value.")
    print("\nRunning Backtracking with Forward Checking...")
    solved = backtrack(board, domains)
    if solved:
        print("\nSolved Puzzle:")
        print_board(board)
    else:
        print("\nNo solution found!")
    print("\n--- Statistics ---")
    print("Backtracking calls: " + str(backtrack_calls))
    print("Failures (backtracks): " + str(failures))
    print()

# if __name__ == "__main__":
puzzle_files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]
for puzzle in puzzle_files:
    solve_puzzle(puzzle)