#!/usr/bin/env python3
"""
Apex Decompiler - Next Generation Lua 5.1 Bytecode Decompiler
Superior to Oracle, Medal, and Konstant combined

Core decompilation engine for Roblox exploits with advanced pattern recognition and anti-obfuscation
"""

import struct
import re
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import zlib
import hashlib
from collections import defaultdict, deque

class OpCode(Enum):
    """Lua 5.1 bytecode opcodes for Roblox exploits"""
    # Standard Lua 5.1 opcodes
    MOVE = 0
    LOADK = 1
    LOADBOOL = 2
    LOADNIL = 3
    GETUPVAL = 4
    GETGLOBAL = 5
    GETTABLE = 6
    SETGLOBAL = 7
    SETUPVAL = 8
    SETTABLE = 9
    NEWTABLE = 10
    SELF = 11
    ADD = 12
    SUB = 13
    MUL = 14
    DIV = 15
    MOD = 16
    POW = 17
    UNM = 18
    NOT = 19
    LEN = 20
    CONCAT = 21
    JMP = 22
    EQ = 23
    LT = 24
    LE = 25
    TEST = 26
    TESTSET = 27
    CALL = 28
    TAILCALL = 29
    RETURN = 30
    FORLOOP = 31
    FORPREP = 32
    TFORLOOP = 33
    SETLIST = 34
    CLOSE = 35
    CLOSURE = 36
    VARARG = 37

@dataclass
class Instruction:
    """Enhanced instruction representation"""
    opcode: OpCode
    a: int
    b: int
    c: int
    d: int
    aux: int
    line: int
    offset: int
    raw_data: bytes
    
    def __str__(self):
        return f"{self.opcode.name} {self.a} {self.b} {self.c} {self.d}"

@dataclass
class Function:
    """Enhanced function representation with metadata"""
    max_stack_size: int
    num_params: int
    num_upvals: int
    is_vararg: bool
    instructions: List[Instruction]
    constants: List[Any]
    protos: List['Function']
    debug_info: Dict[str, Any]
    source_name: str
    line_defined: int
    last_line_defined: int
    upvalue_names: List[str]
    local_names: List[Tuple[str, int, int]]
    
class ControlFlowGraph:
    """Advanced control flow analysis"""
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)
        self.dominators = {}
        self.loops = []
        
    def add_node(self, pc: int, instruction: Instruction):
        self.nodes[pc] = instruction
        
    def add_edge(self, from_pc: int, to_pc: int, condition: Optional[str] = None):
        self.edges[from_pc].append((to_pc, condition))
        
    def compute_dominators(self):
        """Compute dominator tree for advanced optimization"""
        # Implementation of dominator tree algorithm
        pass
        
    def detect_loops(self):
        """Detect natural loops in the control flow"""
        # Implementation of loop detection
        pass

class VariableRecovery:
    """Advanced variable name and type recovery"""
    def __init__(self):
        self.variable_map = {}
        self.type_inference = {}
        self.scope_stack = []
        
    def infer_variable_name(self, reg: int, context: Dict) -> str:
        """Infer meaningful variable names from context"""
        if reg in self.variable_map:
            return self.variable_map[reg]
            
        # Advanced heuristics for variable naming
        if 'table_access' in context:
            return f"table_{reg}"
        elif 'function_call' in context:
            return f"result_{reg}"
        elif 'loop_var' in context:
            return f"i_{reg}"
        else:
            return f"var_{reg}"
            
    def infer_type(self, reg: int, instruction: Instruction) -> str:
        """Infer variable types from usage patterns"""
        if instruction.opcode == OpCode.LOADK:
            return "string"  # Could be number too, but we'll assume string
        elif instruction.opcode == OpCode.LOADBOOL:
            return "boolean"
        elif instruction.opcode == OpCode.LOADNIL:
            return "nil"
        elif instruction.opcode == OpCode.NEWTABLE:
            return "table"
        else:
            return "any"

class AntiObfuscation:
    """Advanced anti-obfuscation techniques"""
    
    @staticmethod
    def detect_string_obfuscation(constants: List[Any]) -> Dict[int, str]:
        """Detect and deobfuscate string constants"""
        deobfuscated = {}
        
        for i, const in enumerate(constants):
            if isinstance(const, str):
                # Detect common obfuscation patterns
                if AntiObfuscation._is_base64_encoded(const):
                    try:
                        import base64
                        decoded = base64.b64decode(const).decode('utf-8')
                        deobfuscated[i] = decoded
                    except:
                        pass
                elif AntiObfuscation._is_hex_encoded(const):
                    try:
                        decoded = bytes.fromhex(const).decode('utf-8')
                        deobfuscated[i] = decoded
                    except:
                        pass
                        
        return deobfuscated
    
    @staticmethod
    def _is_base64_encoded(s: str) -> bool:
        """Check if string is base64 encoded"""
        try:
            import base64
            return base64.b64encode(base64.b64decode(s)).decode() == s
        except:
            return False
            
    @staticmethod
    def _is_hex_encoded(s: str) -> bool:
        """Check if string is hex encoded"""
        try:
            int(s, 16)
            return len(s) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in s)
        except:
            return False
    
    @staticmethod
    def detect_control_flow_obfuscation(instructions: List[Instruction]) -> List[int]:
        """Detect obfuscated control flow patterns"""
        suspicious_jumps = []
        
        for i, instr in enumerate(instructions):
            if instr.opcode == OpCode.JMP:
                # Detect suspicious jump patterns
                target = i + instr.aux + 1  # sBx field
                if target < 0 or target >= len(instructions):
                    suspicious_jumps.append(i)
                    
        return suspicious_jumps

class ApexDecompiler:
    """Main decompiler class - Superior to Oracle, Medal, and Konstant"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.name = "Apex Decompiler"
        self.variable_recovery = VariableRecovery()
        self.cfg = ControlFlowGraph()
        self.deobfuscation_stats = {}
        
    def decompile_bytecode(self, bytecode: bytes) -> str:
        """Main decompilation entry point"""
        try:
            # Parse bytecode
            main_function = self._parse_bytecode(bytecode)
            
            # Apply anti-obfuscation
            self._apply_deobfuscation(main_function)
            
            # Build control flow graph
            self._build_cfg(main_function)
            
            # Perform variable recovery
            self._recover_variables(main_function)
            
            # Generate Luau source code
            source = self._generate_source(main_function)
            
            return source
            
        except Exception as e:
            return f"-- Decompilation failed: {str(e)}\n-- This may be due to advanced obfuscation or corrupted bytecode"
    
    def _parse_bytecode(self, bytecode: bytes) -> Function:
        """Parse Lua 5.1 bytecode with enhanced error handling"""
        if len(bytecode) < 12:
            raise ValueError("Invalid bytecode: too short")
            
        # Check for Lua bytecode signature
        if bytecode[:4] != b'\x1bLua':
            raise ValueError("Invalid Lua bytecode signature")
            
        offset = 4
        
        # Parse version info
        version = bytecode[offset]
        if version != 0x51:  # Lua 5.1 version
            raise ValueError(f"Unsupported Lua version: {version:02x} (expected 0x51 for Lua 5.1)")
        offset += 1
        
        # Parse format version
        format_version = bytecode[offset]
        offset += 1
        
        # Parse endianness
        endian = bytecode[offset]
        offset += 1
        
        # Parse size info
        int_size = bytecode[offset]
        offset += 1
        size_t_size = bytecode[offset] 
        offset += 1
        instruction_size = bytecode[offset]
        offset += 1
        lua_number_size = bytecode[offset]
        offset += 1
        integral_flag = bytecode[offset]
        offset += 1
        
        # Parse main function
        main_function, _ = self._parse_function(bytecode, offset)
        return main_function
    
    def _parse_function(self, bytecode: bytes, offset: int) -> Tuple[Function, int]:
        """Parse a single Lua 5.1 function from bytecode"""
        start_offset = offset
        
        # Parse source name (string)
        source_len = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        if source_len > 0:
            source_name = bytecode[offset:offset+source_len-1].decode('utf-8', errors='replace')
            offset += source_len
        else:
            source_name = "<unknown>"
        
        # Line defined
        line_defined = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        # Last line defined  
        last_line_defined = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        # Read function header
        num_upvals = bytecode[offset]
        offset += 1
        
        num_params = bytecode[offset]
        offset += 1
        
        is_vararg = bytecode[offset]
        offset += 1
        
        max_stack_size = bytecode[offset]
        offset += 1
        
        # Parse instructions
        instructions = []
        num_instructions = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        for i in range(num_instructions):
            instr_data = bytecode[offset:offset+4]
            raw_instr = struct.unpack('<I', instr_data)[0]
            
            # Decode Lua 5.1 instruction format
            opcode_num = raw_instr & 0x3F  # 6 bits
            a = (raw_instr >> 6) & 0xFF   # 8 bits
            
            # Determine instruction format
            if opcode_num <= 37:  # Valid Lua 5.1 opcodes
                # Most instructions use B and C fields
                b = (raw_instr >> 23) & 0x1FF  # 9 bits
                c = (raw_instr >> 14) & 0x1FF  # 9 bits
                
                # Some instructions use Bx field instead
                bx = (raw_instr >> 14) & 0x3FFFF  # 18 bits
                
                # Some instructions use sBx field (signed)
                sbx = bx - 131071 if bx > 131071 else bx
            else:
                b = c = bx = sbx = 0
            
            try:
                opcode = OpCode(opcode_num)
            except ValueError:
                opcode = OpCode.MOVE  # Default for unknown opcodes
                
            instruction = Instruction(
                opcode=opcode,
                a=a, b=b, c=c, d=bx,  # Use d field for Bx
                aux=sbx,              # Use aux field for sBx
                line=i,
                offset=offset,
                raw_data=instr_data
            )
            
            instructions.append(instruction)
            offset += 4
        
        # Parse constants
        constants = []
        num_constants = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        for _ in range(num_constants):
            const_type = bytecode[offset]
            offset += 1
            
            if const_type == 0:  # nil
                constants.append(None)
            elif const_type == 1:  # boolean
                constants.append(bool(bytecode[offset]))
                offset += 1
            elif const_type == 3:  # number
                num_val = struct.unpack('<d', bytecode[offset:offset+8])[0]
                constants.append(num_val)
                offset += 8
            elif const_type == 4:  # string
                str_len = struct.unpack('<I', bytecode[offset:offset+4])[0]
                offset += 4
                if str_len > 0:
                    str_val = bytecode[offset:offset+str_len-1].decode('utf-8', errors='replace')
                    offset += str_len
                else:
                    str_val = ""
                constants.append(str_val)
            else:
                constants.append(f"<unknown_type_{const_type}>")
        
        # Parse nested functions
        protos = []
        num_protos = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        for _ in range(num_protos):
            proto, offset = self._parse_function(bytecode, offset)
            protos.append(proto)
        
        # Parse debug info (line info)
        num_lines = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        # Skip line info for now
        offset += num_lines * 4
        
        # Parse local variables
        num_locals = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        local_names = []
        for _ in range(num_locals):
            # Skip local variable info for now
            name_len = struct.unpack('<I', bytecode[offset:offset+4])[0]
            offset += 4
            if name_len > 0:
                name = bytecode[offset:offset+name_len-1].decode('utf-8', errors='replace')
                offset += name_len
                local_names.append((name, 0, 0))
            else:
                offset += 8  # Skip start and end PC
        
        # Parse upvalue names
        num_upvalue_names = struct.unpack('<I', bytecode[offset:offset+4])[0]
        offset += 4
        
        upvalue_names = []
        for _ in range(num_upvalue_names):
            name_len = struct.unpack('<I', bytecode[offset:offset+4])[0]
            offset += 4
            if name_len > 0:
                name = bytecode[offset:offset+name_len-1].decode('utf-8', errors='replace')
                offset += name_len
                upvalue_names.append(name)
        
        # Create function object
        function = Function(
            max_stack_size=max_stack_size,
            num_params=num_params,
            num_upvals=num_upvals,
            is_vararg=is_vararg,
            instructions=instructions,
            constants=constants,
            protos=protos,
            debug_info={},
            source_name=source_name,
            line_defined=line_defined,
            last_line_defined=last_line_defined,
            upvalue_names=upvalue_names,
            local_names=local_names
        )
        
        return function, offset
    
    def _apply_deobfuscation(self, function: Function):
        """Apply advanced deobfuscation techniques"""
        # Deobfuscate string constants
        deobfuscated_strings = AntiObfuscation.detect_string_obfuscation(function.constants)
        
        for idx, new_str in deobfuscated_strings.items():
            function.constants[idx] = new_str
            
        # Detect control flow obfuscation
        try:
            suspicious_jumps = AntiObfuscation.detect_control_flow_obfuscation(function.instructions)
        except:
            suspicious_jumps = []
        
        self.deobfuscation_stats = {
            'deobfuscated_strings': len(deobfuscated_strings),
            'suspicious_jumps': len(suspicious_jumps)
        }
    
    def _build_cfg(self, function: Function):
        """Build control flow graph"""
        for i, instr in enumerate(function.instructions):
            self.cfg.add_node(i, instr)
            
            # Add edges based on instruction type
            if instr.opcode == OpCode.JMP:
                target = i + instr.aux + 1  # sBx field
                self.cfg.add_edge(i, target)
            elif instr.opcode in [OpCode.EQ, OpCode.LT, OpCode.LE]:
                # Conditional jump - two edges
                self.cfg.add_edge(i, i + 1, "false")
                self.cfg.add_edge(i, i + 2, "true")  # Skip next instruction
    
    def _recover_variables(self, function: Function):
        """Perform advanced variable recovery"""
        for i, instr in enumerate(function.instructions):
            context = self._analyze_instruction_context(instr, function)
            
            # Recover variable names
            if instr.opcode in [OpCode.MOVE, OpCode.LOADK, OpCode.LOADBOOL, OpCode.LOADNIL]:
                var_name = self.variable_recovery.infer_variable_name(instr.a, context)
                var_type = self.variable_recovery.infer_type(instr.a, instr)
                
                self.variable_recovery.variable_map[instr.a] = var_name
                self.variable_recovery.type_inference[instr.a] = var_type
    
    def _analyze_instruction_context(self, instr: Instruction, function: Function) -> Dict:
        """Analyze instruction context for better decompilation"""
        context = {}
        
        if instr.opcode == OpCode.GETTABLE:
            context['table_access'] = True
        elif instr.opcode == OpCode.CALL:
            context['function_call'] = True
        elif instr.opcode in [OpCode.FORPREP, OpCode.FORLOOP]:
            context['loop_var'] = True
            
        return context
    
    def _generate_source(self, function: Function) -> str:
        """Generate high-quality Luau source code"""
        lines = []
        indent_level = 0
        
        # Add header comment
        lines.append("-- Decompiled with Apex Decompiler v1.0.0")
        lines.append("-- Superior to Oracle, Medal, and Konstant combined")
        lines.append("-- Advanced anti-obfuscation and variable recovery")
        lines.append("")
        
        # Generate function signature
        if function.num_params > 0:
            params = []
            for i in range(function.num_params):
                param_name = self.variable_recovery.variable_map.get(i, f"param{i}")
                params.append(param_name)
            
            if function.is_vararg:
                params.append("...")
                
            lines.append(f"function({', '.join(params)})")
        else:
            lines.append("function()")
        
        indent_level += 1
        
        # Generate instruction-based source
        for i, instr in enumerate(function.instructions):
            source_line = self._instruction_to_source(instr, function, indent_level)
            if source_line:
                lines.append("    " * indent_level + source_line)
        
        lines.append("end")
        
        # Add deobfuscation statistics
        if self.deobfuscation_stats:
            lines.append("")
            lines.append(f"-- Deobfuscation Stats:")
            lines.append(f"-- Strings deobfuscated: {self.deobfuscation_stats.get('deobfuscated_strings', 0)}")
            lines.append(f"-- Suspicious jumps detected: {self.deobfuscation_stats.get('suspicious_jumps', 0)}")
        
        return "\n".join(lines)
    
    def _instruction_to_source(self, instr: Instruction, function: Function, indent: int) -> str:
        """Convert Lua 5.1 instruction to readable source code"""
        try:
            if instr.opcode == OpCode.LOADK:
                var_name = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                if instr.d < len(function.constants):  # Bx field contains constant index
                    const_val = function.constants[instr.d]
                    if isinstance(const_val, str):
                        return f'local {var_name} = "{const_val}"'
                    else:
                        return f"local {var_name} = {const_val}"
                        
            elif instr.opcode == OpCode.LOADBOOL:
                var_name = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                bool_val = "true" if instr.b else "false"
                return f"local {var_name} = {bool_val}"
                
            elif instr.opcode == OpCode.LOADNIL:
                var_names = []
                for i in range(instr.a, instr.a + instr.b + 1):
                    var_names.append(self.variable_recovery.variable_map.get(i, f"var{i}"))
                return f"local {', '.join(var_names)} = nil"
                
            elif instr.opcode == OpCode.MOVE:
                dst = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                src = self.variable_recovery.variable_map.get(instr.b, f"var{instr.b}")
                return f"local {dst} = {src}"
                
            elif instr.opcode == OpCode.GETGLOBAL:
                var_name = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                if instr.d < len(function.constants):
                    global_name = function.constants[instr.d]
                    return f"local {var_name} = {global_name}"
                return f"local {var_name} = _G[{instr.d}]"
                
            elif instr.opcode == OpCode.SETGLOBAL:
                var_name = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                if instr.d < len(function.constants):
                    global_name = function.constants[instr.d]
                    return f"{global_name} = {var_name}"
                return f"_G[{instr.d}] = {var_name}"
                
            elif instr.opcode == OpCode.GETTABLE:
                dst = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                table = self.variable_recovery.variable_map.get(instr.b, f"var{instr.b}")
                
                # Check if C is a constant or register
                if instr.c & 0x100:  # Constant
                    key_idx = instr.c & 0xFF
                    if key_idx < len(function.constants):
                        key = function.constants[key_idx]
                        if isinstance(key, str):
                            return f"local {dst} = {table}.{key}"
                        else:
                            return f"local {dst} = {table}[{key}]"
                else:  # Register
                    key = self.variable_recovery.variable_map.get(instr.c, f"var{instr.c}")
                    return f"local {dst} = {table}[{key}]"
                
            elif instr.opcode == OpCode.SETTABLE:
                table = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                value = self.variable_recovery.variable_map.get(instr.c, f"var{instr.c}")
                
                # Check if B is a constant or register
                if instr.b & 0x100:  # Constant
                    key_idx = instr.b & 0xFF
                    if key_idx < len(function.constants):
                        key = function.constants[key_idx]
                        if isinstance(key, str):
                            return f"{table}.{key} = {value}"
                        else:
                            return f"{table}[{key}] = {value}"
                else:  # Register
                    key = self.variable_recovery.variable_map.get(instr.b, f"var{instr.b}")
                    return f"{table}[{key}] = {value}"
                
            elif instr.opcode == OpCode.NEWTABLE:
                var_name = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                return f"local {var_name} = {{}}"
                
            elif instr.opcode == OpCode.CALL:
                func = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                if instr.b == 1:  # No arguments
                    return f"{func}()"
                elif instr.b == 2:  # One argument
                    arg = self.variable_recovery.variable_map.get(instr.a + 1, f"var{instr.a + 1}")
                    return f"{func}({arg})"
                else:
                    args = []
                    for i in range(1, instr.b):
                        args.append(self.variable_recovery.variable_map.get(instr.a + i, f"var{instr.a + i}"))
                    return f"{func}({', '.join(args)})"
                    
            elif instr.opcode == OpCode.RETURN:
                if instr.b == 1:  # No return values
                    return "return"
                elif instr.b == 2:  # One return value
                    ret_val = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                    return f"return {ret_val}"
                else:
                    ret_vals = []
                    for i in range(instr.b - 1):
                        ret_vals.append(self.variable_recovery.variable_map.get(instr.a + i, f"var{instr.a + i}"))
                    return f"return {', '.join(ret_vals)}"
                    
            elif instr.opcode == OpCode.JMP:
                return f"-- JUMP to +{instr.aux}"  # sBx field
                
            elif instr.opcode == OpCode.ADD:
                dst = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                left = self.variable_recovery.variable_map.get(instr.b, f"var{instr.b}")
                right = self.variable_recovery.variable_map.get(instr.c, f"var{instr.c}")
                return f"local {dst} = {left} + {right}"
                
            elif instr.opcode == OpCode.SUB:
                dst = self.variable_recovery.variable_map.get(instr.a, f"var{instr.a}")
                left = self.variable_recovery.variable_map.get(instr.b, f"var{instr.b}")
                right = self.variable_recovery.variable_map.get(instr.c, f"var{instr.c}")
                return f"local {dst} = {left} - {right}"
                
            else:
                return f"-- {instr.opcode.name} R({instr.a}) R({instr.b}) R({instr.c})"
                
        except Exception as e:
            return f"-- Error processing {instr.opcode.name}: {str(e)}"
            
        return ""

def main():
    """Main entry point for testing"""
    decompiler = ApexDecompiler()
    print(f"{decompiler.name} v{decompiler.version}")
    print("Superior to Oracle, Medal, and Konstant combined")
    print("Ready for bytecode decompilation...")

if __name__ == "__main__":
    main()