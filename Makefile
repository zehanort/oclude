.PHONY: clean distclean default

SRC=utils/src
BIN=utils/bin
INC=utils/inc

CXX=g++
CXXFLAGS=-std=c++17 -O3 -Wall -Wno-ignored-attributes -Werror -I./$(INC)
LDFLAGS=-lOpenCL

CXXFLAGS_UTILS=-std=c++17 -O3 -Wall `llvm-config --cxxflags` -I./$(INC)
LDFLAGS_UTILS=`llvm-config --ldflags --system-libs --libs all`

MSGPRINTER=$(INC)/message-printer.hpp

default: $(BIN)/instrumentation-parser

$(BIN)/instrumentation-parser: $(SRC)/instrumentation-parser.cpp $(INC)/instrumentation-parser.hpp $(MSGPRINTER)
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS_UTILS) -o $@ $^ $(LDFLAGS_UTILS)

clean:
	$(RM) -rf $(BIN)

distclean: clean
