#!/usr/bin/env python3

from lark import Lark, Transformer


# Define the new grammar
op_parser = Lark(
    r"""
    program: vardeclist? fundeclist

    vardeclist: (vardec WS)*
    fundeclist: (fundec WS)+

    fundec: "fun" WS typ WS ID "(" paradeclist? ")" WS body WS "endfun"
    !typ: "int" | "void"
    body: vardeclist stmtlist

    paradeclist: type WS ID (WS "," WS type WS ID)*
    vardec: "var" WS type WS varlist ";"
    type: ID
    varlist: ID (WS "," WS ID)*

    stmtlist: stmt (";" WS stmt)*
    stmt: assign
        | print
        | ife
        | whilel
        | returne

    assign: ID WS "=" WS cexp
    print: "print" "(" cexp ")"
    ife: "if" WS cexp WS "then" WS body WS ("else" WS body WS)? "endif"
    whilel: "while" WS cexp WS "do" WS body WS "endwhile"
    returne: "return" WS "(" cexp? ")"

    cexp: exp (WS "<" WS exp)?
    !exp: term (WS ("+"|"-") WS term)*
    !term: factor (WS ("*"|"/") WS factor)*
    factor: ID
          | INT
          | BOOL
          | "(" exp ")"
          | ID "(" arglist? ")"

    arglist: cexp (WS "," WS cexp)*
    BOOL: "true" | "false"

    ID: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %import common.NEWLINE
    %import common.INT
    %ignore WS
    %ignore NEWLINE
    """,
    start="program",  # Ensure there's a newline after this line in the actual file
)


class MyTransformer(Transformer):
    def INT(self, n):
        return int(n)

    def WS(self, space):
        return

    def ID(self, i):
        return str(i)

    def BOOL(self, b):
        return b == "true"

    def program(self, items):
        return {"varDecList": items[0], "funDecList": items[1]}

    def vardeclist(self, items):
        return items[::2]

    def fundeclist(self, items):
        return items[::2]

    def fundec(self, items):
        # items will contain [typ, ID, paradeclist?, body]
        # paradeclist is optional, so check its presence
        typ = items[1]
        fid = items[3]
        if len(items) == 8:
            param_dec_list = items[4]
            body = items[6]
            return {
                "type": typ,
                "id": fid,
                "params": param_dec_list,
                "body": body,
            }
        else:  # No paradeclist
            body = items[5]
            return {
                "type": typ,
                "id": fid,
                "params": [],
                "body": body,
            }

    def typ(self, items):
        return str(items[0])

    def body(self, items):
        vardecs = items[0]
        stmts = items[1]
        return {"var_declarations": vardecs, "statements": stmts}

    def paradeclist(self, items):
        # items will be a flat list of type, ID, type, ID...
        params = []
        for i in range(0, len(items), 2):
            params.append({"type": items[i], "id": items[i + 1]})
        return params

    def vardec(self, items):
        # items will be [type, varlist]
        return {"type": items[1], "vars": items[3]}

    def type(self, items):
        return str(items[0])

    def varlist(self, items):
        return [str(item) for item in items]

    def stmtlist(self, items):
        return items[::2]

    def assign(self, items):
        id_var = items[0]
        return {"assignment": {"id": items[0], "expression": items[3]}}

    def print(self, items):
        return {"print": items[0]}

    def ife(self, items):

        if len(items) == 3:  # if then body
            return {"if_statement": {"condition": items[1], "then_body": items[4]}}
        else:  # if then body else body
            return {
                "if_statement": {
                    "condition": items[1],
                    "then": items[4],
                    "else": items[7],
                }
            }

    def whilel(self, items):
        return {"while": {"condition": items[1], "body": items[4]}}

    def returne(self, items):
        return {"return_statement": items[1] if items[1] else None}

    def stmt(self, items):
        return items[0]

    def cexp(self, items):
        if len(items) > 2:
            return {
                "left": items[0],
                "operator": "<",
                "right": items[3],
            }
        return items[0]

    def exp(self, items):
        if len(items) == 1:
            return items[0]
        # Handle multiple terms with + or -
        result = items[0]
        for i in range(1, len(items), 4):
            operator = items[i + 1]
            operand = items[i + 3]

            # This takes care of the constant optimization
            try:
                if operator == "+":
                    result = int(result) + int(operand)
                else:
                    result = int(result) - int(operand)

            except (ValueError, TypeError):
                result = {
                    "left": result,
                    "operator": operator[0],
                    "right": operand,
                }
        return result

    def term(self, items):
        if len(items) == 1:
            return items[0]
        # Handle multiple factors with * or /
        result = items[0]
        for i in range(1, len(items), 4):
            operator = items[i + 1]
            operand = items[i + 3]
            # This takes care of the constant optimization
            try:
                if operator == "*":
                    result = int(result) * int(operand)
                else:
                    result = int(result) / int(operand)

            except (ValueError, TypeError):
                result = {
                    "left": result,
                    "operator": operator[0],
                    "right": operand,
                }
        return result

    def factor(self, items):
        if len(items) == 1:
            return items[0]
        elif isinstance(items[0], str) and (
            len(items) == 2 or len(items) == 1
        ):  # ID ( [arglist] ) or just ID
            if len(items) == 2:  # Function call
                return {
                    "call": {
                        "id": items[0],
                        "arguments": items[1] if items[1] else [],
                    }
                }
            else:  # Just an ID (variable)
                return items[0]
        else:  # ( exp )
            return items[0]  # The expression inside the parentheses

    def arglist(self, items):
        return items


def read_input(fil):
    with open(fil) as fp:
        return MyTransformer().transform(op_parser.parse(fp.read()))


class ProgramUnparser:
    def __init__(self, indent_level=0, indent_char="    "):
        self.indent_level = indent_level
        self.indent_char = indent_char

    def _indent(self):
        return self.indent_char * self.indent_level

    def unparse(self, parsed_program):
        output = []
        if parsed_program.get("varDecList"):
            output.append(self.unparse_vardeclist(parsed_program["varDecList"]))
        output.append(self.unparse_fundeclist(parsed_program["funDecList"]))
        return "\n".join(output)

    def unparse_vardeclist(self, vardeclist):
        return "\n".join([self.unparse_vardec(vd) for vd in vardeclist])

    def unparse_fundeclist(self, fundeclist):
        return "\n\n".join([self.unparse_fundec(fd) for fd in fundeclist])

    def unparse_fundec(self, fundec):
        params = ", ".join([f"{p['type']} {p['id']}" for p in fundec["params"]])
        body_str = self.unparse_body(fundec["body"])
        return (
            f"fun {fundec['type']} {fundec['id']}({params})\n" f"{body_str}\n" f"endfun"
        )

    def unparse_body(self, body):
        self.indent_level += 1
        var_decs = "\n".join(
            [self.unparse_vardec(vd) for vd in body["var_declarations"]]
        )
        stmts = ";\n".join([self.unparse_stmt(s) for s in body["statements"]])
        self.indent_level -= 1
        return f"{var_decs}\n{stmts}" if var_decs else stmts

    def unparse_vardec(self, vardec):
        vars_str = ", ".join(vardec["vars"])
        return f"{self._indent()}var {vardec['type']} {vars_str};"

    def unparse_stmt(self, stmt):
        if "assignment" in stmt:
            assign = stmt["assignment"]
            return f"{self._indent()}{assign['id']} = {self.unparse_cexp(assign['expression'])}"
        elif "print" in stmt:
            return f"{self._indent()}print({self.unparse_cexp(stmt['print'])})"
        elif "if_statement" in stmt:
            if_stmt = stmt["if_statement"]
            then_body = self.unparse_body(if_stmt["then"])
            else_body = ""
            if "else" in if_stmt:
                else_body = (
                    f"\n{self._indent()}else\n{self.unparse_body(if_stmt['else'])}"
                )
            return (
                f"{self._indent()}if {self.unparse_cexp(if_stmt['condition'])} then\n"
                f"{then_body}{else_body}\n"
                f"{self._indent()}endif"
            )
        elif "while" in stmt:
            while_stmt = stmt["while"]
            body_str = self.unparse_body(while_stmt["body"])
            return (
                f"{self._indent()}while {self.unparse_cexp(while_stmt['condition'])} do\n"
                f"{body_str}\n"
                f"{self._indent()}endwhile"
            )
        elif "return_statement" in stmt:
            ret_val = (
                self.unparse_cexp(stmt["return_statement"])
                if stmt["return_statement"] is not None
                else ""
            )
            return f"{self._indent()}return ({ret_val})"
        return ""  # Should not happen

    def unparse_cexp(self, cexp):
        if isinstance(cexp, dict) and "operator" in cexp and cexp["operator"] == "<":
            return (
                f"{self.unparse_exp(cexp['left'])} < {self.unparse_exp(cexp['right'])}"
            )
        return self.unparse_exp(cexp)

    def unparse_exp(self, exp):
        if isinstance(exp, dict) and "operator" in exp:
            left = self.unparse_exp(exp["left"])
            right = self.unparse_exp(exp["right"])
            return f"{left} {exp['operator']} {right}"
        return self.unparse_term(exp)

    def unparse_term(self, term):
        if isinstance(term, dict) and "operator" in term:
            left = self.unparse_term(term["left"])
            right = self.unparse_term(term["right"])
            return f"{left} {term['operator']} {right}"
        return self.unparse_factor(term)

    def unparse_factor(self, factor):
        if isinstance(factor, str):
            return factor
        elif isinstance(factor, int):
            return str(factor)
        elif isinstance(factor, bool):
            return "true" if factor else "false"
        elif isinstance(factor, dict) and "call" in factor:
            call = factor["call"]
            args = ", ".join([self.unparse_cexp(arg) for arg in call["arguments"]])
            return f"{call['id']}({args})"
        elif isinstance(factor, dict):  # (exp) case
            return f"({self.unparse_exp(factor)})"
        return ""  # Should not happen


class Hoister:
    def __init__(self):
        # scope_stack will store hoisting oportunities and the vars modified beforehand
        self.scope_stack = []

    def enter_scope(self):
        self.scope_stack.append(
            {
                "take_out": [],
                "modified_vars": set(),
                "hoisting_opportunities": [],
                "index": 0,
                "take_out_lines": [],
            }
        )

    def exit_scope(self):
        self.scope_stack.pop()

    def mark_modified(self, var_name):
        if self.scope_stack:
            self.scope_stack[-1]["modified_vars"].add(var_name)

    def add_hoisting_opportunity(self, exp):
        if self.scope_stack:
            self.scope_stack[-1]["hoisting_opportunities"].append(exp)

    def add_take_out(self, exp):
        if self.scope_stack:
            self.scope_stack[-1]["take_out"].append(exp)
            self.scope_stack[-1]["take_out_lines"].append(self.scope_stack[-1]["index"])

    def is_var_modified(self, var_name):
        if self.scope_stack:
            return var_name in self.scope_stack[-1]["modified_vars"]
        return False

    def expression_reduce(self, exp):
        # print("exp: ", exp)
        if isinstance(exp, dict):
            left_can_take_out = 0
            right_can_take_out = 0
            # print("eval left: ")
            if isinstance(exp["left"], dict):
                left_can_take_out = self.expression_reduce(exp["left"])
            elif isinstance(exp["left"], int):
                left_can_take_out = True
            elif isinstance(exp["left"], str) and not self.is_var_modified(exp["left"]):
                left_can_take_out = True
            else:
                left_can_take_out = False

            if isinstance(exp["right"], dict):
                right_can_take_out = self.expression_reduce(exp["right"])
            elif isinstance(exp["right"], int):
                right_can_take_out = True
            elif isinstance(exp["right"], str) and not self.is_var_modified(
                exp["right"]
            ):
                right_can_take_out = True
            else:
                left_can_take_out = False

            if left_can_take_out and right_can_take_out:
                return True
            elif left_can_take_out:
                if isinstance(exp["left"], dict):
                    exp["left"] = "return_" + str(len(self.scope_stack[-1]["take_out"]))
                    self.add_take_out(exp["left"])
                return False
            elif right_can_take_out:
                if isinstance(exp["right"], dict):
                    exp["right"] = "return_" + str(
                        len(self.scope_stack[-1]["take_out"])
                    )
                    self.add_take_out(exp["right"])
                return False
            else:
                return False

        elif isinstance(exp, str) or isinstance(exp, int):
            return True
        else:
            return False

    def optimize_body(self, body):
        self.enter_scope()
        var_decs = body["var_declarations"]
        assigns_top = []

        new_vars = []
        new_assign = []

        for i in range(len(body["statements"])):
            stmt = body["statements"][i]
            self.scope_stack[-1]["index"] = i
            if "while" in stmt.keys():
                results = self.optimize_body(stmt["while"]["body"])
                var_decs.extend(results[0])
                assigns_top.extend(results[1])
            elif "if_statement" in stmt.keys():
                self.optimize_body(stmt["if_statement"]["then"])
                if len(stmt["if_statement"]) == 3:
                    self.optimize_body(stmt["if_statement"]["else"])
            elif "assignment" in stmt.keys():
                self.mark_modified(stmt["assignment"]["id"])
                if self.expression_reduce(
                    stmt["assignment"]["expression"]
                ) and isinstance(stmt["assignment"]["expression"], dict):
                    self.add_take_out(stmt["assignment"]["expression"])
                    stmt["assignment"]["expression"] = "reduced_" + str(
                        len(self.scope_stack[-1]["take_out"]) - 1
                    )

            elif "print" in stmt.keys():
                if self.expression_reduce(stmt["print"]) and isinstance(
                    stmt["print"], dict
                ):
                    self.add_take_out(stmt["print"])
                    stmt["print"] = "reduced_" + str(
                        len(self.scope_stack[-1]["take_out"]) - 1
                    )

            elif "return_statement" in stmt.keys():
                if self.expression_reduce(
                    stmt["return_statement"]["expression"]
                ) and isinstance(stmt["return_statement"]["expression"], dict):
                    self.add_take_out(stmt["return_statement"]["expression"])
                    stmt["return_statement"]["expression"] = "reduced_" + str(
                        len(self.scope_stack[-1]["take_out"]) - 1
                    )

        for i in range(len(assigns_top)):
            body["statements"].insert(self.scope_stack[-1]["index"] - 1, assigns_top[i])

        body["var_declarations"] = var_decs

        for opportunity in range(0, len(self.scope_stack[-1]["take_out"])):
            new_vars.append({"type": "int", "vars": ["reduced_" + str(opportunity)]})
            new_assign.append(
                {
                    "assignment": {
                        "id": "reduced_" + str(opportunity),
                        "expression": self.scope_stack[-1]["take_out"][opportunity],
                    }
                }
            )
        self.exit_scope()
        return [new_vars, new_assign]

    def optimize_p(self, program):
        # In theory, this should also optimize what is inside the function. We will ignore that
        for fun in program["funDecList"]:
            self.optimize_body(fun["body"])


def main():
    path = "input2.txt"
    unparser = ProgramUnparser()

    # the optmization of constants is done inside the parser
    parsed_program = read_input(path)
    # print(parsed_program)

    unparsed_program_str = unparser.unparse(parsed_program)
    print("\n--- Unparsed Program (Before code Hoisting) ---")
    print(unparsed_program_str)

    # Hoister
    hoister = Hoister()
    hoister.optimize_p(parsed_program)
    # print(parsed_program)
    unparsed_program_str = unparser.unparse(parsed_program)
    print("\n--- Unparsed Program (After code Hoisting) ---")
    print(unparsed_program_str)


main()
