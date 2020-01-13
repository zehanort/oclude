.PHONY: clean distclean default

SRC=utils/src
BUILD=utils/build
BIN=utils/bin
INC=utils/inc

CXX=g++
CXXFLAGS=-std=c++17 -O3 -Wall -Wno-ignored-attributes -Werror -I./$(INC)
LDFLAGS=-lOpenCL

CXXFLAGS_UTILS=-std=c++17 -O3 -Wall `llvm-config --cxxflags` -I./$(INC)
LDFLAGS_UTILS=`llvm-config --ldflags --system-libs --libs all`

default: $(BIN)/hostcode-wrapper $(BIN)/instrumentation-parser

$(BUILD)/typegen.o: $(SRC)/typegen.cpp $(INC)/typegen.hpp
	mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) -c -o $@ $< $(LDFLAGS)

$(BIN)/hostcode-wrapper: $(SRC)/hostcode-wrapper.cpp $(INC)/hostcode-wrapper.hpp $(BUILD)/typegen.o
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN)/instrumentation-parser: $(SRC)/instrumentation-parser.cpp $(INC)/instrumentation-parser.hpp
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS_UTILS) -o $@ $^ $(LDFLAGS_UTILS)

clean:
	$(RM) -rf $(BUILD)

distclean: clean
	$(RM) -rf $(BIN)
