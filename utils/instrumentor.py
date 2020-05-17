from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparserext.ext_c_parser import OpenCLCParser
from pycparser.c_ast import *
from .constants import (
    llvm_instructions,
    hidden_counter_name_local,
    hidden_counter_name_global
)

class OcludeInstrumentor(OpenCLCGenerator):
    '''
    Responsible to add instrumentation code
    !!! WARNING !!! It is implicitly taken as granted that all possible curly braces
    have been added to the source code before attempting to instrument it.
    If not, using this class leads to undefined behavior.
    '''
    def __init__(self, instrumentation_data):
        super().__init__()
        self.instrumentation_data = instrumentation_data
        self.function_instrumentation_data = None
        self.oclude_bool_var_idx = 1

    def _get_bb_instrumentation(self, idx):
        '''
        idx points to an entry of self.function_instrumentation_data, which is
        a list of tuples (instr_idx, instr_cnt), and creates the AST representation of the command
        "atomic_{add,sub}(&<hidden_local_counter>[instr_idx], instr_cnt);" for each tuple.
        Returns the list of these representations (i.e. AST nodes)
        '''
        instr = []
        for instr_name, instr_cnt in self.function_instrumentation_data[idx]:

            if instr_name.startswith('retNOT'):
                atomic_func_name = 'atomic_sub'
                instr_index = str(llvm_instructions.index('ret'))
            else:
                atomic_func_name = 'atomic_add'
                instr_index = str(llvm_instructions.index(instr_name))

            instr.append(
                FuncCall(name=ID(atomic_func_name),
                         args=ExprList(exprs=[
                                           UnaryOp(op='&', expr=ArrayRef(name=ID(hidden_counter_name_local),
                                                   subscript=Constant(type='int', value=instr_index))),
                                           Constant(type='int', value=str(instr_cnt))
                                       ]
                              )
                )
            )

        return instr

    def _unroll_cond_level(self, cond):
        '''
        recursive function that turns a conditional of a single operator
        into (one or more) if-else-if-... block(s)
        returns a tuple with 2 fields:
        - an ID node of the boolean variable that holds the result
        - the respective block(s) as a list
        '''

        def create_new_bool_var():
            name = 'oclude_bool_var_' + str(self.oclude_bool_var_idx)
            self.oclude_bool_var_idx += 1
            return name, Decl(name=name,
                              quals=[], storage=[], funcspec=[],
                              type=TypeDecl(declname=name,
                                         quals=[],
                                         type=IdentifierType(names=['bool'])
                                        ),
                              init=None, bitsize=None
                             )

        def assign(var, val):
            '''
            assigns the boolean value val to the variable named var
            UNDEFINED BEHAVIOR if val is not an ID or a string ('true' / 'false')
            '''
            return Assignment(
                op='=',
                lvalue=ID(var),
                rvalue=ID(val) if type(val) is str else val
            )

        if not (isinstance(cond, BinaryOp) and cond.op in ['||', '&&']):
            return cond, None

        var_name, var_decl = create_new_bool_var()
        op = cond.op
        curr_cond = cond
        operands = []
        while isinstance(curr_cond, BinaryOp) and curr_cond.op == op:
            operands.append(curr_cond.right)
            curr_cond = curr_cond.left

        operands.append(curr_cond)
        operands.reverse()

        operand, operand_block = self._unroll_cond_level(operands.pop())
        blocks_to_append = [assign(var_name, operand)]
        if operand_block is not None:
            blocks_to_append = operand_block + blocks_to_append

        while operands:
            operand, operand_block = self._unroll_cond_level(operands.pop())

            if operand_block is not None:
                blocks_to_append = operand_block + blocks_to_append

            if op == '||':
                # if operand is true, then our conditional is true
                # else, we move on to the next operand (if any)
                operand_expr  = operand
                iftrue_block  = assign(var_name, 'true') # conditional is true
                iffalse_block = Compound(block_items=blocks_to_append)

            else: # op == '&&'
                # if op is false, then our conditional is false
                # else, we move on to the next operand (if any)
                operand_expr  = UnaryOp(op='!', expr=operand)
                iftrue_block  = assign(var_name, 'false') # conditional is false
                iffalse_block = Compound(block_items=blocks_to_append)

            blocks_to_append = [If(
                cond    = operand_expr,
                iftrue  = iftrue_block,
                iffalse = iffalse_block
            )]

        return ID(var_name), [var_decl] + blocks_to_append

    def visit_FuncDef(self, n):
        '''
        sets the instrumentation data of this specific function
        for the visit_Compound function to find them later
        '''
        self.function_instrumentation_data = self.instrumentation_data[n.decl.name]
        print('FUNCTION "' + n.decl.name + '" SHOULD HAVE', len(self.function_instrumentation_data), 'BBs')
        return super().visit_FuncDef(n)

    def visit_Compound(self, n):

        # TODO: remove the following 3 lines
        from random import randint
        compound_id = ''.join([str(randint(1, 9)) for _ in range(6)])
        print('[+++] ENTERING Compound with ID =', compound_id)

        instr_block_items = []

        for i in range(len(n.block_items)):
            stmt = n.block_items[i]

            # (maybe) bool var init
            if isinstance(stmt, Decl) and stmt.init is not None:
                cond_var, cond_block_list = self._unroll_cond_level(stmt.init)
                if cond_block_list is not None:
                    stmt.init = cond_var
                    instr_block_items += cond_block_list

            # (maybe) bool var assignment
            elif isinstance(stmt, Assignment):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.rvalue)
                if cond_block_list is not None:
                    stmt.rvalue = cond_var
                    instr_block_items += cond_block_list

            # if statement
            elif isinstance(stmt, If):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.cond)
                if cond_block_list is not None:
                    stmt.cond = cond_var
                    instr_block_items += cond_block_list

            # for statement
            elif isinstance(stmt, For):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.cond)
                # conditional BB
                if cond_block_list is not None:
                    stmt.cond = cond_var
                    instr_block_items += cond_block_list
                    # body BB
                    # repeat conditional BB inside for loop, at the end
                    # remove the declaration of the oclude bool var here
                    # (it is already declared before the for loop)
                    # (also remember that, per the LLVM layout, there is an inc BB
                    #  at the end of the for loop body)
                    for_body = [stmt.stmt] + cond_block_list[1:]
                    # done, replace body of for with the instrumented one
                    stmt.stmt = Compound(for_body)

            # while statement
            elif isinstance(stmt, While):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.cond)
                # conditional BB
                if cond_block_list is not None:
                    stmt.cond = cond_var
                    instr_block_items += cond_block_list
                    # body BB
                    # repeat conditional BB inside while loop, at the end
                    # remove the declaration of the oclude bool var here
                    # (it is already declared before the while loop)
                    while_body = [stmt.stmt] + cond_block_list[1:]
                    # done, replace body of while with the instrumented one
                    stmt.stmt = Compound(while_body)

            # do-while statement
            elif isinstance(stmt, DoWhile):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.cond)
                # before body BB, declare bool var if needed
                if cond_block_list is not None:
                    stmt.cond = cond_var
                    instr_block_items.append(cond_block_list[0])
                    # body BB
                    # repeat conditional BB inside while loop, at the end
                    # remove the declaration of the oclude bool var here
                    # (it is already declared before the while loop)
                    while_body = [stmt.stmt] + cond_block_list[1:]
                    # done, replace body of while with the instrumented one
                    stmt.stmt = Compound(while_body)

            # ternary assignment
            elif isinstance(stmt, Assignment) and isinstance(stmt.rvalue, TernaryOp):
                lval = stmt.lvalue
                ternary = stmt.rvalue
                ternary_cond = ternary.cond
                cond_var, cond_block_list = self._unroll_cond_level(ternary_cond)
                ternary_iftrue = ternary.iftrue
                ternary_iffalse = ternary.iffalse
                stmt = If(
                    cond = cond_var,
                    iftrue = Compound([Assignment(op='=', lvalue=lval, rvalue=ternary_iftrue)]),
                    iffalse = Compound([Assignment(op='=', lvalue=lval, rvalue=ternary_iffalse)])
                )
                if cond_block_list is not None:
                    instr_block_items += cond_block_list

            # ternary statement
            elif isinstance(stmt, TernaryOp):
                cond_var, cond_block_list = self._unroll_cond_level(stmt.cond)
                iftrue = stmt.iftrue
                iffalse = stmt.iffalse
                stmt = If(
                    cond = cond_var,
                    iftrue = Compound([iftrue]),
                    iffalse = Compound([iffalse])
                )
                if cond_block_list is not None:
                    instr_block_items += cond_block_list

            instr_block_items.append(stmt)

        n.block_items = instr_block_items

        # TODO: remove the following 1 line
        print('[---] LEAVING Compound with ID =', compound_id)

        return super().visit_Compound(n)


class OcludeKernelFinalizer(OpenCLCGenerator):
    '''
    Responsible to add prologue and epilogue to all kernels
    '''
    def __init__(self, kernelFuncs):
        super().__init__()
        self.kernelFuncs = kernelFuncs

        # this is the prologue of the instrumentation of every kernel in OpenCL:
        #
        # if (get_local_id(0) == 0)
        #     for (int i = 0; i < <len(llvm_instructions)>; i++)
        #         <hidden_counter_name_local>[i] = 0;
        # barrier(CLK_GLOBAL_MEM_FENCE);
        #
        # and this is its AST:
        self.prologue = [
            If(cond=BinaryOp(op='==',
                             left=FuncCall(name=ID('get_local_id'),
                                           args=ExprList(exprs=[Constant(type='int', value='0')])),
                             right=Constant(type='int', value='0')),
               iftrue=For(init=DeclList(decls=[Decl(name='i', quals=[], storage=[], funcspec=[],
                                        type=TypeDecl(declname='i', quals=[], type=IdentifierType(names=['int'])),
                                        init=Constant(type='int', value='0'), bitsize=None)]),
                          cond=BinaryOp(op='<', left=ID('i'), right=Constant(type='int', value=str(len(llvm_instructions)))),
                          next=UnaryOp(op='p++', expr=ID('i')),
                          stmt=Assignment(op='=', lvalue=ArrayRef(name=ID(hidden_counter_name_local), subscript=ID('i')),
                                                  rvalue=Constant(type='int', value='0'))),
               iffalse=None),
            FuncCall(name=ID('barrier'), args=ExprList(exprs=[ID('CLK_GLOBAL_MEM_FENCE')]))
        ]

        # this is the epilogue of the instrumentation of every kernel in OpenCL:
        #
        # barrier(CLK_GLOBAL_MEM_FENCE);
        # if (get_local_id(0) == 0) {{
        #     int glid = get_group_id(0) * <len(llvm_instructions)>;
        #     for (int i = glid; i < glid + <len(llvm_instructions)>; i++)
        #         <hidden_counter_name_global>[i] = <hidden_counter_name_local>[i - glid];
        #
        # and this is its AST:
        self.epilogue = [
            FuncCall(name=ID('barrier'), args=ExprList(exprs=[ID('CLK_GLOBAL_MEM_FENCE')])),
            If(cond=BinaryOp(op='==',
                             left=FuncCall(name=ID('get_local_id'),
                                           args=ExprList(exprs=[Constant(type='int', value='0')])),
                             right=Constant(type='int', value='0')),
               iftrue=Compound([
                            Decl(name='glid', quals=[], storage=[], funcspec=[],
                                 type=TypeDecl(declname='glid', quals=[], type=IdentifierType(names=['int'])),
                                 init=BinaryOp(op='*', left=FuncCall(name=ID('get_group_id'),
                                               args=ExprList(exprs=[Constant(type='int', value='0')])),
                                               right=Constant(type='int', value=str(len(llvm_instructions)))),
                                 bitsize=None),
                            For(init=DeclList(decls=[Decl(name='i', quals=[], storage=[], funcspec=[],
                                              type=TypeDecl(declname='i', quals=[], type=IdentifierType(names=['int'])),
                                              init=ID('glid'), bitsize=None)]),
                                cond=BinaryOp(op='<', left=ID('i'),
                                              right=BinaryOp(op='+', left=ID('glid'),
                                                             right=Constant(type='int', value=str(len(llvm_instructions))))),
                                next=UnaryOp(op='p++', expr=ID('i')),
                                stmt=Assignment(op='=', lvalue=ArrayRef(name=ID(hidden_counter_name_global), subscript=ID('i')),
                                                rvalue=ArrayRef(name=ID(hidden_counter_name_local),
                                                subscript=BinaryOp(op='-', left=ID('i'), right=ID('glid')))))
                               ]),
               iffalse=None)
        ]

    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add prologue and epilogue
        '''
        if n.decl.name in self.kernelFuncs:
            n.body.block_items = self.prologue + n.body.block_items
            if isinstance(n.body.block_items[-1], Return):
                n.body.block_items = n.body.block_items[:-1] + self.epilogue + n.body.block_items[-1:]
            else:
                n.body.block_items += self.epilogue

        return super().visit_FuncDef(n)


def add_instrumentation_data_to_file(filename, kernels, instr_data_raw, parser):

    # parse instrumentation data
    from itertools import groupby
    from collections import Counter

    instrumentation_per_function = {}
    for funcname, g in groupby(instr_data_raw.strip().splitlines(), lambda line : line.split('|')[0].split(':')[0]):
        func_bbs = sorted(g, key=lambda x : int(x.split(':')[1].split('|')[0]))
        instrs_per_bb = list(map(lambda x : list(map(lambda y : y.split(':')[-1], x.split('|')[1:]))[:-1], func_bbs))
        instrs_per_bb = list(map(lambda x : list(Counter(x).items()), instrs_per_bb))
        instrumentation_per_function[funcname] = instrs_per_bb

    print(len(instrumentation_per_function['calcLikelihoodSum']))
    for i, x in enumerate(instrumentation_per_function['calcLikelihoodSum'], 1):
        print(i, ':', x)
    # exit(0)

    # parsing done, time to add instrumentation to source code
    with open(filename, 'r') as f:
        ast = parser.parse(f.read())

    # add instrumentation data to all functions
    instrumentor = OcludeInstrumentor(instrumentation_per_function)
    ast = OpenCLCParser().parse(instrumentor.visit(ast))

    # add prologue and epilogue to kernel functions only
    kernel_finalizer = OcludeKernelFinalizer(kernels)
    with open(filename, 'w') as f:
        f.write(kernel_finalizer.visit(ast))
