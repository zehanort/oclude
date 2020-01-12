.PHONY: clean distclean default

CXX=g++
CXXFLAGS=-std=c++17 -O3 -Wall -Wno-ignored-attributes -Werror
LDFLAGS=-lOpenCL

CXXFLAGS_UTILS=-std=c++14 -O3 -Wall `llvm-config --cxxflags`
LDFLAGS_UTILS=`llvm-config --ldflags --system-libs --libs all`

default: hostcode-wrapper utils/instrumentation-parser

hostcode-wrapper: hostcode-wrapper.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

utils/instrumentation-parser: utils/instrumentation-parser.cpp
	$(CXX) $(CXXFLAGS_UTILS) -o $@ $^ $(LDFLAGS_UTILS)

clean:
	$(RM) hostcode-wrapper utils/instrumentation-parser

distclean: clean
