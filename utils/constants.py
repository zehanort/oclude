import os
from tempfile import gettempdir

########################
### OCLUDE CONSTANTS ###
########################
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
