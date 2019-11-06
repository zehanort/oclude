.PHONY: clean distclean default

CC=gcc
CFLAGS=

CXX=g++
CXXFLAGS=-std=c++11 -Wall -Werror
LDFLAGS=-lOpenCL

default: oclude commentsout

oclude: oclude.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

commentsout: commentsout.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	$(RM) oclude commentsout

distclean: clean
