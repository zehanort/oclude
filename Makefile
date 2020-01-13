.PHONY: clean distclean default

CXX=g++
CXXFLAGS=-std=c++17 -O3 -Wall -Wno-ignored-attributes -Werror
LDFLAGS=-lOpenCL

CXXFLAGS_UTILS=-std=c++17 -O3 -Wall `llvm-config --cxxflags`
LDFLAGS_UTILS=`llvm-config --ldflags --system-libs --libs all`

SRC=utils/src
BUILD=utils/build
BIN=utils/bin

default: $(BIN)/hostcode-wrapper $(BIN)/instrumentation-parser

$(BUILD)/typegen.o: $(SRC)/typegen.cpp $(SRC)/typegen.hpp
	mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) -c -o $@ $< $(LDFLAGS)

$(BIN)/hostcode-wrapper: $(SRC)/hostcode-wrapper.cpp $(BUILD)/typegen.o
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN)/instrumentation-parser: $(SRC)/instrumentation-parser.cpp
	mkdir -p $(BIN)
	$(CXX) $(CXXFLAGS_UTILS) -o $@ $^ $(LDFLAGS_UTILS)

clean:
	$(RM) -rf $(BIN) $(BUILD)

distclean: clean
