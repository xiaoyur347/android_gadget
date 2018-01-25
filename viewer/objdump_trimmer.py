#!/usr/bin/env python
# Trim objdump output to make it easier to compare the library difference
# usage: arm-linux-androideabi-objdump -dw ./libnative.so | objdump_trimmer.py
from __future__ import print_function

import sys


def is_number(c):
    return '0' <= c <= '9'


def is_hex(c):
    if '0' <= c <= '9':
        return True
    if 'a' <= c <= 'f':
        return True
    if 'A' <= c <= 'F':
        return True
    return False


def print_normal(line):
    print(line)


# <SomeFunction>
def print_function_header(line):
    pos = line.find('<')
    if pos < 0:
        print_normal(line)
        return

    print(line[pos:])


def print_indent_content(line):
    print("\t" + line)


# 94e0: \tb928 \tcbnz	r0, 94ee <SomeFunction+0x292>
def print_function_content(line):
    pos = line.find(':')
    if pos < 0:
        print_normal(line)
        return
    line = line[pos:]

    # trim to address before, like b928
    pos = line.find('\t')
    if pos < 0:
        print("unexpected")
        sys.exit(1)
    line = line[pos+1:]

    # trim to dessemble before, like cbnz
    pos = line.find('\t')
    if pos < 0:
        print("unexpected")
        sys.exit(1)
    line = line[pos+1:]

    # cut 94ee <SomeFunction+0x292>
    # to <SomeFunction+0x292>
    pos = line.find('<')
    if pos < 0:
        print_indent_content(line)
        return
    
    num_right = pos - 1
    while num_right >= 0:
        if line[num_right] == ' ':
            num_right = num_right - 1
        else:
            break
    
    num_left = num_right
    while num_left >= 0:
        if is_hex(line[num_left]):
            num_left = num_left - 1
        else:
            break
    line = line[0:num_left] + line[num_right+1:]
    print_indent_content(line)


def main():
    while True:
        line = sys.stdin.readline()
        if len(line) == 0:
            break
        line = line.strip('\n')
        line = line.strip('\r')
        if len(line) == 0:
            # print empty line
            print()
            continue

        if not line[0] == ' ':
            if is_number(line[0]):
                print_function_header(line)
            else:
                print_normal(line)
        else:
            print_function_content(line)


if __name__ == '__main__':
    main()
