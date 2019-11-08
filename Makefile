.PHONY: clean distclean default

CC=gcc
CFLAGS=

CXX=g++
CXXFLAGS=-std=c++11 -Wall -Werror
LDFLAGS=-lOpenCL

default: oclude

oclude: oclude.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
	cd utils; $(MAKE)

clean:
	$(RM) oclude
	cd utils; $(MAKE) clean

distclean: clean
