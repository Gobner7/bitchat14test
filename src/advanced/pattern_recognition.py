#!/usr/bin/env python3
"""
Apex Decompiler - Advanced Pattern Recognition Module
Superior pattern matching and signature detection system
"""

import re
import hashlib
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class Pattern:
    """Pattern definition for code recognition"""
    name: str
    signature: str
    confidence: float
    description: str
    category: str
    replacements: Dict[str, str]

@dataclass
class Match:
    """Pattern match result"""
    pattern: Pattern
    start_offset: int
    end_offset: int
    confidence: float
    context: Dict[str, Any]

class SignatureDatabase:
    """Advanced signature database for known code patterns"""
    
    def __init__(self):
        self.patterns = []
        self.load_builtin_patterns()
    
    def load_builtin_patterns(self):
        """Load built-in patterns for common obfuscation techniques"""
        
        # Anti-decompiler patterns
        self.patterns.extend([
            Pattern(
                name="konstant_v2_breaker",
                signature=r"local\s+\w+\s*=\s*{.*?}\s*local\s+\w+\s*=\s*function\(\s*\w+\s*\).*?end",
                confidence=0.95,
                description="Konstant v2.1 decompiler breaker pattern",
                category="anti_decompiler",
                replacements={"obfuscated_table": "cleaner_implementation"}
            ),
            
            Pattern(
                name="oracle_confusion",
                signature=r"(\w+)\[(\w+)\]\s*=\s*(\w+)\[(\w+)\]\s*\.\.\s*(\w+)\[(\w+)\]",
                confidence=0.85,
                description="Oracle decompiler confusion pattern",
                category="anti_decompiler", 
                replacements={}
            ),
            
            Pattern(
                name="medal_bypass",
                signature=r"local\s+\w+\s*=\s*loadstring\s*\(\s*[\"'].+?[\"']\s*\)",
                confidence=0.90,
                description="Medal decompiler bypass using loadstring",
                category="anti_decompiler",
                replacements={"loadstring": "-- deobfuscated loadstring call"}
            )
        ])
        
        # String obfuscation patterns
        self.patterns.extend([
            Pattern(
                name="base64_string",
                signature=r"[A-Za-z0-9+/]{20,}={0,2}",
                confidence=0.80,
                description="Base64 encoded string",
                category="string_obfuscation",
                replacements={}
            ),
            
            Pattern(
                name="hex_string",
                signature=r"[0-9a-fA-F]{16,}",
                confidence=0.75,
                description="Hexadecimal encoded string",
                category="string_obfuscation", 
                replacements={}
            ),
            
            Pattern(
                name="char_concatenation",
                signature=r"string\.char\s*\(\s*\d+\s*\)\s*\.\.\s*string\.char\s*\(\s*\d+\s*\)",
                confidence=0.90,
                description="Character concatenation obfuscation",
                category="string_obfuscation",
                replacements={}
            )
        ])
        
        # Control flow obfuscation
        self.patterns.extend([
            Pattern(
                name="opaque_predicate",
                signature=r"if\s+\d+\s*[<>=!]+\s*\d+\s+then.*?end",
                confidence=0.85,
                description="Opaque predicate control flow obfuscation",
                category="control_flow",
                replacements={}
            ),
            
            Pattern(
                name="dead_code_insertion",
                signature=r"local\s+\w+\s*=\s*\d+\s*\+\s*\d+\s*--.*?unused",
                confidence=0.70,
                description="Dead code insertion",
                category="control_flow",
                replacements={}
            )
        ])
        
        # Function obfuscation
        self.patterns.extend([
            Pattern(
                name="function_name_mangling",
                signature=r"local\s+[a-zA-Z_][a-zA-Z0-9_]{20,}\s*=\s*function",
                confidence=0.60,
                description="Mangled function names",
                category="function_obfuscation",
                replacements={}
            ),
            
            Pattern(
                name="indirect_call",
                signature=r"(\w+)\[(\w+)\]\s*\(\s*.*?\s*\)",
                confidence=0.70,
                description="Indirect function call",
                category="function_obfuscation",
                replacements={}
            )
        ])

class AdvancedPatternRecognition:
    """Advanced pattern recognition engine"""
    
    def __init__(self):
        self.signature_db = SignatureDatabase()
        self.match_cache = {}
        self.statistics = defaultdict(int)
        
    def analyze_code(self, source_code: str) -> List[Match]:
        """Analyze source code for known patterns"""
        matches = []
        
        # Create hash for caching
        code_hash = hashlib.md5(source_code.encode()).hexdigest()
        if code_hash in self.match_cache:
            return self.match_cache[code_hash]
        
        for pattern in self.signature_db.patterns:
            pattern_matches = self._find_pattern_matches(source_code, pattern)
            matches.extend(pattern_matches)
            self.statistics[pattern.category] += len(pattern_matches)
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Cache results
        self.match_cache[code_hash] = matches
        
        return matches
    
    def _find_pattern_matches(self, source_code: str, pattern: Pattern) -> List[Match]:
        """Find all matches for a specific pattern"""
        matches = []
        
        try:
            regex_matches = re.finditer(pattern.signature, source_code, re.MULTILINE | re.DOTALL)
            
            for regex_match in regex_matches:
                context = self._extract_context(source_code, regex_match.start(), regex_match.end())
                
                match = Match(
                    pattern=pattern,
                    start_offset=regex_match.start(),
                    end_offset=regex_match.end(),
                    confidence=pattern.confidence,
                    context=context
                )
                
                matches.append(match)
                
        except re.error as e:
            print(f"Regex error in pattern {pattern.name}: {e}")
        
        return matches
    
    def _extract_context(self, source_code: str, start: int, end: int) -> Dict[str, Any]:
        """Extract context around a match"""
        context_size = 100
        
        # Get surrounding context
        context_start = max(0, start - context_size)
        context_end = min(len(source_code), end + context_size)
        
        before = source_code[context_start:start]
        match_text = source_code[start:end]
        after = source_code[end:context_end]
        
        # Calculate line numbers
        lines_before = source_code[:start].count('\n')
        lines_in_match = match_text.count('\n')
        
        return {
            'before': before,
            'match': match_text,
            'after': after,
            'line_start': lines_before + 1,
            'line_end': lines_before + lines_in_match + 1,
            'length': end - start
        }
    
    def get_deobfuscation_suggestions(self, matches: List[Match]) -> Dict[str, List[str]]:
        """Generate deobfuscation suggestions based on matches"""
        suggestions = defaultdict(list)
        
        for match in matches:
            category = match.pattern.category
            
            if category == "anti_decompiler":
                suggestions["Anti-Decompiler Techniques"].append(
                    f"Detected {match.pattern.name} at line {match.context['line_start']}: {match.pattern.description}"
                )
            elif category == "string_obfuscation":
                suggestions["String Obfuscation"].append(
                    f"Found {match.pattern.name}: {match.context['match'][:50]}..."
                )
            elif category == "control_flow":
                suggestions["Control Flow Obfuscation"].append(
                    f"Control flow pattern {match.pattern.name} detected"
                )
            elif category == "function_obfuscation":
                suggestions["Function Obfuscation"].append(
                    f"Function obfuscation: {match.pattern.name}"
                )
        
        return dict(suggestions)
    
    def generate_clean_code(self, source_code: str, matches: List[Match]) -> str:
        """Generate cleaned code by applying pattern replacements"""
        cleaned_code = source_code
        
        # Sort matches by position (reverse order to maintain offsets)
        sorted_matches = sorted(matches, key=lambda x: x.start_offset, reverse=True)
        
        for match in sorted_matches:
            if match.pattern.replacements:
                # Apply pattern-specific replacements
                match_text = match.context['match']
                
                for old, new in match.pattern.replacements.items():
                    if old in match_text:
                        replacement = match_text.replace(old, new)
                        cleaned_code = (
                            cleaned_code[:match.start_offset] + 
                            replacement + 
                            cleaned_code[match.end_offset:]
                        )
                        break
            else:
                # Add comment about detected obfuscation
                comment = f"-- Detected {match.pattern.name}: {match.pattern.description}\n"
                cleaned_code = (
                    cleaned_code[:match.start_offset] + 
                    comment + 
                    cleaned_code[match.start_offset:]
                )
        
        return cleaned_code
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern recognition statistics"""
        total_matches = sum(self.statistics.values())
        
        stats = {
            'total_patterns_detected': total_matches,
            'by_category': dict(self.statistics),
            'cache_size': len(self.match_cache),
            'patterns_loaded': len(self.signature_db.patterns)
        }
        
        return stats

class SmartVariableNaming:
    """Intelligent variable naming system"""
    
    def __init__(self):
        self.naming_rules = self._load_naming_rules()
        self.context_hints = {}
        
    def _load_naming_rules(self) -> Dict[str, List[str]]:
        """Load intelligent naming rules"""
        return {
            'service_calls': ['game', 'workspace', 'players', 'lighting'],
            'gui_elements': ['frame', 'button', 'label', 'textbox'],
            'math_operations': ['result', 'sum', 'difference', 'product'],
            'loop_variables': ['i', 'j', 'k', 'index', 'count'],
            'table_operations': ['data', 'config', 'settings', 'info'],
            'string_operations': ['text', 'message', 'content', 'value']
        }
    
    def suggest_variable_name(self, context: str, usage_pattern: str) -> str:
        """Suggest meaningful variable names based on context"""
        context_lower = context.lower()
        
        # Check for service-related context
        for service in self.naming_rules['service_calls']:
            if service in context_lower:
                return f"{service}_ref"
        
        # Check for GUI context
        for gui_element in self.naming_rules['gui_elements']:
            if gui_element in context_lower:
                return f"gui_{gui_element}"
        
        # Check usage patterns
        if 'for' in usage_pattern or 'while' in usage_pattern:
            return 'loop_var'
        elif 'table' in usage_pattern:
            return 'table_data'
        elif 'string' in usage_pattern:
            return 'text_value'
        
        return 'variable'

def main():
    """Test the pattern recognition system"""
    recognizer = AdvancedPatternRecognition()
    
    # Test code with obfuscation
    test_code = '''
    local obfuscated_func = function(x)
        local result = string.char(72) .. string.char(101) .. string.char(108) .. string.char(108) .. string.char(111)
        if 1 < 2 then
            return result
        end
    end
    
    local base64_data = "SGVsbG8gV29ybGQ="
    local hex_data = "48656c6c6f20576f726c64"
    '''
    
    matches = recognizer.analyze_code(test_code)
    
    print("Pattern Recognition Results:")
    for match in matches:
        print(f"- {match.pattern.name} (confidence: {match.confidence})")
        print(f"  {match.pattern.description}")
        print(f"  Line {match.context['line_start']}")
        print()
    
    suggestions = recognizer.get_deobfuscation_suggestions(matches)
    print("Deobfuscation Suggestions:")
    for category, items in suggestions.items():
        print(f"{category}:")
        for item in items:
            print(f"  - {item}")
        print()
    
    stats = recognizer.get_statistics()
    print("Statistics:", stats)

if __name__ == "__main__":
    main()