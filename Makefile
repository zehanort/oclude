.PHONY: clean distclean default

CC=gcc
CFLAGS=

CXX=g++
CXXFLAGS=-std=c++17 -Wall -Wno-ignored-attributes -Werror -O3
LDFLAGS=-lOpenCL

default: hostcode-wrapper

hostcode-wrapper: hostcode-wrapper.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
	cd utils; $(MAKE)

clean:
	$(RM) hostcode-wrapper
	cd utils; $(MAKE) clean

distclean: clean
