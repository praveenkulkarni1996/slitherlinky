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
import logging

class Slitherlinky(object):
    """ Describes a puzzle and any partial solutions """

    def __init__(self):
        self.cells = None
        self.height = None
        self.width = None
        self.num_edges = None
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
        self.num_edges = 2*self.width*self.height + self.width + self.height
        pprint.pprint(self.cells)
        print()

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
            Amongst any two of booleans, at least one must be false. This
            ensures that atmost one of the booleans is true. 
            Also add a clause that ensures at least one of the booleans is true.
            Together they ensure the "exactly one constraint".
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
                    e1, e2, e3, e4 = [1+e for e in self.get_cell_edges(cell_id)]
                    clauses = cnf_builder[cell_value](e1, e2, e3, e4)
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

    def active_dots_ranked_clauses(self):
        """ 
        A dot has a rank iff it is part of an edge.
        Forward clauses ensure that if there is an edge from a corner, then the
        corner has a rank. Backward clauses ensure that if a corner has a rank,
        then it has an edge present.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        forward_clauses = []
        backward_clauses = []
        for dot in range(num_dots):
            adj_edges = self.get_corner_edges(dot)
            for adj_edge in adj_edges:
                forward_clauses += [[-(adj_edge+1), (dot, num_dots)]]
            backward_clauses += [[(dot, -num_dots)] + [1+e for e in adj_edges]]
        return forward_clauses + backward_clauses

    def unique_rank1_dot_clauses(self):
        """
        There can only be a unique dot with a rank 1. Thus amongst any two dots
        with at least one of them will not have rank 1. 
        """
        num_dots = (1 + self.height) * (1 + self.width)
        unique_clauses = []
        for dot1 in range(num_dots):
            for dot2 in range(num_dots):
                if dot1 != dot2:
                    unique_clauses += [[(dot1, -1), (dot2, -1)]]
        return unique_clauses

    def better_ranks_clauses(self):
        """
        About the ranks of a dot. 
        If a dot has a rank better than k, then it has a rank better than
        (k+1) ... n.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        clauses = []
        for dot in range(num_dots):
            for rank in range(1, num_dots + 1):
                for low_rank in range(rank + 1, num_dots + 1):
                    clauses += [[(dot, -rank), (dot, low_rank)]]
        return clauses

    def better_neighbours_clauses(self):
        """
        At least one of the neighbours has a better rank than the current dot.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        clauses = []
        for dot in range(num_dots):
            adj_dots = self.get_adjacent_dots(dot_id=dot)
            for rank in range(2, num_dots + 1):
                clause = [(dot, -rank)] + [(adot, rank-1) for adot in adj_dots]
                clauses += [clause]
        return clauses

    def call_sat_solver(self):
        """
        Moves the variables and constraints to the SAT solver.
        """
        num_dots = (1 + self.height) * (1 + self.width)
        constraints = self.cell_constraints + self.loop_constraints
        new_clauses = []
        new_clauses += self.active_dots_ranked_clauses()
        new_clauses += self.unique_rank1_dot_clauses()
        new_clauses += self.better_ranks_clauses()
        new_clauses += self.better_neighbours_clauses()
        self.dot_rank_to_int = {}
        dot_ranks = [(dot, rank)
                     for dot in range(num_dots)
                     for rank in range(1, num_dots + 1)]
        for i, dot_rank in enumerate(dot_ranks):
            index = 1 + i + self.num_edges
            self.dot_rank_to_int[dot_rank] = index
        compiled_clauses = []
        for clause in new_clauses:
            compiled_clause = []
            for terminal in clause:
                if type(terminal) is tuple:
                    a, b = terminal
                    sign = b // abs(b)
                    terminal = sign * self.dot_rank_to_int[(a, abs(b))]
                compiled_clause.append(terminal)
            compiled_clauses.append(compiled_clause)

        all_clauses = compiled_clauses + constraints
        self.solution = pycosat.solve(constraints + compiled_clauses)

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

    def solve(self, input_filename):
        """ Runs solution pipeline. """
        self.read_puzzle(filename=input_filename)
        self.generate_cell_constraints()
        self.generate_loop_constraints()
        self.call_sat_solver()
        self.interpret_solution()



if __name__ == '__main__':
    slither = Slitherlinky()
    slither.solve(input_filename='tests/mod1.txt')
