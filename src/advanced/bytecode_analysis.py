#!/usr/bin/env python3
"""
Apex Decompiler - Advanced Bytecode Analysis Module
Deep bytecode analysis and optimization detection
"""

import struct
import hashlib
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
# import numpy as np  # Optional dependency

class OptimizationLevel(Enum):
    """Bytecode optimization levels"""
    NONE = 0
    BASIC = 1
    AGGRESSIVE = 2
    OBFUSCATED = 3

@dataclass
class BasicBlock:
    """Basic block in control flow graph"""
    id: int
    start_pc: int
    end_pc: int
    instructions: List[Any]
    predecessors: Set[int] = field(default_factory=set)
    successors: Set[int] = field(default_factory=set)
    dominators: Set[int] = field(default_factory=set)
    
@dataclass
class LoopInfo:
    """Loop information"""
    header: int
    body: Set[int]
    exits: Set[int]
    loop_type: str  # 'for', 'while', 'repeat'
    nesting_level: int

@dataclass
class DataFlowInfo:
    """Data flow analysis information"""
    definitions: Dict[int, Set[int]]  # register -> set of definition points
    uses: Dict[int, Set[int]]         # register -> set of use points
    live_in: Set[int]                 # live variables at block entry
    live_out: Set[int]                # live variables at block exit

class AdvancedBytecodeAnalyzer:
    """Advanced bytecode analysis engine"""
    
    def __init__(self):
        self.basic_blocks = {}
        self.cfg_edges = defaultdict(list)
        self.dominance_tree = {}
        self.loops = []
        self.data_flow = {}
        self.optimization_level = OptimizationLevel.NONE
        
    def analyze_function(self, function) -> Dict[str, Any]:
        """Perform comprehensive bytecode analysis"""
        analysis_results = {}
        
        # Build control flow graph
        self._build_cfg(function)
        analysis_results['cfg'] = self.basic_blocks
        
        # Compute dominance information
        self._compute_dominance()
        analysis_results['dominance'] = self.dominance_tree
        
        # Detect loops
        self._detect_loops()
        analysis_results['loops'] = self.loops
        
        # Perform data flow analysis
        self._analyze_data_flow(function)
        analysis_results['data_flow'] = self.data_flow
        
        # Detect optimization level
        self._detect_optimization_level(function)
        analysis_results['optimization_level'] = self.optimization_level
        
        # Advanced pattern detection
        patterns = self._detect_advanced_patterns(function)
        analysis_results['patterns'] = patterns
        
        return analysis_results
    
    def _build_cfg(self, function):
        """Build control flow graph with basic blocks"""
        instructions = function.instructions
        
        # Find basic block boundaries
        leaders = set([0])  # First instruction is always a leader
        
        for i, instr in enumerate(instructions):
            # Jump targets are leaders
            if hasattr(instr, 'opcode'):
                if instr.opcode.name == 'JMP':
                    if hasattr(instr, 'd'):
                        target = i + instr.d + 1
                        if 0 <= target < len(instructions):
                            leaders.add(target)
                    # Instruction after jump is also a leader
                    if i + 1 < len(instructions):
                        leaders.add(i + 1)
                elif instr.opcode.name in ['CALL', 'RETURN']:
                    # Instruction after call/return is a leader
                    if i + 1 < len(instructions):
                        leaders.add(i + 1)
        
        # Create basic blocks
        leaders_list = sorted(leaders)
        block_id = 0
        
        for i in range(len(leaders_list)):
            start = leaders_list[i]
            end = leaders_list[i + 1] - 1 if i + 1 < len(leaders_list) else len(instructions) - 1
            
            block_instructions = instructions[start:end + 1]
            
            basic_block = BasicBlock(
                id=block_id,
                start_pc=start,
                end_pc=end,
                instructions=block_instructions
            )
            
            self.basic_blocks[block_id] = basic_block
            block_id += 1
        
        # Build edges between basic blocks
        self._build_cfg_edges(instructions)
    
    def _build_cfg_edges(self, instructions):
        """Build edges in the control flow graph"""
        for block_id, block in self.basic_blocks.items():
            last_instr = block.instructions[-1] if block.instructions else None
            
            if last_instr and hasattr(last_instr, 'opcode'):
                if 'JUMP' in last_instr.opcode.name:
                    # Find target block
                    if hasattr(last_instr, 'd'):
                        target_pc = block.end_pc + last_instr.d + 1
                        target_block_id = self._find_block_by_pc(target_pc)
                        
                        if target_block_id is not None:
                            block.successors.add(target_block_id)
                            self.basic_blocks[target_block_id].predecessors.add(block_id)
                            self.cfg_edges[block_id].append(target_block_id)
                    
                    # Conditional jumps also fall through
                    if 'IF' in last_instr.opcode.name:
                        next_block_id = self._find_block_by_pc(block.end_pc + 1)
                        if next_block_id is not None:
                            block.successors.add(next_block_id)
                            self.basic_blocks[next_block_id].predecessors.add(block_id)
                            self.cfg_edges[block_id].append(next_block_id)
                
                elif last_instr.opcode.name != 'RETURN':
                    # Regular fall-through
                    next_block_id = self._find_block_by_pc(block.end_pc + 1)
                    if next_block_id is not None:
                        block.successors.add(next_block_id)
                        self.basic_blocks[next_block_id].predecessors.add(block_id)
                        self.cfg_edges[block_id].append(next_block_id)
    
    def _find_block_by_pc(self, pc: int) -> Optional[int]:
        """Find basic block containing given PC"""
        for block_id, block in self.basic_blocks.items():
            if block.start_pc <= pc <= block.end_pc:
                return block_id
        return None
    
    def _compute_dominance(self):
        """Compute dominance relationships"""
        if not self.basic_blocks:
            return
        
        # Initialize dominance sets
        entry_block = 0
        all_blocks = set(self.basic_blocks.keys())
        
        # Entry block dominates only itself
        self.basic_blocks[entry_block].dominators = {entry_block}
        
        # All other blocks initially dominated by all blocks
        for block_id in self.basic_blocks:
            if block_id != entry_block:
                self.basic_blocks[block_id].dominators = all_blocks.copy()
        
        # Iterative algorithm
        changed = True
        while changed:
            changed = False
            
            for block_id in self.basic_blocks:
                if block_id == entry_block:
                    continue
                
                block = self.basic_blocks[block_id]
                
                # Intersection of dominators of all predecessors
                new_dominators = all_blocks.copy()
                for pred_id in block.predecessors:
                    new_dominators &= self.basic_blocks[pred_id].dominators
                
                # Add self
                new_dominators.add(block_id)
                
                if new_dominators != block.dominators:
                    block.dominators = new_dominators
                    changed = True
        
        # Build dominance tree
        for block_id, block in self.basic_blocks.items():
            immediate_dominator = None
            min_dominators = len(all_blocks) + 1
            
            for dom_id in block.dominators:
                if dom_id != block_id:
                    dom_block = self.basic_blocks[dom_id]
                    if len(dom_block.dominators) < min_dominators:
                        min_dominators = len(dom_block.dominators)
                        immediate_dominator = dom_id
            
            if immediate_dominator is not None:
                self.dominance_tree[block_id] = immediate_dominator
    
    def _detect_loops(self):
        """Detect natural loops using dominance information"""
        self.loops = []
        
        # Find back edges (edges to dominators)
        back_edges = []
        for block_id, block in self.basic_blocks.items():
            for succ_id in block.successors:
                if succ_id in block.dominators:
                    back_edges.append((block_id, succ_id))
        
        # For each back edge, find the natural loop
        for tail, head in back_edges:
            loop_body = self._find_natural_loop(tail, head)
            
            # Determine loop type
            loop_type = self._classify_loop_type(head, loop_body)
            
            # Calculate nesting level
            nesting_level = self._calculate_nesting_level(head)
            
            loop_info = LoopInfo(
                header=head,
                body=loop_body,
                exits=self._find_loop_exits(loop_body),
                loop_type=loop_type,
                nesting_level=nesting_level
            )
            
            self.loops.append(loop_info)
    
    def _find_natural_loop(self, tail: int, head: int) -> Set[int]:
        """Find natural loop body for a back edge"""
        loop_body = {head, tail}
        worklist = deque([tail])
        
        while worklist:
            current = worklist.popleft()
            
            for pred_id in self.basic_blocks[current].predecessors:
                if pred_id not in loop_body:
                    loop_body.add(pred_id)
                    worklist.append(pred_id)
        
        return loop_body
    
    def _classify_loop_type(self, header: int, body: Set[int]) -> str:
        """Classify the type of loop"""
        header_block = self.basic_blocks[header]
        
        # Check instructions in header for loop patterns
        for instr in header_block.instructions:
            if hasattr(instr, 'opcode'):
                if 'FORN' in instr.opcode.name:
                    return 'for_numeric'
                elif 'FORG' in instr.opcode.name:
                    return 'for_generic'
        
        # Default classification based on structure
        if len(header_block.predecessors) > 1:
            return 'while'
        else:
            return 'repeat'
    
    def _calculate_nesting_level(self, block_id: int) -> int:
        """Calculate loop nesting level"""
        nesting = 0
        
        for loop in self.loops:
            if block_id in loop.body and loop.header != block_id:
                nesting += 1
        
        return nesting
    
    def _find_loop_exits(self, loop_body: Set[int]) -> Set[int]:
        """Find exit points from a loop"""
        exits = set()
        
        for block_id in loop_body:
            block = self.basic_blocks[block_id]
            
            for succ_id in block.successors:
                if succ_id not in loop_body:
                    exits.add(block_id)
                    break
        
        return exits
    
    def _analyze_data_flow(self, function):
        """Perform data flow analysis"""
        for block_id, block in self.basic_blocks.items():
            data_flow_info = DataFlowInfo(
                definitions=defaultdict(set),
                uses=defaultdict(set),
                live_in=set(),
                live_out=set()
            )
            
            # Analyze each instruction for def/use
            for i, instr in enumerate(block.instructions):
                if hasattr(instr, 'opcode') and hasattr(instr, 'a'):
                    # Most instructions define register A
                    if instr.opcode.name not in ['JMP', 'RETURN']:
                        data_flow_info.definitions[instr.a].add(block.start_pc + i)
                    
                    # Check for register uses
                    if hasattr(instr, 'b') and instr.opcode.name != 'LOADK':
                        data_flow_info.uses[instr.b].add(block.start_pc + i)
                    
                    if hasattr(instr, 'c') and instr.opcode.name in ['GETTABLE', 'SETTABLE']:
                        data_flow_info.uses[instr.c].add(block.start_pc + i)
            
            self.data_flow[block_id] = data_flow_info
        
        # Compute live variable information
        self._compute_liveness()
    
    def _compute_liveness(self):
        """Compute live variable information"""
        changed = True
        
        while changed:
            changed = False
            
            for block_id in reversed(list(self.basic_blocks.keys())):
                data_flow = self.data_flow[block_id]
                old_live_in = data_flow.live_in.copy()
                
                # live_out = union of live_in of all successors
                data_flow.live_out = set()
                for succ_id in self.basic_blocks[block_id].successors:
                    data_flow.live_out.update(self.data_flow[succ_id].live_in)
                
                # live_in = use ∪ (live_out - def)
                all_defs = set()
                all_uses = set()
                
                for reg, def_points in data_flow.definitions.items():
                    if def_points:
                        all_defs.add(reg)
                
                for reg, use_points in data_flow.uses.items():
                    if use_points:
                        all_uses.add(reg)
                
                data_flow.live_in = all_uses.union(data_flow.live_out - all_defs)
                
                if data_flow.live_in != old_live_in:
                    changed = True
    
    def _detect_optimization_level(self, function):
        """Detect the optimization level of bytecode"""
        score = 0
        total_instructions = len(function.instructions)
        
        if total_instructions == 0:
            self.optimization_level = OptimizationLevel.NONE
            return
        
        # Count optimization indicators
        jump_instructions = 0
        constant_loads = 0
        dead_code_blocks = 0
        
        for instr in function.instructions:
            if hasattr(instr, 'opcode'):
                if instr.opcode.name == 'JMP':
                    jump_instructions += 1
                elif instr.opcode.name in ['LOADK', 'LOADN']:
                    constant_loads += 1
        
        # Check for dead code (unreachable blocks)
        reachable = set()
        self._mark_reachable(0, reachable)
        dead_code_blocks = len(self.basic_blocks) - len(reachable)
        
        # Calculate optimization score
        jump_ratio = jump_instructions / total_instructions
        constant_ratio = constant_loads / total_instructions
        dead_code_ratio = dead_code_blocks / len(self.basic_blocks) if self.basic_blocks else 0
        
        if jump_ratio > 0.3 or dead_code_ratio > 0.2:
            score += 2  # Likely obfuscated
        elif jump_ratio > 0.1:
            score += 1  # Some optimization
        
        if constant_ratio > 0.5:
            score += 1  # Heavy constant usage
        
        # Determine optimization level
        if score >= 3:
            self.optimization_level = OptimizationLevel.OBFUSCATED
        elif score >= 2:
            self.optimization_level = OptimizationLevel.AGGRESSIVE
        elif score >= 1:
            self.optimization_level = OptimizationLevel.BASIC
        else:
            self.optimization_level = OptimizationLevel.NONE
    
    def _mark_reachable(self, block_id: int, reachable: Set[int]):
        """Mark reachable basic blocks"""
        if block_id in reachable or block_id not in self.basic_blocks:
            return
        
        reachable.add(block_id)
        
        for succ_id in self.basic_blocks[block_id].successors:
            self._mark_reachable(succ_id, reachable)
    
    def _detect_advanced_patterns(self, function) -> Dict[str, Any]:
        """Detect advanced bytecode patterns"""
        patterns = {
            'anti_debugging': [],
            'vm_detection': [],
            'string_encryption': [],
            'control_flow_flattening': [],
            'opaque_predicates': []
        }
        
        # Detect anti-debugging patterns
        for instr in function.instructions:
            if hasattr(instr, 'opcode'):
                if instr.opcode.name == 'GETIMPORT':
                    # Check for debug library imports
                    if hasattr(instr, 'd') and instr.d < len(function.constants):
                        const = function.constants[instr.d]
                        if isinstance(const, str) and 'debug' in const.lower():
                            patterns['anti_debugging'].append({
                                'type': 'debug_import',
                                'constant': const,
                                'instruction_offset': instr.offset
                            })
        
        # Detect control flow flattening
        if len(self.basic_blocks) > 10:  # Threshold for complex control flow
            switch_blocks = 0
            for block in self.basic_blocks.values():
                if len(block.successors) > 3:
                    switch_blocks += 1
            
            if switch_blocks > len(self.basic_blocks) * 0.3:
                patterns['control_flow_flattening'].append({
                    'type': 'dispatcher_pattern',
                    'switch_blocks': switch_blocks,
                    'total_blocks': len(self.basic_blocks)
                })
        
        # Detect opaque predicates
        for block in self.basic_blocks.values():
            for instr in block.instructions:
                if hasattr(instr, 'opcode') and instr.opcode.name in ['EQ', 'LT', 'LE']:
                    # Check for constant comparisons (potential opaque predicates)
                    if hasattr(instr, 'b') and hasattr(instr, 'c'):
                        patterns['opaque_predicates'].append({
                            'type': 'conditional_jump',
                            'block_id': block.id,
                            'instruction': str(instr)
                        })
        
        return patterns
    
    def generate_analysis_report(self) -> str:
        """Generate comprehensive analysis report"""
        report_lines = []
        
        report_lines.append("=== Apex Decompiler - Advanced Bytecode Analysis Report ===")
        report_lines.append("")
        
        # Control Flow Graph Statistics
        report_lines.append("Control Flow Graph:")
        report_lines.append(f"  Basic Blocks: {len(self.basic_blocks)}")
        report_lines.append(f"  CFG Edges: {sum(len(edges) for edges in self.cfg_edges.values())}")
        
        # Loop Information
        report_lines.append("")
        report_lines.append("Loop Analysis:")
        report_lines.append(f"  Natural Loops: {len(self.loops)}")
        
        for i, loop in enumerate(self.loops):
            report_lines.append(f"    Loop {i + 1}:")
            report_lines.append(f"      Type: {loop.loop_type}")
            report_lines.append(f"      Header: Block {loop.header}")
            report_lines.append(f"      Body Size: {len(loop.body)} blocks")
            report_lines.append(f"      Nesting Level: {loop.nesting_level}")
            report_lines.append(f"      Exit Points: {len(loop.exits)}")
        
        # Optimization Level
        report_lines.append("")
        report_lines.append(f"Optimization Level: {self.optimization_level.name}")
        
        # Dominance Information
        report_lines.append("")
        report_lines.append("Dominance Tree:")
        for block_id, dominator in self.dominance_tree.items():
            report_lines.append(f"  Block {block_id} dominated by Block {dominator}")
        
        return "\n".join(report_lines)

def main():
    """Test the bytecode analyzer"""
    analyzer = AdvancedBytecodeAnalyzer()
    
    # Mock function for testing
    class MockInstruction:
        def __init__(self, opcode_name, a=0, b=0, c=0, d=0, offset=0):
            from core.decompiler_engine import OpCode
            self.opcode = OpCode[opcode_name] if hasattr(OpCode, opcode_name) else None
            self.a = a
            self.b = b
            self.c = c
            self.d = d
            self.offset = offset
    
    class MockFunction:
        def __init__(self):
            self.instructions = [
                MockInstruction('LOADK', 0, 0, 0, 0),
                MockInstruction('LOADK', 1, 0, 0, 1),
                MockInstruction('JUMPIF', 0, 1, 0, 2),
                MockInstruction('CALL', 0, 1, 1),
                MockInstruction('RETURN', 0, 1),
                MockInstruction('CALL', 1, 1, 1),
                MockInstruction('RETURN', 1, 1)
            ]
            self.constants = ["hello", "world"]
    
    mock_function = MockFunction()
    results = analyzer.analyze_function(mock_function)
    
    print("Analysis Results:")
    for key, value in results.items():
        print(f"{key}: {value}")
    
    print("\nDetailed Report:")
    print(analyzer.generate_analysis_report())

if __name__ == "__main__":
    main()