.PHONY: clean distclean default

CXX=g++
CXXFLAGS=-std=c++11 -Wall -Werror
LDFLAGS=-lOpenCL

default: oclude

oclude: oclude.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	$(RM) oclude

distclean: clean
