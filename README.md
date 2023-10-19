# AMN

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
![Tests](https://github.com/Deric-W/AMN/actions/workflows/Tests.yaml/badge.svg)
[![codecov](https://codecov.io/gh/Deric-W/AMN/branch/main/graph/badge.svg?token=SU3982mC17)](https://codecov.io/gh/Deric-W/AMN)

The AMN package implements a simple virtual machine for the AM0 and AM1 instructions sets.

To use it, simply execute it with `python3 -m AMN -i <instruction set> exec path/to/file.txt` to execute the instructions written in a file.

If you want an interactive console just use `python3 -m AMN -i <instruction set> repl`.

## Requirements

Python >= 3.10 is required to use the utility.

## Installation

```sh
python3 -m pip install AMN
```

## Examples

The REPL (read eval print loop) in action:

```
python3 -m AMN -i am0 repl
Welcome the the AM0 REPL, type 'help' for help
AM0 >> exec READ 0
Input: 8
AM0 >> exec READ 1
Input: 42
AM0 >> exec LOAD 0
AM0 >> exec LOAD 1
AM0 >> exec GT
AM0 >> exec JMC 24
AM0 >> status
Counter: 24
Stack: []
Memory:
    0 := 8
    1 := 42
AM0 >> exit
Exiting REPL...
```

Example program which outputs the biggest of two numbers:

```
READ 0;
READ 1;
LOAD 0;
LOAD 1;
GT;
JMC 10;
LOAD 0;
STORE 2;
JMP 12;
LOAD 1;
STORE 2;
WRITE 2;
```
