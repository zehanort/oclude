from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import *
from .constants import (
    llvm_instructions,
    hidden_counter_name_local,
    hidden_counter_name_global
)

class OcludeInstrumentor(OpenCLCGenerator):
    '''
    Responsible to:
        1. add prologue and epilogue to all kernels
        2. add instrumentation code
    !!! WARNING !!! It is implicitly taken as granted that all possible curly braces
    have been added to the source code before attempting to instrument it.
    If not, using this class leads to undefined behavior.
    '''
    def __init__(self, kernelFuncs, instrumentation_data):

        super().__init__()

        self.kernelFuncs = kernelFuncs
        self.instrumentation_data = instrumentation_data
        self.function_instrumentation_data = None

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

    def _create_instrumentation_cmds(self, idx):
        '''
        idx points to an entry of self.function_instrumentation_data, which is
        a list of tuples (instr_idx, instr_cnt), and creates the AST representation of the command
        "atomic_{add,sub}(&<hidden_local_counter>[instr_idx], instr_cnt);" for each tuple.
        Returns the list of these representations
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
                FuncCall(name=ID(name=atomic_func_name),
                         args=ExprList(exprs=[
                                           UnaryOp(op='&', expr=ArrayRef(name=ID(name=hidden_counter_name_local),
                                                   subscript=Constant(type='int', value=instr_index))),
                                           Constant(type='int', value=str(instr_cnt))
                                       ]
                              )
                )
            )

        return instr

    def _count_logical_binops(self, bo):
        if not isinstance(bo, BinaryOp):
            return 1
        if isinstance(bo, BinaryOp):
            if not (bo.op == '||' or bo.op == '&&'):
                return 1
            else:
                l = self._count_logical_binops(bo.left)
                r = self._count_logical_binops(bo.right)
                return l + r

    def _process_bb(self, bb, idx, finish=True):

        if bb is None:
            return idx, bb

        instrumented_bb = []

        block_items = bb.block_items + [None] if bb.block_items is not None else [None]
        for block_item in block_items:
            # case 1: reached the end of bb, should have at least a ret or a br
            if block_item is None or isinstance(block_item, Return):
                if finish:
                    print('\tIN END')
                    instrumented_bb += self._create_instrumentation_cmds(idx)
                    print('\t\tHELLO')
                    idx += 1
                    if block_item is not None:
                        instrumented_bb.append(block_item)
                break
            # case 2: right before a compound; need to add instrumentation cmds
            #         several subcases need to be taken into consideration
            elif isinstance(block_item, If):
                print('\tIN IF')
                how_many_bin_ops = self._count_logical_binops(block_item.cond)
                for _ in range(how_many_bin_ops):
                    instrumented_bb += self._create_instrumentation_cmds(idx)
                    idx += 1
                idx, instrumented_iftrue = self._process_bb(block_item.iftrue, idx)
                block_item.iftrue = instrumented_iftrue
                # if-else-if is a special case
                finish = not (block_item.iffalse is not None and len(block_item.iffalse.block_items) == 1
                              and isinstance(block_item.iffalse.block_items[0], If))
                idx, instrumented_iffalse = self._process_bb(block_item.iffalse, idx, finish)
                block_item.iffalse = instrumented_iffalse
                instrumented_bb.append(block_item)
                # even if there is no else, a BB is created, take care of it
                if block_item.iffalse is None:
                    instrumented_bb += self._create_instrumentation_cmds(idx)
                    idx += 1
            elif isinstance(block_item, Assignment) and isinstance(block_item.rvalue, TernaryOp):
                print('\tIN TERNARY')
                # " ...some of you may die, but this is a risk I am willing to take... "
                how_many_bin_ops = self._count_logical_binops(block_item.rvalue.cond)
                for _ in range(how_many_bin_ops):
                    instrumented_bb += self._create_instrumentation_cmds(idx)
                    idx += 1
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                instrumented_bb.append(block_item)
            elif isinstance(block_item, For) or isinstance(block_item, While) or isinstance(block_item, DoWhile):
                print('\tIN FOR/WHILE/DOWHILE')
                # before if/while/dowhile
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                # cond
                how_many_bin_ops = self._count_logical_binops(block_item.cond)
                for _ in range(how_many_bin_ops):
                    instrumented_bb += self._create_instrumentation_cmds(idx)
                    idx += 1
                print('\tOPS COUNTED:', how_many_bin_ops)
                # body
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                idx, block_item.stmt = self._process_bb(block_item.stmt, idx)
                if isinstance(block_item, For):
                    # i++
                    block_item.stmt.block_items += self._create_instrumentation_cmds(idx)
                    idx += 1
                instrumented_bb.append(block_item)
            # case 3: right before a simple body item; nothing to do
            else:
                print('\tIN ORDINARY (DO NOTHING)')
                instrumented_bb.append(block_item)

        return idx, Compound(block_items=instrumented_bb)

    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add instrumentation
        '''
        self.function_instrumentation_data = self.instrumentation_data[n.decl.name]
        print('FUNCTION:', n.decl.name, 'SHOULD BE:', len(self.function_instrumentation_data))
        ### step 1: add instrumentation instructions ###
        bbs, n.body = self._process_bb(n.body, 0)
        if n.decl.name in self.kernelFuncs:
            ### step 2: add prologue ###
            n.body.block_items = self.prologue + n.body.block_items
            ### step 3: add epilogue ###
            if isinstance(n.body.block_items[-1], Return):
                n.body.block_items = n.body.block_items[:-1] + self.epilogue + n.body.block_items[-1:]
            else:
                n.body.block_items += self.epilogue
        print('FUNCTION:', n.decl.name, 'COUNTED:', bbs)
        assert len(self.function_instrumentation_data) == bbs

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

    instrumentor = OcludeInstrumentor(kernels, instrumentation_per_function)
    with open(filename, 'w') as f:
        f.write(instrumentor.visit(ast))
