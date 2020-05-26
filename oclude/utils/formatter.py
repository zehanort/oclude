from .constants import hidden_counter_name_local, hidden_counter_name_global

from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import *

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

        self.hiddenCounterLocalArgument = Decl(
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

        self.hiddenCounterGlobalArgument = Decl(
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

    def _add_missing_braces(self, stmt):
        if stmt is not None and not isinstance(stmt, Compound):
            return Compound(block_items=[stmt])
        return stmt

    def visit_If(self, n):
        n.iftrue = self._add_missing_braces(n.iftrue)
        n.iffalse = self._add_missing_braces(n.iffalse)
        return super().visit_If(n)

    def visit_For(self, n):
        n.stmt = self._add_missing_braces(n.stmt)
        return super().visit_For(n)

    def visit_While(self, n):
        n.stmt = self._add_missing_braces(n.stmt)
        return super().visit_While(n)

    def visit_DoWhile(self, n):
        n.stmt = self._add_missing_braces(n.stmt)
        return super().visit_DoWhile(n)

    def visit_FuncDef(self, n):
        '''
        Overrides visit_FuncDef to add hidden oclude buffers
        '''
        n.decl.type.args.params.append(self.hiddenCounterLocalArgument)
        if n.decl.name in self.kernelFuncs:
            n.decl.type.args.params.append(self.hiddenCounterGlobalArgument)
        return super().visit_FuncDef(n)

    def visit_FuncCall(self, n):
        '''
        Overrides visit_FuncCall to add hidden oclude buffers
        '''
        if n.name.name in self.funcCallsToEdit:
            n.args.exprs.append(ID(hidden_counter_name_local))
        return super().visit_FuncCall(n)
