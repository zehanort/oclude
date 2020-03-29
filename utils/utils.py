import os
import subprocess as sp
from sys import stderr
from tempfile import gettempdir
from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import (
    Compound, Decl, PtrDecl, TypeDecl, IdentifierType, ID,
    If, BinaryOp, FuncCall, ExprList, Constant, For,
    DeclList, UnaryOp, Assignment, ArrayRef
)

class Interactor(object):

    def __init__(self, arg):
        self.prompt = '[' + arg.split('.')[0] +  ']'
        self.verbose = False

    def __call__(self, message, prompt=True, nl=True):
        if prompt and nl:
            stderr.write(f'{self.prompt} {message}\n')
        elif prompt:
            stderr.write(f'{self.prompt} {message}')
        elif nl:
            stderr.write(message + '\n')
        else:
            stderr.write(message)

    def set_verbosity(self, verbose):
        self.verbose = verbose

    def run_command(self, text, utility, *rest):
        command = ' '.join([utility, *rest]) if rest else utility
        if text is not None:
            self(text + (f': {command}' if self.verbose else ''))
        cmdout = sp.run(command.split(), stdout=sp.PIPE, stderr=sp.PIPE)
        if (cmdout.returncode != 0):
            self(f'Error while running {utility}. STDERR of command follows:')
            self(cmdout.stderr.decode("ascii"), prompt=False)
            exit(cmdout.returncode)
        return cmdout.stdout.decode('ascii'), cmdout.stderr.decode('ascii')

llvm_instructions = ['add', 'sub', 'mul', 'udiv', 'sdiv', 'urem', 'srem',
                     'fneg', 'fadd', 'fsub', 'fmul', 'fdiv', 'frem', 'shl',
                     'lshr', 'ashr', 'and', 'or', 'xor', 'extractelement',
                     'insertelement', 'shufflevector', 'extractvalue', 'insertvalue',
                     'alloca',
                     'load private', 'load global', 'load constant', 'load local', 'load callee',
                     'store private', 'store global', 'store constant', 'store local', 'store callee',
                     'fence', 'cmpxchg', 'atomicrmw', 'getelementptr',
                     'ret', 'br', 'switch', 'indirectbr', 'invoke', 'call', 'callbr', 'resume', 'catchswitch',
                     'catchret', 'cleanupret', 'unreachable', 'trunc', 'zext', 'sext', 'fptrunc', 'fpext',
                     'fptoui', 'fptosi', 'uitofp', 'sitofp', 'ptrtoint', 'inttoptr', 'bitcast', 'addrspacecast',
                     'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg',
                     'landingpad', 'catchpad', 'cleanuppad']

preprocessor = 'cpp'

bindir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')

templlvm = os.path.join(gettempdir(), '.oclude_tmp_instr_ll.ll')

hidden_counter_name_local = 'ocludeHiddenCounterLocal'
hidden_counter_name_global = 'ocludeHiddenCounterGlobal'

prologue = f'''if (get_local_id(0) == 0)
    for (int i = 0; i < {len(llvm_instructions)}; i++)
        {hidden_counter_name_local}[i] = 0;
barrier(CLK_GLOBAL_MEM_FENCE);
'''

epilogue = f'''barrier(CLK_GLOBAL_MEM_FENCE);
if (get_local_id(0) == 0) {{
    int glid = get_group_id(0) * {len(llvm_instructions)};
    for (int i = glid; i < glid + {len(llvm_instructions)}; i++)
        {hidden_counter_name_global}[i] = {hidden_counter_name_local}[i - glid];
}}
'''

hiddenCounterLocalArgument = Decl(
    name=hidden_counter_name_local,
    quals=['__local'],
    storage=[],
    funcspec=[],
    type=PtrDecl(
        quals=[],
        type=TypeDecl(
            declname=hidden_counter_name_local,
            quals=['__local'],
            type=IdentifierType(names=['uint'])
        )
    ),
    init=None,
    bitsize=None
)

hiddenCounterGlobalArgument = Decl(
    name=hidden_counter_name_global,
    quals=['__global'],
    storage=[],
    funcspec=[],
    type=PtrDecl(
        quals=[],
        type=TypeDecl(
            declname=hidden_counter_name_global,
            quals=['__global'],
            type=IdentifierType(names=['uint'])
        )
    ),
    init=None,
    bitsize=None
)

# this is the prologue of the instrumentation of every kernel in OpenCL:
#
# if (get_local_id(0) == 0)
#     for (int i = 0; i < <len(llvm_instructions)>; i++)
#         <hidden_counter_name_local>[i] = 0;
# barrier(CLK_GLOBAL_MEM_FENCE);
#
# and this is its AST:

prologue = [
    If(cond=BinaryOp(op='==',
                     left=FuncCall(name=ID(name='get_local_id'),
                                   args=ExprList(exprs=[Constant(type='int', value='0')])),
                     right=Constant(type='int', value='0')),
       iftrue=For(init=DeclList(decls=[Decl(name='i', quals=[], storage=[], funcspec=[],
                                type=TypeDecl(declname='i', quals=[], type=IdentifierType(names=['int'])),
                                init=Constant(type='int', value='0'), bitsize=None)]),
                  cond=BinaryOp(op='<', left=ID(name='i'), right=Constant(type='int', value=str(len(llvm_instructions)))),
                  next=UnaryOp(op='p++', expr=ID(name='i')),
                  stmt=Assignment(op='=', lvalue=ArrayRef(name=ID(name=hidden_counter_name_local), subscript=ID(name='i')),
                                          rvalue=Constant(type='int', value='0'))),
       iffalse=None),
    FuncCall(name=ID(name='barrier'), args=ExprList(exprs=[ID(name='CLK_GLOBAL_MEM_FENCE')]))
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

epilogue = [
    FuncCall(name=ID(name='barrier'), args=ExprList(exprs=[ID(name='CLK_GLOBAL_MEM_FENCE')])),
    If(cond=BinaryOp(op='==',
                     left=FuncCall(name=ID(name='get_local_id'),
                                   args=ExprList(exprs=[Constant(type='int', value='0')])),
                     right=Constant(type='int', value='0')),
       iftrue=Compound(block_items=[
                            Decl(name='glid', quals=[], storage=[], funcspec=[],
                                 type=TypeDecl(declname='glid', quals=[], type=IdentifierType(names=['int'])),
                                 init=BinaryOp(op='*', left=FuncCall(name=ID(name='get_group_id'),
                                               args=ExprList(exprs=[Constant(type='int', value='0')])),
                                               right=Constant(type='int', value=str(len(llvm_instructions)))),
                                 bitsize=None),
                            For(init=DeclList(decls=[Decl(name='i', quals=[], storage=[], funcspec=[],
                                              type=TypeDecl(declname='i', quals=[], type=IdentifierType(names=['int'])),
                                              init=ID(name='glid'), bitsize=None)]),
                                cond=BinaryOp(op='<', left=ID(name='i'),
                                              right=BinaryOp(op='+', left=ID(name='glid'),
                                                             right=Constant(type='int', value=str(len(llvm_instructions))))),
                                next=UnaryOp(op='p++', expr=ID(name='i')),
                                stmt=Assignment(op='=', lvalue=ArrayRef(name=ID(name=hidden_counter_name_global), subscript=ID(name='i')),
                                                rvalue=ArrayRef(name=ID(name=hidden_counter_name_local),
                                                subscript=BinaryOp(op='-', left=ID(name='i'), right=ID(name='glid')))))]),
       iffalse=None)
]

class OcludeFormatter(OpenCLCGenerator):
    '''
    2 additions regarding OpenCLCGenerator:
        1. add missing curly braces around if/else/for/do while/while
        2. add hidden oclude buffers
    '''

    def __init__(self, funcCallsToEdit, kernelFuncs):
        super().__init__()
        self.funcCallsToEdit = funcCallsToEdit
        self.kernelFuncs = kernelFuncs

    def _add_braces_around_stmt(self, n):
        if not isinstance(n.stmt, Compound):
            return Compound(block_items=[n.stmt])
        return n.stmt

    def visit_If(self, n):
        if n.iftrue is not None and not isinstance(n.iftrue, Compound):
            n.iftrue = Compound(block_items=[n.iftrue])
        if n.iffalse is not None and not isinstance(n.iffalse, Compound):
            n.iffalse = Compound(block_items=[n.iffalse])
        return super().visit_If(n)

    def visit_For(self, n):
        n.stmt = self._add_braces_around_stmt(n)
        return super().visit_For(n)

    def visit_While(self, n):
        n.stmt = self._add_braces_around_stmt(n)
        return super().visit_While(n)

    def visit_DoWhile(self, n):
        n.stmt = self._add_braces_around_stmt(n)
        return super().visit_DoWhile(n)

    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add hidden oclude buffers
        '''
        n.decl.type.args.params.append(hiddenCounterLocalArgument)
        if n.decl.name in self.kernelFuncs:
            n.decl.type.args.params.append(hiddenCounterGlobalArgument)
        return super().visit_FuncDef(n)

    def visit_FuncCall(self, n):
        '''
        Overrides visit_FuncCall to add hidden oclude buffers
        '''
        if n.name.name in self.funcCallsToEdit:
            x = n.args.exprs.append(ID(hidden_counter_name_local))
        return super().visit_FuncCall(n)

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

    def _create_instrumentation_cmds(self, idx):
        '''
        idx points to an entry of self.function_instrumentation_data, which is
        a list of tuples (instr_idx, instr_cnt), and creates the AST representation of the command
        "atomic_add(&<hidden_local_counter>[instr_idx], instr_cnt);" for each tuple.
        Returns the list of these representations
        '''
        instr = []
        for instr_idx, instr_cnt in self.function_instrumentation_data[idx]:
            instr.append(
                FuncCall(name=ID(name='atomic_add'),
                         args=ExprList(exprs=[
                                           UnaryOp(op='&', expr=ArrayRef(name=ID(name=hidden_counter_name_local),
                                                   subscript=Constant(type='int', value=instr_idx))),
                                           Constant(type='int', value=instr_cnt)
                                       ]
                              )
                )
            )
        return instr

    def _process_bb(self, bb, idx):

        instrumented_bb = []

        for block_item in bb + [None]:
            # case 1: reached the end of bb
            if block_item is None or isinstance(block_item, Return):
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                if block_item is not None:
                    instrumented_bb.append(block_item)
                break
            # case 2: right before a compound; need to add instrumentation cmds
            #         several subcases need to be taken into consideration
            elif isinstance(block_item, Compound):
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                idx, internal_instrumented_bb = self._process_bb(block_item, idx)
                instrumented_bb += internal_instrumented_bb
                instrumented_bb.append(block_item)
            elif isinstance(block_item, If):
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                idx, instrumented_iftrue = self._process_bb(block_item.iftrue, idx)
                block_item.iftrue = instrumented_iftrue
                idx, instrumented_iffalse = self._process_bb(block_item.iffalse, idx)
                block_item.iffalse = instrumented_iffalse
                instrumented_bb.append(block_item)
            elif isinstance(block_item, For) or isinstance(block_item, While) or isinstance(block_item, DoWhile):
                instrumented_bb += self._create_instrumentation_cmds(idx)
                idx += 1
                idx, block_item.stmt = self._process_bb(block_item.stmt, idx)
                instrumented_bb.append(block_item)
            # case 3: right before a simple body item; nothing to do
            else:
                instrumented_bb.append(block_item)

        return idx, instrumented_bb

    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add instrumentation
        '''
        self.function_instrumentation_data = self.instrumentation_data[n.decl.name]
        ### step 1: add instrumentation instructions ###
        _, n.body.block_items = self._process_bb(n.body.block_items, 0)
        if n.name.name in self.kernelFuncs:
            ### step 2: add prologue ###
            n.body.block_items = self.prologue + n.body.block_items
            ### step 3: add epilogue ###
            if isinstance(n.body.block_items[-1], Return):
                n.body.block_items = n.body.block_items[:-1] + self.epilogue + n.body.block_items[-1:]
            else:
                n.body.block_items += self.epilogue

        return super().visit_FuncDef(n)

def add_instrumentation_data_to_file(filename, kernels, instr_data_raw):
    '''
    returns a dictionary "line (int): code to add (string)"
    '''

    from collections import defaultdict

    def write_incr(key, val):
        return f'atomic_add(&{hidden_counter_name_local}[{key}], {val});'

    def write_decr_ret(val):
        '''
        needed to balance out the "call"s that were removed due to inlined functions
        '''
        return f'atomic_sub(&{hidden_counter_name_local}[{llvm_instructions.index("ret")}], {val});'

    # parse instrumentation data and create an instrumentation dict for each function
    instr_data_lines = sorted(instr_data_raw.splitlines(), key=lambda x : int(x.split('|')[0].split(':')[1]))
    instr_data_dicts = defaultdict(list)
    previous_function_name, previous_function_line = instr_data_lines[0].split('|')[0].split(':')

    instr_data_dict = defaultdict(str)

    for line in instr_data_lines:
        data = list(filter(None, line.split('|')))
        current_function_name, current_function_line = data[0].split(':')
        data = data[1:]
        bb_instrumentation_data = [0] * (len(llvm_instructions) + 1) # +1 for ret negation (inlined functions)

        # new function? (done with all BBs of the previous one)
        if current_function_name != previous_function_name:
            instr_data_dicts[previous_function_name, int(previous_function_line)].append(instr_data_dict)
            previous_function_name, previous_function_line = current_function_name, current_function_line
            instr_data_dict = defaultdict(str)

        for datum in data:
            [lineno, instruction] = datum.split(':')
            if instruction == 'retNOT':
                bb_instrumentation_data[-1] += 1
            else:
                bb_instrumentation_data[llvm_instructions.index(instruction)] += 1
        for instruction_index, instruction_cnt in enumerate(bb_instrumentation_data):
            if instruction_cnt > 0:
                # is it a ret negation due to an inlined function?
                if instruction_index == len(bb_instrumentation_data) - 1:
                    instr_data_dict[int(current_function_line)] += write_decr_ret(instruction_cnt)
                else:
                    instr_data_dict[int(current_function_line)] += write_incr(instruction_index, instruction_cnt)

    instr_data_dicts[(previous_function_name, int(previous_function_line))].append(instr_data_dict)

    # sort instrumentation order as appeared in source file text and some mumbo-jumbo restructuring
    # mainly to get rid of defaultdicts; final structure is explained in the comments below
    instr_data_dicts = list(map(list, instr_data_dicts.items()))
    instr_data_list = [(x, *list(map(lambda defdict : list(defdict.items()), y))) for x, y in instr_data_dicts]
    instr_data_list = [(x, sorted(y, key=lambda k : k[0])) for x, y in instr_data_list]
    # at this point, instr_data_list holds instrumentation information in the following form:
    # each entry is a tuple of the form ((function_name, function_line), instrumentation_data)
    # the instrumentation_data is a list of tuples. Each tuple corresponds to a BB of the function
    # each tuple holds the information (line to enter code -i.e. first line of the BB-, code -a string-)

    # uncomment the following segment to see it for yourself:
    for (fn, fl), instrd in instr_data_list:
        print('function', fn, 'line', fl)
        for instrl, instrc in instrd:
            print(f'\tinsert following code at line {instrl}: {instrc}')
            print()
    exit(0)

    # now modify the file in place with the instr_data dicts
    # each instr_data (1 per function) is a dict <line:instrumentation_data>
    with open(filename, 'r') as f:
        filedata = f.readlines()
    offset = 0
    insertion_line = 0
    added_prologue = defaultdict(bool)

    for (function_name, function_line), instr_data in instr_data_list:
        # firstly, add code at the start of kernels to initialize local counter buffer to 0
        if function_name in kernels and not added_prologue[function_name]:
            filedata.insert(function_line + offset, prologue)
            offset += len(prologue.splitlines())
            added_prologue[function_name] = True
        for lineno, instr_string in instr_data:
            # must add instrumentation data between the previous line and this one
            insertion_line = lineno + offset
            filedata.insert(insertion_line, instr_string + '\n')
            offset += 1
        insertion_line += 1
        # lastly, add code at the end of kernels to copy local buffer to the respective space in the global one
        if function_name in kernels:
            filedata.insert(insertion_line, epilogue)
            offset += len(epilogue.splitlines())

    # done; write the instrumented source back to file
    with open(filename, 'w') as f:
        f.writelines(filedata)
