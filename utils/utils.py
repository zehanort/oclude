import os

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

tempfile = '.oclude_tmp_instr_src.cl'
templlvm = '.oclude_tmp_instr_ll.ll'

hidden_counter_name_local = 'ocludeHiddenCounterLocal'
hidden_counter_name_global = 'ocludeHiddenCounterGlobal'
counterBufferLocal = f', __local uint *{hidden_counter_name_local}'
counterBufferGlobal = f', __global uint *{hidden_counter_name_global}'
# only the following will be exported and used by the instrumentor
counterBuffers = counterBufferLocal + ' ' + counterBufferGlobal

epilogue = f'''if (get_local_id(0) == 0) {{
    int glid = get_group_id(0) * {len(llvm_instructions)};
    for (int i = glid; i < glid + {len(llvm_instructions)}; i++)
        {hidden_counter_name_global}[i] = {hidden_counter_name_local}[i - glid];
        // {hidden_counter_name_global}[i] = get_group_id(0);
}}
'''

def remove_comments(src):
    ### modified version of: http://www.cmycode.com/2016/02/program-for-remove-comments-c.html ###
    COMMENT_START = '/'
    ONELINE_COMMENT = 1
    MULTILINE_COMMENT = 2

    retsrc = ''
    escape = False
    comment_type = 0
    skip_new_line = False
    string_started = False
    comment_ending = False
    comment_started = False

    for c in src:

        if skip_new_line:
            skip_new_line = False
            if c == '\n':
                continue

        if comment_type == ONELINE_COMMENT:
            if c == '\\':
                escape = not escape
            elif c == '\n' and not escape:
                comment_type = 0
                comment_started = False
                retsrc += c
            else:
                escape = False
            continue

        if comment_type == MULTILINE_COMMENT:
            if comment_ending:
                if c == COMMENT_START:
                    comment_ending = False
                    comment_started = False
                    comment_type = 0
                    skip_new_line = True
                    continue
                comment_ending = False
            if c == '*':
                comment_ending = True
            continue

        if comment_started:
            if c == '*':
                comment_type = MULTILINE_COMMENT
                continue
            if c == COMMENT_START:
                comment_type = ONELINE_COMMENT
                continue
            retsrc += COMMENT_START
            comment_started = False

        if string_started:
            if c == '\\':
                escape = not escape
            elif c == '"' and not escape:
                string_started = False
            else:
                escape = False
            retsrc += c
            continue

        if c == '"':
            string_started = True

        if c == COMMENT_START:
            comment_started = True
            continue

        retsrc += c

    # return the source string without empty lines
    return os.linesep.join([line for line in retsrc.splitlines() if line])

def instrument_sourcefile(filename, instr_data_raw):
    '''
    returns a dictionary "line (int): code to add (string)"
    '''

    from collections import defaultdict

    def write_incr(key, val):
        '''
        returns the instrumentation string
        '''
        return f'atomic_add(&{hidden_counter_name_local}[{key}], {val});'

    # parse instrumentation data and create an instrumentation dict
    instr_data_dict = defaultdict(str)
    for line in instr_data_raw.splitlines():
        bb_instrumentation_data = [0] * len(llvm_instructions)
        data = filter(None, line.split('|')[1:])
        for datum in data:
            [lineno, instruction] = datum.split(':')
            bb_instrumentation_data[llvm_instructions.index(instruction)] += 1
        for instruction_index, instruction_cnt in enumerate(bb_instrumentation_data):
            if instruction_cnt > 0:
                instr_data_dict[int(lineno)] += write_incr(instruction_index, instruction_cnt)

    # now modify the file in place with the instr_data dict
    # the instr_data is a dict <line:instrumentation_data>
    with open(filename, 'r') as f:
        filedata = f.readlines()
    offset = -1
    insertion_line = 0
    for lineno in instr_data_dict.keys():
        # must add instrumentation data between the previous line and this one
        insertion_line = lineno + offset
        filedata.insert(insertion_line, instr_data_dict[lineno] + '\n')
        offset += 1
    insertion_line += 1

    # lastly, add code at the end to copy local buffer to the respective space in the global one
    filedata.insert(insertion_line, epilogue)

    # done; write the instrumented source back to file
    with open(filename, 'w') as f:
        f.writelines(filedata)
