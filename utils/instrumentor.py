from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import *
from .constants import (
    llvm_instructions,
    hidden_counter_name_local,
    hidden_counter_name_global
)

from itertools import count, filterfalse

class OcludeInstrumentor(OpenCLCGenerator):
    '''
    Responsible to add instrumentation code
    !!! WARNING !!! It is implicitly taken as granted that all possible curly braces
    have been added to the source code before attempting to instrument it.
    If not, using this class leads to undefined behavior.
    '''
    def __init__(self, kernelFuncs, instrumentation_data):

        super().__init__()

        self.instrumentation_data = instrumentation_data
        self.function_instrumentation_data = None
        self.oclude_bool_var_idx = 1

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

    def _get_bb_instrumentation(self, idx):
        print('>>> NEXT INSTRUMENTATION BLOCK ASKED <<<')
        '''
        idx points to an entry of self.function_instrumentation_data, which is
        a list of tuples (instr_idx, instr_cnt), and creates the AST representation of the command
        "atomic_{add,sub}(&<hidden_local_counter>[instr_idx], instr_cnt);" for each tuple.
        Returns the list of these representations (i.e. AST nodes)
        '''
        instr = []
        # TODO: remove the following line
        idx = min(idx, len(self.function_instrumentation_data)-1)
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
        recursive method that turns a conditional of a single operator
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

            if operand_block is not None:
                blocks_to_append = operand_block + blocks_to_append

        return ID(var_name), [var_decl] + blocks_to_append

    def _process_unrolled_cond(self, cond_blocks, idx):
        '''
        recursive method that returns the following tuple:
        1. the instrumented version of cond_block_list
        2. the new idx
        '''
        print('!!!!!!!!!!!!!!!!!!!!!!!!! IN PROCESS UNROLLED COND !!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        # important: there is a constant in this recursion:
        # THE INSTRUMENTATION OF THE BB THAT PRECEDES THIS LIST OF BLOCKS
        # HAS BEEN ADDED BY THE CALLER!
        # that means that we only get inside the first if cond_block
        # and we add nothing before it (only inside it)
        if cond_blocks is None:
            print('!!!!!!!!!!!!!!!!!!!!!!!!! OUT (SAAAAAAAAAAAAAAAAAAAD) PROCESS UNROLLED COND !!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return cond_blocks, idx

        # if len(cond_blocks) == 1 and isinstance(cond_blocks[0], Assignment):
        #     cond_blocks = self._get_bb_instrumentation(idx) + cond_blocks
        #     idx += 1
        #     return cond_blocks, idx

        instr_cond_blocks = []

        # done_with_first = False
        # for i in range(len(cond_blocks)):
        #     block = cond_blocks[i]
        #     if isinstance(block, If):
        #         if done_with_first:
        #             instr_cond_blocks += self._get_bb_instrumentation(idx)
        #             idx += 1
        #         else:
        #             done_with_first = True
        #         instr_iffalse = self._get_bb_instrumentation(idx)
        #         idx += 1
        #         instr_iffalse_block, idx = self._process_unrolled_cond(block.iffalse.block_items, idx)
        #         instr_iffalse_block = instr_iffalse + instr_iffalse_block
        #         block.iffalse.block_items = instr_iffalse_block
        #     instr_cond_blocks.append(block)

        for cond_block in cond_blocks:
            if isinstance(cond_block, If):
                instr_iffalse = self._get_bb_instrumentation(idx)
                idx += 1
                instr_iffalse_block, idx = self._process_unrolled_cond(cond_block.iffalse.block_items, idx)
                cond_block.iffalse.block_items = instr_iffalse + instr_iffalse_block
            instr_cond_blocks.append(cond_block)

        print('!!!!!!!!!!!!!!!!!!!!!!!!! OUT PROCESS UNROLLED COND !!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        return instr_cond_blocks, idx


    def _process_block(self, block, idx):

        if block is None:
            return idx, block

        instr_block_items = []

        for block_item in block.block_items:

            # case 1: right before a compound; need to add instrumentation cmds
            #         several subcases need to be taken into consideration

            ### (maybe) bool var init ###
            if isinstance(block_item, Decl) and block_item.init is not None:
                print('\tIN VAR DECL AND INIT')
                cond_var, cond_block_list = self._unroll_cond_level(block_item.init)
                if cond_block_list is not None:
                    block_item.init = cond_var
                    cond_block_list, idx = self._process_unrolled_cond(cond_block_list, idx)
                    instr_block_items += cond_block_list
                instr_block_items.append(block_item)
                # the last BB
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1

            ### (maybe) bool var assignment ###
            elif isinstance(block_item, Assignment):
                print('\tIN VAR ASSIGNMENT')
                cond_var, cond_block_list = self._unroll_cond_level(block_item.rvalue)
                if cond_block_list is not None:
                    block_item.rvalue = cond_var
                    cond_block_list, idx = self._process_unrolled_cond(cond_block_list, idx)
                    instr_block_items += cond_block_list
                instr_block_items.append(block_item)
                # the last BB
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1

            ### if statement ###
            elif isinstance(block_item, If):
                print('\tIN IF')

                # (possible) cond instrumentation
                cond_var, cond_block_list = self._unroll_cond_level(block_item.cond)
                if cond_block_list is not None:
                    block_item.cond = cond_var
                    cond_block_list, idx = self._process_unrolled_cond(cond_block_list, idx)
                    instr_block_items += cond_block_list

                # iftrue instrumentation
                iftrue_instrumentation = self._get_bb_instrumentation(idx)
                idx += 1
                idx, processed_iftrue = self._process_block(block_item.iftrue, idx)
                instrumented_iftrue = iftrue_instrumentation + processed_iftrue.block_items
                block_item.iftrue = Compound(instrumented_iftrue)

                # iffalse instrumentation
                if block_item.iffalse is not None:
                    iffalse_instrumentation = self._get_bb_instrumentation(idx)
                    idx += 1
                    idx, processed_iffalse = self._process_block(block_item.iffalse, idx)
                    instrumented_iffalse = iffalse_instrumentation + processed_iffalse.block_items
                    block_item.iffalse = Compound(instrumented_iffalse)

                instr_block_items.append(block_item)

                # the last BB (i.e. if.end):
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1

            ### for statement ###
            elif isinstance(block_item, For):
                print('\tIN FOR')

                ############# IMPORTANT NOTE #############
            	# we assume that we will not find        #
            	# compound conditions if for statements, #
            	# for simplicity                         #
                ##########################################

                # surely there is one cond BB
                cond_instr_block_list = self._get_bb_instrumentation(idx)
                idx += 1
                # (possible) cond instrumentation
                cond_var, cond_block_list = self._unroll_cond_level(block_item.cond)
                if cond_block_list is not None:
                    raise NotImplementedError('found for statement with compound condition')

                instr_block_items += cond_instr_block_list

                # body BB
                body_instr = self._get_bb_instrumentation(idx)
                idx += 1
                idx, processed_body = self._process_block(block_item.stmt, idx)
                # inc BB at the end of for
                body_instr += self._get_bb_instrumentation(idx)
                idx += 1
                # add cond BB(s) at the end of for
                for_body = [Compound(body_instr + processed_body.block_items)] + cond_instr_block_list
                block_item.stmt.block_items = for_body
                instr_block_items.append(block_item)

                # the last BB (i.e. for.end):
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1

            ### while statement ###
            elif isinstance(block_item, While):
                print('\tIN WHILE')

                # surely there is one cond BB
                cond_instr_block_list = self._get_bb_instrumentation(idx)
                idx += 1
                # (possible) cond instrumentation
                cond_var, cond_block_list = self._unroll_cond_level(block_item.cond)
                if cond_block_list is not None:
                    cond_instr_block_list += self._get_bb_instrumentation(idx)
                    idx += 1
                    block_item.cond = cond_var
                    cond_instr_block_list_extra, idx = self._process_unrolled_cond(cond_block_list, idx)
                    cond_instr_block_list += cond_instr_block_list_extra

                instr_block_items += cond_instr_block_list

                # body BB
                body_instr = self._get_bb_instrumentation(idx)
                idx += 1
                idx, processed_body = self._process_block(block_item.stmt, idx)
                # add cond BB(s) at the end of while
                # remove the declaration of the master bool var first
                cond_instr_block_list = list(
                    filterfalse(lambda x, c=count():
                        isinstance(x, Decl) and next(c) < 1, cond_instr_block_list
                    )
                )
                while_body = [Compound(body_instr + processed_body.block_items)] + cond_instr_block_list
                block_item.stmt.block_items = while_body
                instr_block_items.append(block_item)

                # the last BB (i.e. while.end):
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1

            ### do-while statement ###
            elif isinstance(block_item, DoWhile):
                print('\tIN DO WHILE')

                # body BB
                body_instr = self._get_bb_instrumentation(idx)
                idx += 1
                idx, processed_body = self._process_block(block_item.stmt, idx)

                # surely there is one cond BB
                cond_instr_block_list = self._get_bb_instrumentation(idx)
                idx += 1
                # (possible) cond instrumentation
                cond_var, cond_block_list = self._unroll_cond_level(block_item.cond)
                if cond_block_list is not None:
                    cond_instr_block_list += self._get_bb_instrumentation(idx)
                    idx += 1
                    block_item.cond = cond_var
                    cond_instr_block_list_extra, idx = self._process_unrolled_cond(cond_block_list, idx)
                    cond_instr_block_list += cond_instr_block_list_extra

                # get the declaration of the master bool var
                try:
                    master_bool_var_decl = next(x for x in cond_instr_block_list if isinstance(x, Decl))
                except StopIteration:
                    master_bool_var_decl = None
                # remove the declaration of the master bool var
                cond_instr_block_list = list(
                    filterfalse(lambda x, c=count():
                        isinstance(x, Decl) and next(c) < 1, cond_instr_block_list
                    )
                )
                while_body = [Compound(body_instr + processed_body.block_items)] + cond_instr_block_list
                block_item.stmt.block_items = while_body
                if master_bool_var_decl is not None:
                    instr_block_items.append(master_bool_var_decl)
                instr_block_items.append(block_item)

                # the last BB (i.e. while.end):
                instr_block_items += self._get_bb_instrumentation(idx)
                idx += 1



            # case 2: right before a simple body item; nothing to do
            else:
                print('\tIN ORDINARY (DO NOTHING)')
                instr_block_items.append(block_item)

        block.block_items = instr_block_items
        return idx, block





                # TODO: MUST ADD THESE TOO:
        #     # ternary assignment
        #     elif isinstance(block_item, Assignment) and isinstance(block_item.rvalue, TernaryOp):
        #         lval = block_item.lvalue
        #         ternary = block_item.rvalue
        #         ternary_cond = ternary.cond
        #         cond_var, cond_block_list = self._unroll_cond_level(ternary_cond)
        #         ternary_iftrue = ternary.iftrue
        #         ternary_iffalse = ternary.iffalse
        #         block_item = If(
        #             cond = cond_var,
        #             iftrue = Compound([Assignment(op='=', lvalue=lval, rvalue=ternary_iftrue)]),
        #             iffalse = Compound([Assignment(op='=', lvalue=lval, rvalue=ternary_iffalse)])
        #         )
        #         if cond_block_list is not None:
        #             instr_block_items += cond_block_list
        #
        #     # ternary statement
        #     elif isinstance(block_item, TernaryOp):
        #         cond_var, cond_block_list = self._unroll_cond_level(block_item.cond)
        #         iftrue = block_item.iftrue
        #         iffalse = block_item.iffalse
        #         block_item = If(
        #             cond = cond_var,
        #             iftrue = Compound([iftrue]),
        #             iffalse = Compound([iffalse])
        #         )
        #         if cond_block_list is not None:
        #             instr_block_items += cond_block_list
        #
        #     instr_block_items.append(block_item)





    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add instrumentation
        '''
        self.function_instrumentation_data = self.instrumentation_data[n.decl.name]
        print('FUNCTION "' + n.decl.name + '" SHOULD HAVE', len(self.function_instrumentation_data), 'BBs')
        ### step 1: add instrumentation instructions ###
        first_func_instr = self._get_bb_instrumentation(0)
        bbs, n.body = self._process_block(n.body, 1)
        n.body.block_items = first_func_instr + n.body.block_items
        if n.decl.name in self.kernelFuncs:
            ### step 2: add prologue ###
            n.body.block_items = self.prologue + n.body.block_items
            ### step 3: add epilogue ###
            if isinstance(n.body.block_items[-1], Return):
                n.body.block_items = n.body.block_items[:-1] + self.epilogue + n.body.block_items[-1:]
            else:
                n.body.block_items += self.epilogue
        print('FUNCTION:', n.decl.name, 'COUNTED:', bbs)

        # the following assertion means that the way we mapped the source code
        # to BBs led us to counting the correct number of BBs
        # (i.e. the number of BBs in the respective LLVM bitcode).
        # It is of paramount importance that this assertion never fails!
        # assert len(self.function_instrumentation_data) == bbs

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

    # print(len(instrumentation_per_function['calcLikelihoodSum']))
    # for i, x in enumerate(instrumentation_per_function['calcLikelihoodSum'], 1):
    #     print(i, ':', x)
    # exit(0)

    # parsing done, time to add instrumentation to source code
    with open(filename, 'r') as f:
        ast = parser.parse(f.read())

    instrumentor = OcludeInstrumentor(kernels, instrumentation_per_function)
    with open(filename, 'w') as f:
        f.write(instrumentor.visit(ast))
