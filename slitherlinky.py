"""
Author:     Praveen Kulkarni
Email:      praveenkulkarni1996@gmail.com
Website:    https://www.cse.iitd.ac.in/~cs5140599
File:       slitherlinky.py
Project:    slitherlinky
License:    MIT
"""

import argparse
import pycosat
import logging


class Slitherlinky(object):
    """ Describes a puzzle and any partial solutions """

    def __init__(self):
        self.cells = None
        self.height = None
        self.width = None
        self.cell_constraints = []
        self.loop_constraints = []

    def read_puzzle(self, filename):
        """ reads a puzzle from a file """
        with open(filename) as fin:
            self.cells = [[None if char == '.' else int(char)
                          for char in line.strip()]
                          for line in fin]
        self.width = len(self.cells[0])
        self.height = len(self.cells)

    def generate_cell_constraints(self):
        """
        The cell constraints correspond to the main objective of the game where
        each cell must have as many edges as it's value. The value of each cell
        is amongst [None, 0, 1, 2 3].  These can be expressed using edge
        variables only.
        This updates the self.cell_constraints, and has no other side effects.
        """
        def zero(e1, e2, e3, e4):
            """
            All e1, e2, e3 and e4 must be false.
            """
            logging.debug('zero({}, {}, {}, {})'.format(e1, e2, e3, e4))
            return [[-e1], [-e2], [-e3], [-e4]]

        def one(e1, e2, e3, e4):
            """
            The "exactly one" constraint can be expressed as
            * Amongst any two of booleans, at least one must be false.
            * Atleast one of the booleans is true.
            """
            logging.debug('one({}, {}, {}, {})'.format(e1, e2, e3, e4))
            return [[-e1, -e2], [-e1, -e3], [-e1, -e4],
                    [-e2, -e3], [-e2, -e4], [-e3, -e4],
                    [e1, e2, e3, e4]]

        def two(e1, e2, e3, e4):
            """
            Amongst any three booleans, at least one must be true,
            and atleast one must be false.
            """
            logging.debug('two({}, {}, {}, {})'.format(e1, e2, e3, e4))
            return [[e2, e3, e4], [e1, e3, e4],
                    [e1, e2, e4], [e1, e2, e3],
                    [-e2, -e3, -e4], [-e1, -e3, -e4],
                    [-e1, -e2, -e4], [-e1, -e2, -e3]]

        def three(e1, e2, e3, e4):
            """
            Amongst any two booleans, at least one must be true. This ensures
            that there are at least three true booleans.
            Also add a clause that ensures at least one of them must be false.
            Together they ensure the "exactly three correct"
            """
            logging.debug('three({}, {}, {}, {})'.format(e1, e2, e3, e4))
            return [[e1, e2], [e1, e3], [e1, e4],
                    [e2, e3], [e2, e4], [e3, e4],
                    [-e1, -e2, -e3, -e4]]

        self.cell_constraints = []
        cnf_builder = [zero, one, two, three]
        cell_id = -1
        for row in range(self.height):
            for col in range(self.width):
                cell_id += 1
                cell_value = self.cells[row][col]
                assert cell_value in [None, 0, 1, 2, 3]
                if cell_value is None:
                    pass
                else:
                    assert 0 <= cell_value <= 3
                    edges = [1+e for e in self.get_cell_edges(cell_id)]
                    clauses = cnf_builder[cell_value](*edges)
                    self.cell_constraints += clauses

    def generate_loop_constraints(self):
        """
        The loop constraints ensure that all the edges form loops. They are
        expressed by ensuring that every corner is part of either 0 or 2 edges.
        These can be expressed using the edge variables only.
        This updates the self.loop_constriants, and has no other side effects.
        """

        def two(e1, e2):
            """
            If there are only two edges at a corner, then either both edges are
            true, or both aren't. One edge implies the other.
            """
            return [[-e1, e2], [e1, -e2]]

        def three(e1, e2, e3):
            """
            If there are three edges at a corner, then exactly two of them are
            true, or none of them are.
            * Having two edges implies the other isn't.
            * Having one of the edges implies one of the other is.
            """
            return [[-e1, -e2, -e3],
                    [-e1, e2, e3],
                    [e1, -e2, e3],
                    [e1, e2, -e3]]

        def four(e1, e2, e3, e4):
            """
            If there are four edges at a corner, then exactly two of them are
            true, or none of them are.
            * Having one edge implies one of the other is an edge.
            * Having two edges imples the other two aren't an edge.
            """
            return [[-e1, e2, e3, e4],
                    [e1, -e2, e3, e4],
                    [e1, e2, -e3, e4],
                    [e1, e2, e3, -e4],
                    [-e1, -e2, -e3],
                    [-e1, -e2, -e4],
                    [-e1, -e3, -e4],
                    [-e2, -e3, -e4]]

        num_corners = (self.width + 1) * (self.height + 1)
        constraint_fn = [None, None, two, three, four]
        for corner_id in range(num_corners):
            edges = [1+e for e in self.get_corner_edges(corner_id)]
            clauses = constraint_fn[len(edges)](*edges)
            self.loop_constraints += clauses

    def call_sat_solver(self, verify=False):
        """
        Moves the variables and constraints to the SAT solver.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        constraints = self.cell_constraints + self.loop_constraints
        count = 0
        for solution in pycosat.itersolve(constraints):
            test_solution = [edge for edge in solution if edge > 0]
            result = self.validate(test_solution)
            if result:
                self.solution = test_solution
                count += 1
                if not verify:
                    break
                if count > 1:
                    raise Exception("multiple solutions")

    def get_cell_edges(self, cell_id):
        """
        Returns a list of four integers corresponding to the edges around a
        cell.
        """
        assert 0 <= cell_id < (self.height * self.width)
        # precomputation
        cell_row = cell_id // self.width
        cell_col = cell_id % self.width
        num_horizontal = self.height * (self.width + 1)
        # horizontal edges
        upper_edge = cell_id
        lower_edge = upper_edge + self.width
        # vertical edges
        left_edge = num_horizontal + ((cell_row * (self.width + 1)) + cell_col)
        right_edge = left_edge + 1
        return [upper_edge, lower_edge, left_edge, right_edge]

    def get_corner_edges(self, corner_id):
        """
        Returns a list of 2-4 edge indices corresponding to the edges
        around a cell. The corners are numbered in ascending order from the
        top-left to the bottom-right.
        """
        assert 0 <= corner_id < (self.width + 1) * (self.height + 1)
        col = corner_id % (self.width + 1)
        row = corner_id // (self.width + 1)
        left_edge = None
        right_edge = None
        up_edge = None
        down_edge = None
        H = self.width * (self.height + 1)
        if col < self.width:
            right_edge = (self.width * row) + col
        if col > 0:
            left_edge = (self.width * row) + col - 1
        if row > 0:
            up_edge = H + corner_id - (self.width + 1)
        if row < self.height:
            down_edge = H + corner_id
        edges = [edge
                 for edge in [left_edge, right_edge, up_edge, down_edge]
                 if edge is not None]
        return edges

    def get_adjacent_edges(self, edge_id):
        """
        Returns a list of upto 6 edges that are adjacent to edge_id.
        """
        vert_edges = self.height * (self.width + 1)
        hori_edges = self.width * (self.height + 1)
        num_edges = vert_edges + hori_edges
        num_corners = (self.width + 1) * (self.height + 1)
        assert 0 <= edge_id < num_edges
        a, b = [corner_id
                for corner_id in range(num_corners)
                if edge_id in self.get_corner_edges(corner_id)]
        edges_a = [edge
                   for edge in self.get_corner_edges(a)
                   if edge != edge_id]
        edges_b = [edge
                   for edge in self.get_corner_edges(b)
                   if edge != edge_id]
        return edges_a + edges_b

    def get_adjacent_dots(self, dot_id):
        """
        Returns a list of dots adjacent to a given dot dot_id.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        dot_id_edges = set(self.get_corner_edges(dot_id))
        adjacent_dots = []
        for dot in range(num_dots):
            dot_edges = set(self.get_corner_edges(dot))
            common_edges = dot_edges.intersection(dot_id_edges)
            if len(common_edges) > 0:
                adjacent_dots.append(dot)
        return adjacent_dots

    def solve(self, input_filename=None, verify=False):
        """ Runs solution pipeline. """
        if input_filename is not None:
            self.read_puzzle(filename=input_filename)
        self.generate_cell_constraints()
        self.generate_loop_constraints()
        self.call_sat_solver(verify=verify)
        self.draw_solution()

    def validate(self, solution):
        """ Validates that the generated solution has a single loop """
        if solution is []:
            return False
        solution = [edge - 1 for edge in solution]
        far_edges = solution[1:]
        start = [solution[0]]
        while far_edges != []:
            nbrs = [nbr
                    for edge in start
                    for nbr in self.get_adjacent_edges(edge)
                    if nbr in far_edges]
            if nbrs == [] and far_edges != []:
                return False
            far_edges = [edge for edge in far_edges if edge not in nbrs]
            start = nbrs
        return True

    def draw_solution(self):
        """ Draws the solution in ASCII-art. """
        num_row = 4 * (self.height + 1) + 1
        num_col = 4 * (self.width + 1) + 1
        g = [[' ' for cols in range(num_col)] for rows in range(num_row)]

        def horizontal_edge(edge):
            """ Draw a horizontal edge on the grid. """
            col_f = edge % self.width
            row_l = edge // self.width
            y = 4 * row_l
            x1 = 4 * col_f
            x2 = 4 * (col_f + 1)
            for x in range(x1, x2+1):
                g[y][x] = '#'

        def vertical_edge(edge):
            """ Draw a vertical edge on the grid. """
            row_f = edge // (self.width + 1)
            col_l = edge % (self.width + 1)
            y1 = 4 * row_f
            y2 = 4 * (row_f + 1)
            x = 4 * col_l
            for y in range(y1, y2+1):
                g[y][x] = '#'

        def draw_numbers():
            for row_index, row in enumerate(self.cells):
                for col_index, val in enumerate(row):
                    if val is not None:
                        y = 4 * row_index + 2
                        x = 4 * col_index + 2
                        g[y][x] = str(val)

        draw_numbers()
        horizontal_limit = self.height * (self.width + 1)
        horizontals = [e - 1
                       for e in self.solution
                       if e <= horizontal_limit]
        verticals = [e - horizontal_limit - 1
                     for e in self.solution
                     if e > horizontal_limit]
        for h_edge in horizontals:
            horizontal_edge(edge=h_edge)
        for v_edge in verticals:
            vertical_edge(edge=v_edge)
        gs = '\n'.join([''.join(g_row) for g_row in g])
        print(gs)


def interactive_mode(row, col):
    cells = []
    for row_index in range(row):
        row_list = [int(char) if char.isdigit() else None
                    for char in list(input())]
        if len(row_list) != col:
            raise IOError('column length exceeds {}'.format(col))
        cells.append(row_list)
    return cells


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', 
            help='Specify input filename. By default reads interactively')
    parser.add_argument('-r', '--row',
            help='Number of rows in grid for interactive mode.',
            type=int)
    parser.add_argument('-c', '--col',
            help='Number of columns in grid for interactive mode.',
            type=int)
    parser.add_argument('-v', '--verify',
            help='Verify that there is only one solution.',
            action='store_true')
    args = parser.parse_args()
    slither = Slitherlinky()
    if args.file is not None:
        slither.solve(input_filename=args.file, verify=args.verify)
    else:
        if args.row is None or args.col is None:
            raise IOError('row and col must be specified in interactive mode')
        cells = interactive_mode(args.row, args.col)
        slither.cells = cells
        slither.height = args.row
        slither.width = args.col
        slither.solve()
