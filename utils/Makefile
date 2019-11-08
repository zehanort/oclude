.PHONY: clean distclean default

CXX=g++
CXXFLAGS=-std=c++14 `llvm-config --cxxflags`
LDFLAGS=`llvm-config --ldflags --system-libs --libs all` /usr/lib/x86_64-linux-gnu/libfl.a

default: instrumentation-parser

instrumentation-parser: instrumentation-parser.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	$(RM) instrumentation-parser

distclean: clean
