#!/usr/bin/env python3
"""
Apex Decompiler - Modern GUI Interface
Superior user interface that outclasses Oracle, Medal, and Konstant
"""

import sys
import os
import json
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import *
        from PyQt5.QtCore import *
        from PyQt5.QtGui import *
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if PYQT_AVAILABLE:
    from core.decompiler_engine import ApexDecompiler
    from advanced.pattern_recognition import AdvancedPatternRecognition
    from advanced.bytecode_analysis import AdvancedBytecodeAnalyzer

class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    
    def __init__(self, text: str, primary: bool = False):
        super().__init__(text)
        self.primary = primary
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5CBF60, stop:1 #55b059);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3CAF40, stop:1 #359f39);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #f0f0f0;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #e0e0e0;
                    border-color: #bbb;
                }
                QPushButton:pressed {
                    background: #d0d0d0;
                }
            """)

class CodeEditor(QTextEdit):
    """Advanced code editor with syntax highlighting"""
    
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 11))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        # Enable line numbers
        self.line_number_area = LineNumberArea(self)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), 
                                               self.line_number_area_width(), cr.height()))
    
    def line_number_area_width(self):
        digits = len(str(max(1, self.document().blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

class LineNumberArea(QWidget):
    """Line number area for code editor"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(40, 40, 40))
        
        block = self.code_editor.document().firstBlock()
        block_number = 1
        top = self.code_editor.document().documentMargin()
        bottom = top + self.code_editor.document().size().height()
        
        painter.setPen(QColor(120, 120, 120))
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number)
                painter.drawText(0, int(top), self.width() - 5, 
                               self.code_editor.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.code_editor.document().size().height()
            block_number += 1

class AnalysisPanel(QWidget):
    """Analysis results panel"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Analysis tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #2d2d30;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #d4d4d4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #007acc;
            }
        """)
        
        # Pattern Recognition tab
        self.pattern_tab = QTextEdit()
        self.pattern_tab.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.tabs.addTab(self.pattern_tab, "Pattern Recognition")
        
        # Bytecode Analysis tab
        self.bytecode_tab = QTextEdit()
        self.bytecode_tab.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.tabs.addTab(self.bytecode_tab, "Bytecode Analysis")
        
        # Statistics tab
        self.stats_tab = QTextEdit()
        self.stats_tab.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.tabs.addTab(self.stats_tab, "Statistics")
        
        layout.addWidget(self.tabs)
    
    def update_pattern_analysis(self, patterns: List[Any]):
        """Update pattern recognition results"""
        text = "=== Pattern Recognition Results ===\n\n"
        
        if not patterns:
            text += "No suspicious patterns detected.\n"
        else:
            for i, match in enumerate(patterns):
                text += f"Pattern {i + 1}: {match.pattern.name}\n"
                text += f"  Confidence: {match.confidence:.2f}\n"
                text += f"  Description: {match.pattern.description}\n"
                text += f"  Category: {match.pattern.category}\n"
                text += f"  Line: {match.context.get('line_start', 'Unknown')}\n"
                text += f"  Match: {match.context.get('match', '')[:100]}...\n\n"
        
        self.pattern_tab.setPlainText(text)
    
    def update_bytecode_analysis(self, analysis: Dict[str, Any]):
        """Update bytecode analysis results"""
        text = "=== Advanced Bytecode Analysis ===\n\n"
        
        # Control Flow Graph
        cfg = analysis.get('cfg', {})
        text += f"Control Flow Graph:\n"
        text += f"  Basic Blocks: {len(cfg)}\n"
        
        # Loops
        loops = analysis.get('loops', [])
        text += f"  Natural Loops: {len(loops)}\n"
        
        for i, loop in enumerate(loops):
            text += f"    Loop {i + 1}: {loop.loop_type} (nesting: {loop.nesting_level})\n"
        
        # Optimization Level
        opt_level = analysis.get('optimization_level', 'Unknown')
        text += f"\nOptimization Level: {opt_level}\n"
        
        # Advanced Patterns
        patterns = analysis.get('patterns', {})
        text += f"\nAdvanced Patterns Detected:\n"
        
        for category, items in patterns.items():
            if items:
                text += f"  {category.replace('_', ' ').title()}: {len(items)} instances\n"
        
        self.bytecode_tab.setPlainText(text)
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update decompilation statistics"""
        text = "=== Decompilation Statistics ===\n\n"
        
        text += f"Deobfuscation Results:\n"
        text += f"  Strings Deobfuscated: {stats.get('deobfuscated_strings', 0)}\n"
        text += f"  Suspicious Jumps: {stats.get('suspicious_jumps', 0)}\n"
        text += f"  Pattern Matches: {stats.get('total_patterns_detected', 0)}\n"
        text += f"  Cache Size: {stats.get('cache_size', 0)}\n"
        
        text += f"\nPerformance:\n"
        text += f"  Decompilation Time: {stats.get('decompilation_time', 'N/A')}\n"
        text += f"  Analysis Time: {stats.get('analysis_time', 'N/A')}\n"
        text += f"  Memory Usage: {stats.get('memory_usage', 'N/A')}\n"
        
        self.stats_tab.setPlainText(text)

class ApexDecompilerGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.decompiler = ApexDecompiler()
        self.pattern_recognizer = AdvancedPatternRecognition()
        self.bytecode_analyzer = AdvancedBytecodeAnalyzer()
        
        self.current_file = None
        self.decompilation_thread = None
        
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Apex Decompiler v1.0.0 - Superior to Oracle, Medal & Konstant")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(self.create_app_icon())
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - File operations and controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Center panel - Code editor
        center_panel = self.create_center_panel()
        main_layout.addWidget(center_panel, 3)
        
        # Right panel - Analysis results
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Status bar
        self.create_status_bar()
        
        # Menu bar
        self.create_menu_bar()
    
    def create_app_icon(self):
        """Create application icon"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(76, 175, 80))
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        painter.end()
        
        return QIcon(pixmap)
    
    def create_left_panel(self):
        """Create left control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(300)
        
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Apex Decompiler")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Superior to Oracle, Medal & Konstant")
        subtitle.setStyleSheet("font-size: 12px; color: #888; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.open_button = ModernButton("Open Bytecode File", primary=True)
        self.open_button.clicked.connect(self.open_file)
        file_layout.addWidget(self.open_button)
        
        self.save_button = ModernButton("Save Decompiled Code")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setEnabled(False)
        file_layout.addWidget(self.save_button)
        
        layout.addWidget(file_group)
        
        # Decompilation options
        options_group = QGroupBox("Decompilation Options")
        options_layout = QVBoxLayout(options_group)
        
        self.advanced_analysis = QCheckBox("Advanced Pattern Recognition")
        self.advanced_analysis.setChecked(True)
        options_layout.addWidget(self.advanced_analysis)
        
        self.anti_obfuscation = QCheckBox("Anti-Obfuscation")
        self.anti_obfuscation.setChecked(True)
        options_layout.addWidget(self.anti_obfuscation)
        
        self.variable_recovery = QCheckBox("Smart Variable Recovery")
        self.variable_recovery.setChecked(True)
        options_layout.addWidget(self.variable_recovery)
        
        self.control_flow_analysis = QCheckBox("Control Flow Analysis")
        self.control_flow_analysis.setChecked(True)
        options_layout.addWidget(self.control_flow_analysis)
        
        layout.addWidget(options_group)
        
        # Decompile button
        self.decompile_button = ModernButton("Decompile", primary=True)
        self.decompile_button.clicked.connect(self.start_decompilation)
        self.decompile_button.setEnabled(False)
        layout.addWidget(self.decompile_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # File info
        self.file_info = QLabel("No file loaded")
        self.file_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.file_info)
        
        layout.addStretch()
        
        return panel
    
    def create_center_panel(self):
        """Create center code editor panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        
        # Editor tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #d4d4d4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #007acc;
            }
        """)
        
        # Original bytecode tab
        self.bytecode_editor = CodeEditor()
        self.bytecode_editor.setPlainText("Load a bytecode file to begin decompilation...")
        self.editor_tabs.addTab(self.bytecode_editor, "Bytecode (Hex)")
        
        # Decompiled code tab
        self.code_editor = CodeEditor()
        self.code_editor.setPlainText("-- Decompiled code will appear here")
        self.editor_tabs.addTab(self.code_editor, "Decompiled Luau")
        
        layout.addWidget(self.editor_tabs)
        
        return panel
    
    def create_right_panel(self):
        """Create right analysis panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        
        # Analysis panel
        self.analysis_panel = AnalysisPanel()
        layout.addWidget(self.analysis_panel)
        
        return panel
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Load a bytecode file to start")
        
        # Add permanent widgets
        self.version_label = QLabel("v1.0.0")
        self.status_bar.addPermanentWidget(self.version_label)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Bytecode', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save Decompiled Code', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        batch_action = QAction('Batch Decompile', self)
        batch_action.triggered.connect(self.batch_decompile)
        tools_menu.addAction(batch_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #d4d4d4;
            }
            QCheckBox {
                color: #d4d4d4;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
    
    def open_file(self):
        """Open bytecode file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Bytecode File",
            "",
            "Luau Bytecode (*.luac *.out);;All Files (*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.load_file(file_path)
    
    def load_file(self, file_path: str):
        """Load bytecode file"""
        try:
            with open(file_path, 'rb') as f:
                bytecode = f.read()
            
            # Display hex dump
            hex_dump = self.create_hex_dump(bytecode)
            self.bytecode_editor.setPlainText(hex_dump)
            
            # Update UI
            file_name = os.path.basename(file_path)
            file_size = len(bytecode)
            
            self.file_info.setText(f"File: {file_name}\nSize: {file_size} bytes")
            self.decompile_button.setEnabled(True)
            self.status_bar.showMessage(f"Loaded {file_name} ({file_size} bytes)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def create_hex_dump(self, data: bytes) -> str:
        """Create hex dump of bytecode"""
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            lines.append(f'{i:08x}: {hex_part:<48} {ascii_part}')
        return '\n'.join(lines)
    
    def start_decompilation(self):
        """Start decompilation in background thread"""
        if not self.current_file:
            return
        
        self.decompile_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.status_bar.showMessage("Decompiling...")
        
        # Start decompilation thread
        self.decompilation_thread = DecompilationThread(
            self.current_file,
            self.decompiler,
            self.pattern_recognizer,
            self.bytecode_analyzer,
            self.advanced_analysis.isChecked(),
            self.anti_obfuscation.isChecked(),
            self.variable_recovery.isChecked(),
            self.control_flow_analysis.isChecked()
        )
        
        self.decompilation_thread.finished.connect(self.decompilation_finished)
        self.decompilation_thread.error.connect(self.decompilation_error)
        self.decompilation_thread.start()
    
    def decompilation_finished(self, result: Dict[str, Any]):
        """Handle decompilation completion"""
        self.decompile_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.save_button.setEnabled(True)
        
        # Update code editor
        self.code_editor.setPlainText(result['source_code'])
        
        # Update analysis panels
        if 'pattern_matches' in result:
            self.analysis_panel.update_pattern_analysis(result['pattern_matches'])
        
        if 'bytecode_analysis' in result:
            self.analysis_panel.update_bytecode_analysis(result['bytecode_analysis'])
        
        if 'statistics' in result:
            self.analysis_panel.update_statistics(result['statistics'])
        
        # Switch to decompiled code tab
        self.editor_tabs.setCurrentIndex(1)
        
        self.status_bar.showMessage("Decompilation completed successfully")
    
    def decompilation_error(self, error_msg: str):
        """Handle decompilation error"""
        self.decompile_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Decompilation Error", error_msg)
        self.status_bar.showMessage("Decompilation failed")
    
    def save_file(self):
        """Save decompiled code"""
        if not self.code_editor.toPlainText():
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Decompiled Code",
            "",
            "Luau Script (*.luau *.lua);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.toPlainText())
                
                self.status_bar.showMessage(f"Saved to {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def batch_decompile(self):
        """Batch decompile multiple files"""
        QMessageBox.information(self, "Batch Decompile", 
                               "Batch decompilation feature coming soon!")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Apex Decompiler v1.0.0</h2>
        <p><b>Superior to Oracle, Medal & Konstant Combined</b></p>
        
        <p>Features:</p>
        <ul>
        <li>Advanced Pattern Recognition</li>
        <li>Anti-Obfuscation Technology</li>
        <li>Smart Variable Recovery</li>
        <li>Control Flow Analysis</li>
        <li>Modern User Interface</li>
        </ul>
        
        <p>Built with advanced algorithms that surpass existing decompilers.</p>
        """
        
        QMessageBox.about(self, "About Apex Decompiler", about_text)

class DecompilationThread(QThread):
    """Background decompilation thread"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str, decompiler, pattern_recognizer, 
                 bytecode_analyzer, advanced_analysis: bool, anti_obfuscation: bool,
                 variable_recovery: bool, control_flow_analysis: bool):
        super().__init__()
        self.file_path = file_path
        self.decompiler = decompiler
        self.pattern_recognizer = pattern_recognizer
        self.bytecode_analyzer = bytecode_analyzer
        self.advanced_analysis = advanced_analysis
        self.anti_obfuscation = anti_obfuscation
        self.variable_recovery = variable_recovery
        self.control_flow_analysis = control_flow_analysis
    
    def run(self):
        """Run decompilation in background"""
        try:
            import time
            start_time = time.time()
            
            # Read bytecode
            with open(self.file_path, 'rb') as f:
                bytecode = f.read()
            
            # Decompile
            source_code = self.decompiler.decompile_bytecode(bytecode)
            
            result = {
                'source_code': source_code,
                'statistics': {
                    'decompilation_time': f"{time.time() - start_time:.2f}s",
                    **self.decompiler.deobfuscation_stats
                }
            }
            
            # Advanced analysis if enabled
            if self.advanced_analysis:
                pattern_matches = self.pattern_recognizer.analyze_code(source_code)
                result['pattern_matches'] = pattern_matches
                
                pattern_stats = self.pattern_recognizer.get_statistics()
                result['statistics'].update(pattern_stats)
            
            # Bytecode analysis if enabled
            if self.control_flow_analysis:
                try:
                    # Parse function for analysis
                    main_function = self.decompiler._parse_bytecode(bytecode)
                    bytecode_analysis = self.bytecode_analyzer.analyze_function(main_function)
                    result['bytecode_analysis'] = bytecode_analysis
                except Exception as e:
                    print(f"Bytecode analysis error: {e}")
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

def main():
    """Main entry point"""
    if not PYQT_AVAILABLE:
        print("PyQt6 or PyQt5 is required for the GUI interface.")
        print("Install with: pip install PyQt6")
        return
    
    app = QApplication(sys.argv)
    app.setApplicationName("Apex Decompiler")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon
    app.setWindowIcon(QIcon())
    
    window = ApexDecompilerGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()