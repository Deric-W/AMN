#!/usr/bin/python3

"""AM1 Tests"""

from unittest import TestCase
from AMN.am1 import Instruction, Machine, MemoryContext


# do not remove trailing whitespace!
EXAMPLE_PROGRAM1 = \
"""
INIT 2;
CALL 24;
JMP 0;

INIT 0;
LOAD(lokal,-3);
LIT 0;   
GT;
JMC 21;
LOAD(lokal, -3);
LIT 1;
SUB;
PUSH;
LOAD(lokal,-2);
PUSH;
CALL 4;
LOADI(-2);
LIT 2;
ADD;
STOREI(-2);   
JMP 23;
LIT 0;
STOREI(-2);
RET 2;
   
INIT 0;
READ(global,1);
LOAD(global,1);
PUSH;
LOADA(global,2);
PUSH;
CALL 4;
WRITE(global,2);
RET 0; 
"""

EXAMPLE_PROGRAM2 = \
"""
INIT 3;
LIT 1;
STORE 3;
READI 3;
LOAD 1;
LIT 2;
MUL;
LIT 12;
DIV;
LIT 2;
MOD;
STORE 1;
LOAD 1;
LIT 0;
EQ;
LOAD 1;
LIT 0;
NE;
LOAD 1;
LIT 0;
LT;
LOAD 1;
LIT 0;
GT;
LOAD 1;
LIT 1;
LE;
LOAD 1;
LIT 1;
GE;
WRITE 1;
LIT 2;
STORE 3;
STOREI 2;
WRITEI 2;
STOREI 2;
WRITEI 2;
STOREI 2;
WRITEI 2;
STOREI 2;
WRITEI 2;
STOREI 2;
WRITEI 2;
STOREI 2;
WRITEI 2;
"""


class InstructionTest(TestCase):
    """AM1 instruction tests"""

    def test_parse(self) -> None:
        """test instruction parsing"""
        self.assertEqual(
            Instruction.parse("ADD"),
            (Instruction.ADD, MemoryContext.LOKAL, 0)
        )
        self.assertEqual(
            Instruction.parse("JMP 42"),
            (Instruction.JMP, MemoryContext.LOKAL, 42)
        )
        self.assertEqual(
            Instruction.parse("LOAD(lokal,-3)"),
            (Instruction.LOAD, MemoryContext.LOKAL, -3)
        )
        with self.assertRaises(ValueError):
            Instruction.parse("JMP x")
        with self.assertRaises(KeyError):
            Instruction.parse("XXX")
        with self.assertRaises(ValueError):
            Instruction.parse("LOAD lokal,-3")
        with self.assertRaises(KeyError):
            Instruction.parse("LOAD(xxx,-3)")
        with self.assertRaises(ValueError):
            Instruction.parse("LOAD(lokal,xxx)")

    def test_parse_program(self) -> None:
        """test program parsing"""
        self.assertEqual(
            list(Instruction.parse_program(EXAMPLE_PROGRAM1)),
            [
                (Instruction.INIT, MemoryContext.LOKAL, 2),
                (Instruction.CALL, MemoryContext.LOKAL, 24),
                (Instruction.JMP, MemoryContext.LOKAL, 0),
                (Instruction.INIT, MemoryContext.LOKAL, 0),
                (Instruction.LOAD, MemoryContext.LOKAL, -3),
                (Instruction.LIT, MemoryContext.LOKAL, 0),
                (Instruction.GT, MemoryContext.LOKAL, 0),
                (Instruction.JMC, MemoryContext.LOKAL, 21),
                (Instruction.LOAD, MemoryContext.LOKAL, -3),
                (Instruction.LIT, MemoryContext.LOKAL, 1),
                (Instruction.SUB, MemoryContext.LOKAL, 0),
                (Instruction.PUSH, MemoryContext.LOKAL, 0),
                (Instruction.LOAD, MemoryContext.LOKAL, -2),
                (Instruction.PUSH, MemoryContext.LOKAL, 0),
                (Instruction.CALL, MemoryContext.LOKAL, 4),
                (Instruction.LOADI, MemoryContext.LOKAL, -2),
                (Instruction.LIT, MemoryContext.LOKAL, 2),
                (Instruction.ADD, MemoryContext.LOKAL, 0),
                (Instruction.STOREI, MemoryContext.LOKAL, -2),
                (Instruction.JMP, MemoryContext.LOKAL, 23),
                (Instruction.LIT, MemoryContext.LOKAL, 0),
                (Instruction.STOREI, MemoryContext.LOKAL, -2),
                (Instruction.RET, MemoryContext.LOKAL, 2),
                (Instruction.INIT, MemoryContext.LOKAL, 0),
                (Instruction.READ, MemoryContext.GLOBAL, 1),
                (Instruction.LOAD, MemoryContext.GLOBAL, 1),
                (Instruction.PUSH, MemoryContext.LOKAL, 0),
                (Instruction.LOADA, MemoryContext.GLOBAL, 2),
                (Instruction.PUSH, MemoryContext.LOKAL, 0),
                (Instruction.CALL, MemoryContext.LOKAL, 4),
                (Instruction.WRITE, MemoryContext.GLOBAL, 2),
                (Instruction.RET, MemoryContext.LOKAL, 0)
            ]
        )
        self.assertEqual(list(Instruction.parse_program("")), [])
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1;\nADD\nJMP 3;"))
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1; XXX; ADD;"))
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1;\n ADD;\nJMP 3;"))

    def test_has_payload(self) -> None:
        """test payload information"""
        has_payload = {
            Instruction.LIT,
            Instruction.LOAD,
            Instruction.LOADI,
            Instruction.LOADA,
            Instruction.STORE,
            Instruction.STOREI,
            Instruction.JMP,
            Instruction.JMC,
            Instruction.READ,
            Instruction.READI,
            Instruction.WRITE,
            Instruction.WRITEI,
            Instruction.CALL,
            Instruction.RET,
            Instruction.INIT
        }
        for instruction in Instruction:
            self.assertEqual(
                instruction.has_payload(),
                instruction in has_payload,
                f"invalid payload data for {instruction}"
            )

    def test_is_jump(self) -> None:
        """test jump information"""
        is_jump = {
            Instruction.JMP,
            Instruction.JMC,
            Instruction.CALL,
            Instruction.RET
        }
        for instruction in Instruction:
            self.assertEqual(
                instruction.is_jump(),
                instruction in is_jump,
                f"invalid jump data for {instruction}"
            )

    def test_has_context(self) -> None:
        """test checking whether an instruction has a context"""
        has_context = {
            Instruction.LOAD,
            Instruction.LOADA,
            Instruction.STORE,
            Instruction.READ,
            Instruction.WRITE
        }
        for instruction in Instruction:
            self.assertEqual(
                instruction.has_context(),
                instruction in has_context,
                f"invalid context data for {instruction}"
            )


class MachineTest(TestCase):
    """AM1 machine tests"""

    def test_default(self) -> None:
        """test default state"""
        machine = Machine.default(iter([]))
        self.assertEqual(machine.counter, 1)
        self.assertEqual(machine.stack, [])
        self.assertEqual(machine.runtime_stack, [])
        self.assertEqual(machine.reference_pointer, 0)

    def test_reset(self) -> None:
        """test reset state"""
        iterator = iter(range(0))
        machine = Machine(42, [1, 2], [4, 6], 2, iterator)
        machine.reset()
        self.assertEqual(machine.counter, 1)
        self.assertEqual(machine.stack, [])
        self.assertEqual(machine.runtime_stack, [])
        self.assertEqual(machine.reference_pointer, 0)
        self.assertIs(machine.input, iterator)

    def test_status(self) -> None:
        """test status information"""
        machines = [
            Machine.default(iter([])),
            Machine(42, [1, 2], [4, 6], 2, iter(range(9)))
        ]
        for machine in machines:
            status = machine.status()
            self.assertIn("Counter", status)
            self.assertIn("Stack", status)
            self.assertIn("Runtime Stack", status)
            self.assertIn("Reference Pointer", status)

    def test_state(self) -> None:
        """test state representation"""
        self.assertEqual(
            Machine.default(iter(range(3))).state([], []),
            "(1, ε, ε, 0, ε, ε)"
        )
        self.assertEqual(
            Machine(42, [1, 2], [4, 6], 2, iter(range(9))).state(range(1, 3), range(2)),
            "(42, 2 : 1, 4 : 6, 2, 1 : 2, 0 : 1)"
        )

    def test_execute(self) -> None:
        """test program execution"""
        program1 = tuple(Instruction.parse_program(EXAMPLE_PROGRAM1))
        program2 = tuple(Instruction.parse_program(EXAMPLE_PROGRAM2))
        machine = Machine.default(iter([1, 42]))
        self.assertEqual(
            list(machine.execute_program(program1)),
            [None] * 35 + [2, None, None]
        )
        machine.reset()
        self.assertEqual(
            list(filter(lambda value: value is not None, machine.execute_program(program2))),
            [1, 1, 1, 1, 0, 1, 0]
        )
        self.assertIsNone(next(machine.input, None))

    def test_frames(self) -> None:
        """test frame detection"""
        machine = Machine(42, [1, 2], [4, 6, 2, 0, 3, 4, 42, 4, 99], 8, iter([]))
        self.assertEqual(
            list(machine.frames()),
            [
                [42, 4, 99],
                [2, 0, 3, 4],
                [4, 6]
            ]
        )
        machine = Machine(42, [1, 2], [2, 0, 3, 4, 42, 2, 99], 6, iter([]))
        self.assertEqual(
            list(machine.frames()),
            [
                [42, 2, 99],
                [2, 0, 3, 4]
            ]
        )
        self.assertEqual(
            list(Machine.default(iter([])).frames()),
            []
        )
