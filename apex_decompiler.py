#!/usr/bin/env python3
"""
Apex Decompiler - Main Application Launcher
Superior to Oracle, Medal, and Konstant combined

Usage:
    python apex_decompiler.py gui          # Launch GUI interface
    python apex_decompiler.py cli [args]   # Use CLI interface
    python apex_decompiler.py [file]       # Quick decompile
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def main():
    """Main application entry point"""
    
    # Print banner
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                    APEX DECOMPILER v1.0.0                 ║
    ║              Superior to Oracle, Medal & Konstant         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python apex_decompiler.py gui          # Launch GUI interface")
        print("  python apex_decompiler.py cli [args]   # Use CLI interface")
        print("  python apex_decompiler.py [file]       # Quick decompile")
        print()
        print("Examples:")
        print("  python apex_decompiler.py gui")
        print("  python apex_decompiler.py script.luac")
        print("  python apex_decompiler.py cli decompile script.luac -v")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'gui':
        # Launch GUI interface
        try:
            from gui.main_window import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"GUI dependencies not available: {e}")
            print("Install with: pip install PyQt6")
            sys.exit(1)
    
    elif command == 'cli':
        # Launch CLI interface
        from cli.apex_cli import main as cli_main
        # Remove 'cli' from arguments
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        cli_main()
    
    elif command.endswith(('.luac', '.out')) or os.path.exists(command):
        # Quick decompile mode
        from core.decompiler_engine import ApexDecompiler
        
        input_file = command
        if not os.path.exists(input_file):
            print(f"Error: File not found: {input_file}")
            sys.exit(1)
        
        print(f"Quick decompiling: {input_file}")
        
        try:
            decompiler = ApexDecompiler()
            
            with open(input_file, 'rb') as f:
                bytecode = f.read()
            
            source_code = decompiler.decompile_bytecode(bytecode)
            
            # Save to output file
            output_file = os.path.splitext(input_file)[0] + '_decompiled.luau'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(source_code)
            
            print(f"✓ Decompilation completed!")
            print(f"✓ Output saved to: {output_file}")
            
            # Print basic stats
            deobf_stats = decompiler.deobfuscation_stats
            if deobf_stats:
                print(f"✓ Deobfuscated strings: {deobf_stats.get('deobfuscated_strings', 0)}")
                print(f"✓ Suspicious jumps detected: {deobf_stats.get('suspicious_jumps', 0)}")
            
        except Exception as e:
            print(f"Error: Decompilation failed: {str(e)}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'gui', 'cli', or provide a bytecode file")
        sys.exit(1)

if __name__ == "__main__":
    main()