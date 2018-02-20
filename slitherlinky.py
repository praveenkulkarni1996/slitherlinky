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
import pprint

class Slitherlinky(object):
    """ Describes a puzzle and any partial solutions """

    def __init__(self):
        self.cells = None
        self.height = None
        self.width = None
        self.cell_constraints = []
        self.loop_constraints = []
        self.single_loop_constraints = []

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
            return [[-e1], [-e2], [-e3], [-e4]]

        def one(e1, e2, e3, e4):
            """
            Amongst any two of booleans, at least one must be false. This
            ensures that atmost one of the booleans is true. 
            Also add a clause that ensures at least one of the booleans is true.
            Together they ensure the "exactly one constraint".
            """
            return [[-e1, -e2], [-e1, -e3], [-e1, -e4],
                    [-e2, -e3], [-e2, -e4], [-e3, -e4], 
                    [e1, e2, e3, e4]]

        def two(e1, e2, e3, e4):
            """
            Amongst any three booleans, at least one must be true, 
            and atleast one must be false.
            """
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
            return [[e1, e2], [e1, e3], [e1, e4],
                    [e2, e3], [e2, e4], [e3, e4], 
                    [-e1, -e2, -e3, -e4]]

        self.cell_constraints = []
        cnf_builder = [zero, one, two, three]
        cell_id = 0
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.cells[row][col]
                if cell_value is None:
                    pass
                else:
                    e1, e2, e3, e4 = [1+e for e in self.get_cell_edges(cell_id)]
                    clauses = cnf_builder[cell_value](e1, e2, e3, e4)
                    self.cell_constraints += clauses
                cell_id += 1

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

    def generate_single_loop_constraints(self):
        """
        Ensures that the solution consists of a single loop only. This requires
        the use of connected variables.  The connected predicate is defined
        recursively.  Two edges are connected iff
        1) they are adjacent
        2), or if any of the adjacent edges are adjacent
        This function updates the self.single_loop_constriants.
        """
        def adjacent_clauses(e1, e2, c12):
            """ 
            c12 is the connected variable, which is defined as below:
            * If e1 and e2 are true then it implies c12.
            * If the c12 is true then it implies e1 and e2.
            """
            return [[-e1, -e2, c12], [-c12, e1], [-c12, e2]]

        def non_adjacent_clause(e1, e2, c12, adj_c):
            """
            e1 : source edge present ?
            e2 : destination edge present ?
            c12 : e1 and e2 are connected ?
            adj_c: List of c(1, j) where e1 and ej are neighbours.

            The recursive definition of c12 can be split into two sets of
            clauses - forward and backward clauses.
            * Forward clauses ensure that if a neighbour of e1 is connected to
              e2, and if edge e1 and e2 exist, then e1 is connected to e2.
            * Backward clauses ensure that if e1 is connected to e2, then both 
              e1 and e2 are present, and atleast one of the neighbours of e1 is
              also connected.
            """
            forward_clauses = [[-nc, -e1, -e2, c12] for nc in adj_c]
            backward_clauses = [[-c12, e1], [-c12, e2], [-c12] + adj_c]
            return forward_clauses + backward_clauses

        def get_c(edge1, edge2):
            return num_edges + 1 + c_vars.index((edge1, edge2))

        num_edges = (2 * self.width * self.height) + self.width + self.height

        c_vars = sorted([(a, b) 
                  for a in range(num_edges)
                  for b in range(num_edges)
                  if a != b])

        for e1 in range(num_edges):
            adj = self.get_adjacent_edges(e1)
            adj_c = [get_c(e1, e2) for e2 in adj]
            for e2 in range(num_edges):
                if e1 != e2:
                    c12 = get_c(e1, e2)
                    if e2 in adj:
                        clauses = adjacent_clauses(e1+1, e2+1, c12) 
                    else:
                        clauses = non_adjacent_clause(e1+1, e2+1, c12, adj_c)
                    self.single_loop_constraints += clauses

    def call_sat_solver(self):
        """
        Moves the variables and constraints to the SAT solver.
        """
        constraints = self.cell_constraints + self.loop_constraints + self.single_loop_constraints
        self.solution = pycosat.solve(constraints)

    def interpret_solution(self):
        """
        Interprets the SAT output (= boolean variables) and generates a
        solution.
        """
        num_hori_edges = self.width * (self.height + 1)
        num_vert_edges = self.height * (self.width + 1) 
        num_edges = num_vert_edges + num_hori_edges
        hori_edges = self.solution[:num_hori_edges]
        vert_edges = self.solution[num_hori_edges:num_edges]

        print(list(filter(lambda x: x > 0, hori_edges)))
        print(list(filter(lambda x: x > 0, vert_edges)))
        exit()
        H = 2 * (self.height + 1) + 1
        W = 2 * (self.width + 1) + 1
        outputs = [[' ' for _ in range(W)] for _ in range(H)]
        pprint.pprint(outputs)

        for row in range(self.height + 1):
            print(row)
            start_slice = row * (self.width + 1)
            end_slice = (row + 1) * (self.width + 1)
            solution_row = hori_edges[start_slice:end_slice]
            for pos, value in enumerate(solution_row):
                if value > 0:
                    outputs[row * 2][pos*2 + 0] = '.'
                    outputs[row * 2][pos*2 + 1] = '-'
                    outputs[row * 2][pos*2 + 2] = '.'

        for col in range(self.width + 1):
            start_slice = col * (self.height + 1)
            end_slice = (col + 1) * (self.height + 1)
            solution_col = vert_edges[start_slice:end_slice]
            for pos, value in enumerate(solution_col):
                if value > 0:
                    outputs[pos*2 + 0][col * 2] = '.'
                    outputs[pos*2 + 1][col * 2] = '|'
                    outputs[pos*2 + 2][col * 2] = '.'
        for line in outputs:
            print(''.join(line))
        # pprint.pprint(outputs)
        exit()

        print(hori_edges)
        print(vert_edges)
        # print(list(filter(lambda x: x > 0, self.solution[:num_edges])))

    def get_cell_edges(self, cell_id):
        """
        Returns a list of four integers corresponding to the edges around a
        cell.
        """
        assert 0 <= cell_id < (self.height * self.width)
        # precomputation
        cell_row = int(cell_id / self.width)
        cell_col = cell_id % self.width
        num_horizontal = self.width * (self.height + 1)
        # horizontal edges
        upper_edge = cell_id
        lower_edge = upper_edge + self.width
        # vertical edges
        left_edge = num_horizontal + ((cell_row * self.width) + cell_col)
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
        row = int(corner_id / (self.width + 1))
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

    def solve(self, input_filename=None):
        """ Runs solution pipeline. """
        self.read_puzzle(filename=input_filename)
        self.generate_cell_constraints()
        self.generate_loop_constraints()
        self.generate_single_loop_constraints()
        self.call_sat_solver()
        self.interpret_solution()


if __name__ == '__main__':
    slither = Slitherlinky()
    slither.solve(input_filename='tests/mod1.txt')
