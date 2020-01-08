import os
from sys import stderr

class MessagePrinter(object):
    def __init__(self, arg):
        self.prompt = '[' + arg.split('.')[0] +  ']'
    def __call__(self, message, prompt=True, nl=True):
        if prompt and nl:
            stderr.write(f'{self.prompt} {message}\n')
        elif prompt:
            stderr.write(f'{self.prompt} {message}')
        elif nl:
            stderr.write(message + '\n')
        else:
            stderr.write(message)

llvm_instructions = ['add', 'sub', 'mul', 'udiv', 'sdiv', 'urem', 'srem',
                     'fneg', 'fadd', 'fsub', 'fmul', 'fdiv', 'frem', 'shl',
                     'lshr', 'ashr', 'and', 'or', 'xor', 'extractelement',
                     'insertelement', 'shufflevector', 'extractvalue', 'insertvalue',
                     'alloca', 'load', 'store', 'fence', 'cmpxchg', 'atomicrmw', 'getelementptr',
                     'ret', 'br', 'switch', 'indirectbr', 'invoke', 'call', 'callbr', 'resume', 'catchswitch',
                     'catchret', 'cleanupret', 'unreachable', 'trunc', 'zext', 'sext', 'fptrunc', 'fpext',
                     'fptoui', 'fptosi', 'uitofp', 'sitofp', 'ptrtoint', 'inttoptr', 'bitcast', 'addrspacecast',
                     'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg',
                     'landingpad', 'catchpad', 'cleanuppad']

tempfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.oclude_tmp_instr_src.cl')
templlvm = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.oclude_tmp_instr_ll.ll')

hidden_counter_name_local = 'ocludeHiddenCounterLocal'
hidden_counter_name_global = 'ocludeHiddenCounterGlobal'

epilogue = f'''barrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);
if (get_local_id(0) == 0) {{
    int glid = get_group_id(0) * {len(llvm_instructions)};
    for (int i = glid; i < glid + {len(llvm_instructions)}; i++)
        {hidden_counter_name_global}[i] = {hidden_counter_name_local}[i - glid];
}}
'''

def add_instrumentation_data_to_file(filename, kernels, instr_data_raw):
    '''
    returns a dictionary "line (int): code to add (string)"
    '''

    from collections import defaultdict

    def write_incr(key, val):
        '''
        returns the instrumentation string
        '''
        return f'atomic_add(&{hidden_counter_name_local}[{key}], {val});'

    # parse instrumentation data and create an instrumentation dict for each function
    instr_data_lines = instr_data_raw.splitlines()
    instr_data_dicts = defaultdict(list)
    previous_function_name, previous_function_line = instr_data_lines[0].split('|')[0].split(':')

    instr_data_dict = defaultdict(str)

    for line in instr_data_lines:
        data = list(filter(None, line.split('|')))
        current_function_name, current_function_line = data[0].split(':')
        data = data[1:]
        bb_instrumentation_data = [0] * len(llvm_instructions)

        # new function? (done with all BBs of the previous one)
        if current_function_name != previous_function_name:
            instr_data_dicts[previous_function_name, int(previous_function_line)].append(instr_data_dict)
            previous_function_name, previous_function_line = current_function_name, current_function_line
            instr_data_dict = defaultdict(str)

        for datum in data:
            [lineno, instruction] = datum.split(':')
            bb_instrumentation_data[llvm_instructions.index(instruction)] += 1
        for instruction_index, instruction_cnt in enumerate(bb_instrumentation_data):
            if instruction_cnt > 0:
                instr_data_dict[int(lineno)] += write_incr(instruction_index, instruction_cnt)

    instr_data_dicts[(current_function_name, int(current_function_line))].append(instr_data_dict)

    # sort instrumentation order as appeared in source file text and some mumbo-jumbo restructuring
    # mainly to get rid of defaultdicts; final structure is explained in the comments below
    instr_data_dicts = sorted(list(instr_data_dicts.items()), key=lambda x : x[0][1])
    instr_data_dicts = list(map(lambda x : list(x), instr_data_dicts))
    instr_data_list = [(x, *list(map(lambda defdict : list(defdict.items()), y))) for x, y in instr_data_dicts]
    # at this point, instr_data_list holds instrumentation information in the following form:
    # each entry is a tuple of the form ((function_name, function_line), instrumentation_data)
    # the instrumentation_data is a list of tuples. Each tuple corresponds to a BB of the function
    # each tuple holds the information (line to enter code -i.e. first line of the BB-, code -a string-)

    # uncomment the following segment to see it for yourself:
    # for (fn, fl), instrd in instr_data_list:
    #     print('function', fn, 'line', fl)
    #     for instrl, instrc in instrd:
    #         print(f'\tinsert following code at line {instrl}: {instrc}')
    # exit(0)

    # now modify the file in place with the instr_data dicts
    # each instr_data (1 per function) is a dict <line:instrumentation_data>
    with open(filename, 'r') as f:
        filedata = f.readlines()
    offset = -1
    insertion_line = 0

    for (function_name, function_line), instr_data in instr_data_list:
        for lineno, instr_string in instr_data:
            # must add instrumentation data between the previous line and this one
            insertion_line = lineno + offset
            filedata.insert(insertion_line, instr_string + '\n')
            offset += 1
        insertion_line += 1
        # lastly, add code at the end of kernels to copy local buffer to the respective space in the global one
        if function_name in kernels:
            filedata.insert(insertion_line, epilogue)
            offset += 1

    # done; write the instrumented source back to file
    with open(filename, 'w') as f:
        f.writelines(filedata)
