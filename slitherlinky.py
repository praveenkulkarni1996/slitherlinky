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


class Slitherlinky(object):
    """ Describes a puzzle and any partial solutions """

    def __init__(self):
        self.cells = None
        self.height = None
        self.width = None
        self.cell_constraints = []
        self.loop_constriants = []
        self.single_loop_constraints = []


    def read_puzzle(self, filename):
        """ reads a puzzle from a file """
        self.cells = [[3, 3]] #TODO: read from file instead of the mockup
        self.width = 2
        self.height = 1

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
                if 0 <= cell_value <= 3:
                    e1, e2, e3, e4 = [1+e for e in self.get_cell_edges(cell_id)]
                    clauses = cnf_builder[cell_value](e1, e2, e3, e4)
                    self.cell_constraints += clauses
                cell_id += 1
        print(self.cell_constraints)

    def generate_loop_constraints(self):
        """
        The loop constraints ensure that all the edges form loops. They are
        expressed by ensuring that every corner is part of either 0 or 2 edges.
        These can be expressed using the edge variables only.
        This updates the self.loop_constriants, and has no other side effects.
        """
        pass

    def generate_single_loop_constraints(self):
        """
        Ensures that the solution consists of a single loop only. This requires
        the use of connected variables.  The connected predicate is defined
        recursively.  Two edges are connected iff
        1) they are adjacent
        2), or if any of the adjacent edges are adjacent
        This function updates the self.single_loop_constriants.
        """
        pass

    def call_sat_solver(self):
        """
        Moves the variables and constraints to the SAT solver.
        """
        print(self.cell_constraints)
        print(pycosat.solve(self.cell_constraints))
        pass

    def interpret_solution(self):
        """
        Interprets the SAT output (= boolean variables) and generates a
        solution.
        """
        pass

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
        row = corner_id % (self.width + 1)
        col = corner_id % (self.width + 1)
        lt_edge = None
        rt_edge = None
        up_edge = None
        dn_edge = None
        H = self.width * (self.height + 1)
        if col < self.width:
            right_edge = (self.width * row) + col
        if col > 0:
            left_edge = (self.width * row) + col - 1
        if row > 0:
            up_edge = H + corner_id - (width + 1)
        if row < self.height:
            down_edge = H + corner_id
        edges = [edge
                 for edge in [left_edge, right_edge, up_edge, down_edge]
                 if edge]
        return edges

    def get_adjacent_edges(self, edge_id):
        """
        Returns a list of upto 6 edges that are adjacent to edge_id.
        """
        n = self.width * self.height
        a, b = None
        for corner_id in range(n):
            if edge_id in self.get_corner_edges(corner_id):
                if a == None:
                    a = corner_id
                else:
                    b = corner_id
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
        raise NotImplemented("None of the functions are ready")


if __name__ == '__main__':
    slither = Slitherlinky()
    slither.solve()
