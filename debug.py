#!/usr/bin/env python
#-*- coding: UTF-8 -*-
import time
import sys

INICIO = time.time()
VERBOSE = 1

def debug(*args):
    if VERBOSE:
        sys.stderr.writelines("".join(
            ["%7.2f" % (time.time() - INICIO),
            " ",
            " ". join([str(e) for e in args]) + "\n",
            ])) 
