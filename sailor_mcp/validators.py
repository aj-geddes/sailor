"""
Mermaid Validator Component
As specified in /docs/index.md Core Components architecture
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class ValidationError:
    """Validation error with location info."""
    line: Optional[int] = None
    column: Optional[int] = None
    message: str = ""
    severity: str = "error"
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of Mermaid validation."""
    is_valid: bool
    diagram_type: Optional[str] = None
    errors: List[ValidationError] = None
    warnings: List[ValidationError] = None
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


class MermaidValidator:
    """
    Mermaid diagram validator as documented in architecture.
    Validates syntax and provides detailed error reporting.
    """
    
    def __init__(self):
        self.diagram_patterns = {
            'flowchart': r'^\s*(graph|flowchart)\s+(TD|TB|BT|RL|LR)',
            'sequence': r'^\s*sequenceDiagram',
            'class': r'^\s*classDiagram',
            'state': r'^\s*stateDiagram(-v2)?',
            'er': r'^\s*erDiagram',
            'gantt': r'^\s*gantt',
            'pie': r'^\s*pie(\s+title\s+.+)?',
            'journey': r'^\s*journey',
            'gitgraph': r'^\s*gitGraph',
            'mindmap': r'^\s*mindmap'
        }
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate Mermaid diagram code.
        Follows architecture documented in /docs/index.md
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(message="Empty diagram code")]
            )
        
        lines = code.split('\n')
        errors = []
        warnings = []
        suggestions = []
        
        # Detect diagram type
        diagram_type = self._detect_diagram_type(code)
        
        if not diagram_type:
            errors.append(ValidationError(
                line=1,
                message="Could not detect diagram type",
                suggestion="Start with a valid diagram declaration (e.g., 'graph TD', 'sequenceDiagram')"
            ))
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
        
        # Basic syntax validation
        self._validate_basic_syntax(lines, errors, warnings, diagram_type)
        
        # Diagram-specific validation
        if diagram_type == 'flowchart':
            self._validate_flowchart(lines, errors, warnings)
        elif diagram_type == 'sequence':
            self._validate_sequence(lines, errors, warnings)
        elif diagram_type == 'class':
            self._validate_class(lines, errors, warnings)
        
        # Generate suggestions
        if not errors:
            suggestions = self._generate_suggestions(code, diagram_type)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            diagram_type=diagram_type,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={'total_lines': len(lines)}
        )
    
    def _detect_diagram_type(self, code: str) -> Optional[str]:
        """Detect the type of Mermaid diagram."""
        first_line = code.strip().split('\n')[0].strip()
        
        for diagram_type, pattern in self.diagram_patterns.items():
            if re.match(pattern, first_line, re.IGNORECASE):
                return diagram_type
        
        return None
    
    def _validate_basic_syntax(self, lines: List[str], errors: List[ValidationError], 
                             warnings: List[ValidationError], diagram_type: str):
        """Validate basic syntax common to all diagrams."""
        # For class and ER diagrams, braces span multiple lines, so check entire code
        if diagram_type in ['class', 'er']:
            full_code = '\n'.join(lines)
            if full_code.count('{') != full_code.count('}'):
                errors.append(ValidationError(
                    line=0,
                    message="Unmatched curly braces in diagram",
                    suggestion="Ensure all { have matching } in class/entity definitions"
                ))
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('%%'):
                continue
            
            # Check for unmatched brackets
            if line.count('[') != line.count(']'):
                errors.append(ValidationError(
                    line=i,
                    message="Unmatched square brackets",
                    suggestion="Ensure all [ have matching ]"
                ))
            
            if line.count('(') != line.count(')'):
                errors.append(ValidationError(
                    line=i,
                    message="Unmatched parentheses", 
                    suggestion="Ensure all ( have matching )"
                ))
            
            # Skip curly brace check for class and ER diagrams (handled above)
            if diagram_type not in ['class', 'er']:
                if line.count('{') != line.count('}'):
                    errors.append(ValidationError(
                        line=i,
                        message="Unmatched curly braces",
                        suggestion="Ensure all { have matching }"
                    ))
    
    def _validate_flowchart(self, lines: List[str], errors: List[ValidationError], 
                           warnings: List[ValidationError]):
        """Validate flowchart-specific syntax."""
        nodes = set()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('%%') or i == 1:  # Skip first line (declaration)
                continue
            
            # Extract node definitions and connections
            if '-->' in line or '---' in line:
                # Connection line
                parts = re.split(r'-->|---', line)
                for part in parts:
                    part = part.strip()
                    if part:
                        node_match = re.match(r'^([A-Za-z0-9_]+)', part)
                        if node_match:
                            nodes.add(node_match.group(1))
            else:
                # Node definition
                node_match = re.match(r'^([A-Za-z0-9_]+)', line)
                if node_match:
                    nodes.add(node_match.group(1))
        
        # Check for unreferenced nodes
        if len(nodes) < 2:
            warnings.append(ValidationError(
                message="Diagram has very few nodes",
                suggestion="Consider adding more nodes to make the diagram more informative"
            ))
    
    def _validate_sequence(self, lines: List[str], errors: List[ValidationError], 
                          warnings: List[ValidationError]):
        """Validate sequence diagram syntax."""
        participants = set()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('%%') or i == 1:
                continue
            
            # Extract participants
            if line.startswith('participant '):
                match = re.match(r'participant\s+(\w+)', line)
                if match:
                    participants.add(match.group(1))
            elif '->>' in line or '-->' in line:
                # Message line
                parts = re.split(r'->>|-->', line)
                if len(parts) >= 2:
                    sender = parts[0].strip()
                    if sender and not sender in participants:
                        participants.add(sender)
        
        if len(participants) < 2:
            warnings.append(ValidationError(
                message="Sequence diagram should have at least 2 participants",
                suggestion="Add more participants with 'participant Name' statements"
            ))
    
    def _validate_class(self, lines: List[str], errors: List[ValidationError], 
                       warnings: List[ValidationError]):
        """Validate class diagram syntax."""
        classes = set()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('%%') or i == 1:
                continue
            
            # Class definition
            if line.startswith('class '):
                match = re.match(r'class\s+(\w+)', line)
                if match:
                    classes.add(match.group(1))
    
    def _generate_suggestions(self, code: str, diagram_type: str) -> List[str]:
        """Generate helpful suggestions for improving the diagram."""
        suggestions = []
        
        if diagram_type == 'flowchart':
            if 'subgraph' not in code:
                suggestions.append("Consider using subgraphs to group related nodes")
            if len(code.split('\n')) < 5:
                suggestions.append("Add more nodes and connections to make the flowchart more detailed")
        
        elif diagram_type == 'sequence':
            if 'note' not in code:
                suggestions.append("Consider adding notes to explain complex interactions")
        
        return suggestions
    
    def auto_fix(self, code: str) -> ValidationResult:
        """
        Attempt to auto-fix common validation errors.
        Returns a new ValidationResult with fixed code if successful.
        """
        # This is a placeholder for auto-fix functionality
        # In practice, this would implement common fixes like:
        # - Adding missing quotes
        # - Fixing bracket mismatches
        # - Correcting common syntax errors
        
        result = self.validate(code)
        if result.is_valid:
            return result
        
        # For now, return original validation result
        return result