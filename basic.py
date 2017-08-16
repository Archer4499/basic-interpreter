#!/usr/bin/env python3

import operator
import sys
import re

__author__ = "Derek King"


class StatementError(Exception):
    pass


class VariableError(Exception):
    pass


class EvalError(Exception):
    pass


def lookup(var, var_dict):
    """
    :param var: either a variable name or an int
    :param var_dict: (dict of var_name: value): Dict of current variables and values
    :return: value of var or int
    :raises VariableError: if var is either not a valid variable name or an int
    """
    if var in var_dict:
        value = var_dict[var]
    else:
        try:
            value = int(var)
        except ValueError:
            raise VariableError
    return value


def evaluate(exp, var_dict):
    """
    :param exp: [value, "+"|"-"|"*"|"/"|"%"|"^"|"=="|">"|"<"|">="|"<="|"!=", value]
    :param var_dict: (dict of var_name: value): Dict of current variables and values
    :return: value
    :raises EvalError: if given operator is not valid
    :raises VariableError: if var lookup fails
    """
    # String operations work for all except "-"
    operators = {"+": operator.add,  "-": operator.sub,
                 "*": operator.mul,  "/": operator.floordiv,
                 "%": operator.mod,  "^": operator.pow,
                 "==": operator.eq,  ">": operator.gt,
                 "<": operator.lt,  ">=": operator.ge,
                 "<=": operator.le, "!=": operator.ne}

    if len(exp) is not 3:
        raise EvalError

    try:
        value1 = lookup(exp[0], var_dict)
        value2 = lookup(exp[2], var_dict)
    except:
        raise

    if exp[1] in operators:
        # int() allows == and > operators to evaluate to 1 or 0
        result = int(operators[exp[1]](value1, value2))
    else:
        raise EvalError
    return result


class Statements:
    def __init__(self):
        """
        A class containing all valid statements
        """
        pass

    class REM:
        def __init__(self, data):
            """
            :param data: [comment string]
            """
            self.comment = data[0]

        @staticmethod
        def run(_):
            return None, None

    class LET:
        def __init__(self, data):
            """
            :param data: [variable, "=", expression]
            :raises StatementError: If content of statement is invalid
            """
            if len(data) is not 5:
                raise StatementError
            self.variable = data[0]
            if data[1] != "=":
                raise StatementError
            self.expression = data[2:]

        def run(self, var_dict):
            """
            :param var_dict: (dict of var_name: value): Dict of current variables and values
            :return: None, tuple of var_name: value
            :raises VariableError: if var lookup fails
            """
            if self.variable[0].isdigit():
                raise VariableError

            try:
                result = evaluate(self.expression, var_dict)
            except:
                raise
            return None, (self.variable, result)

    class GOTO:
        def __init__(self, data):
            """
            :param data: [value]
            :raises StatementError: If content of statement is invalid
            """
            if len(data) is not 1:
                raise StatementError
            self.value = data[0]

        def run(self, var_dict):
            """
            :param var_dict: (dict of var_name: value): Dict of current variables and values
            :return: line number of GOTO target, None
            :raises VariableError: if var lookup fails
            """
            try:
                value = lookup(self.value, var_dict)
            except:
                raise
            return value, None

    class PRINT:
        def __init__(self, data):
            """
            :param data: [value]
            :raises StatementError: If content of statement is invalid
            """
            if len(data) is not 1:
                raise StatementError
            self.value = data[0]

        def run(self, var_dict):
            """
            :param var_dict: (dict of var_name: value): Dict of current variables and values
            :return: None, None
            :raises VariableError: if var lookup fails
            """
            try:
                value = lookup(self.value, var_dict)
            except:
                raise
            print(value)
            return None, None

    class IF:
        def __init__(self, data):
            """
            :param data: [expression, "GOTO", value]
            :raises StatementError: If content of statement is invalid
            """
            if len(data) is not 5:
                raise StatementError
            self.expression = data[0:3]
            if data[3] != "GOTO":
                raise StatementError
            self.value = data[4]

        def run(self, var_dict):
            """
            :param var_dict: (dict of var_name: value): Dict of current variables and values
            :return: line number of GOTO target, None
            :raises VariableError: if var lookup fails
            """
            try:
                if evaluate(self.expression, var_dict):
                    value = lookup(self.value, var_dict)
                else:
                    value = None
            except:
                raise
            return value, None


class Line:
    def __init__(self, string):
        """
        Contains the line number and an instance of a statement class of a line of BASIC
        :param string: A line of BASIC code
        """
        # Allow quoted strings
        self.content = re.findall(r"([^\s\"]+|\".*?\")", string)

        if self.content[0].isdigit():
            self.line_no = int(self.content[0])
        else:
            print("The line containing \"" + string.strip() + "\" does not have a valid line number")
            sys.exit(1)

        # Searches the Statements class for a class with the same name as the given statement
        StatementClass = getattr(Statements, self.content[1])
        if StatementClass:
            try:
                self.statement = StatementClass(self.content[2:])
            except StatementError:
                print("Error parsing statement on line:", self.line_no)
                sys.exit(1)
        else:
            print("Invalid statement name on line:", self.line_no)
            sys.exit(1)

    def __str__(self):
        return " ".join(self.content)

    def run(self, var_dict):
        """
        :param var_dict: (dict of var_name: value): Dict of current variables and values
        :return: line number of GOTO target, tuple of var_name: value
        """
        try:
            return self.statement.run(var_dict)
        except VariableError:
            print("Invalid variable name on line:", self.line_no)
            sys.exit(1)
        except EvalError:
            print("Error evaluating expression on line:", self.line_no)
            sys.exit(1)


def parse_input(data):
    """
    :param data: Raw BASIC code
    :return: (dict of line_no: Line): Parsed BASIC code
    """
    parsed_dict = dict()
    for line in data:
        line = line.strip()
        if line:  # Ignore blank lines
            curr_line = Line(line)
            if curr_line.line_no not in parsed_dict:
                parsed_dict[curr_line.line_no] = curr_line
            else:
                print("Multiple lines with same line number:", curr_line.line_no)
                sys.exit(1)
    return parsed_dict


def run_code(code_dict):
    """
    Tells each line of code to run in order of line number with GOTO handling
    :param code_dict: (dict of line_no: Line): Parsed BASIC code
    """
    var_dict = dict()
    index = sorted(code_dict.keys())
    i = 0
    while i < len(index):
        new_line, new_var = code_dict[index[i]].run(var_dict)
        if new_var:
            var_dict[new_var[0]] = new_var[1]
        if new_line is not None:
            try:
                i = index.index(new_line)
            except ValueError:
                print("Invalid GOTO target on line:", code_dict[index[i]].line_no)
                sys.exit(1)
        else:
            i += 1


def print_code_inorder(code_dict):
    """
    Prints the given BASIC code ordered by line numbers
    :param code_dict: (dict of line_no: Line): Parsed BASIC code
    """
    print("## BASIC Code ##")
    for key in sorted(code_dict.keys()):
        print(code_dict[key])
    print("## END ##")


if __name__ == '__main__':
    # Exits with:
    #   0 if success
    #   1 if invalid input
    #   2 if invalid arguments

    # Reads a BASIC program from stdin if no arguments given,
    # else tries to read from given filename.
    if len(sys.argv) is 1:
        code = parse_input(sys.stdin)
    elif len(sys.argv) is 2:
        try:
            with open(sys.argv[1], "r") as f:
                code = parse_input(f)
        except IOError:
            print("Given argument is not a file")
            sys.exit(2)
    else:
        print("Too many arguments")
        sys.exit(2)

    # print_code_inorder(code)
    run_code(code)
