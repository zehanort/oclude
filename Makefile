.PHONY: clean distclean default

SRC=oclude/utils/src
BIN=oclude/utils/bin
INC=oclude/utils/inc

CXX=g++
CXXFLAGS=-std=c++17 -O3 -Wall -Wno-ignored-attributes -Werror -I./$(INC)

CXXFLAGS_UTILS=`llvm-config --cxxflags` -I./$(INC)
LDFLAGS_UTILS=`llvm-config --ldflags --system-libs --libs all`

MSGPRINTER=$(INC)/message-printer.hpp

default: $(BIN)/instrumentation-parser

$(BIN)/instrumentation-parser: $(SRC)/instrumentation-parser.cpp $(INC)/instrumentation-parser.hpp $(MSGPRINTER)
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS) $(CXXFLAGS_UTILS) -o $@ $^ $(LDFLAGS_UTILS)

clean:
	$(RM) -rf $(BIN)

distclean: clean
