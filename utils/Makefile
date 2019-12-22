.PHONY: clean distclean default

CXX=g++
CXXFLAGS=-std=c++14 `llvm-config --cxxflags`
LDFLAGS=`llvm-config --ldflags --system-libs --libs all`

default: instrumentation-parser

instrumentation-parser: instrumentation-parser.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	$(RM) instrumentation-parser

distclean: clean
