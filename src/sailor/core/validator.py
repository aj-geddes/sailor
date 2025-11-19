"""
Mermaid diagram validation with comprehensive error reporting.
"""
import re
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DiagramType(Enum):
    """Supported Mermaid diagram types."""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequenceDiagram"
    CLASS = "classDiagram"
    STATE = "stateDiagram"
    ER = "erDiagram"
    GANTT = "gantt"
    PIE = "pie"
    JOURNEY = "journey"
    GITGRAPH = "gitGraph"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"
    QUADRANT = "quadrantChart"
    REQUIREMENT = "requirementDiagram"
    C4CONTEXT = "C4Context"


@dataclass
class ValidationError:
    """Structured validation error."""
    line: Optional[int]
    column: Optional[int]
    message: str
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of diagram validation."""
    is_valid: bool
    diagram_type: Optional[DiagramType]
    errors: List[ValidationError]
    warnings: List[ValidationError]
    metadata: Dict[str, Any]


class MermaidValidator:
    """
    Comprehensive Mermaid diagram validator with detailed error reporting.
    """
    
    # Diagram type patterns
    DIAGRAM_PATTERNS = {
        DiagramType.FLOWCHART: re.compile(r'^\s*(graph|flowchart)\s+(TB|TD|BT|RL|LR)', re.MULTILINE),
        DiagramType.SEQUENCE: re.compile(r'^\s*sequenceDiagram', re.MULTILINE),
        DiagramType.CLASS: re.compile(r'^\s*classDiagram', re.MULTILINE),
        DiagramType.STATE: re.compile(r'^\s*stateDiagram(-v2)?', re.MULTILINE),
        DiagramType.ER: re.compile(r'^\s*erDiagram', re.MULTILINE),
        DiagramType.GANTT: re.compile(r'^\s*gantt', re.MULTILINE),
        DiagramType.PIE: re.compile(r'^\s*pie(\s+title)?', re.MULTILINE),
        DiagramType.JOURNEY: re.compile(r'^\s*journey', re.MULTILINE),
        DiagramType.GITGRAPH: re.compile(r'^\s*gitGraph', re.MULTILINE),
        DiagramType.MINDMAP: re.compile(r'^\s*mindmap', re.MULTILINE),
        DiagramType.TIMELINE: re.compile(r'^\s*timeline', re.MULTILINE),
        DiagramType.QUADRANT: re.compile(r'^\s*quadrantChart', re.MULTILINE),
        DiagramType.REQUIREMENT: re.compile(r'^\s*requirementDiagram', re.MULTILINE),
        DiagramType.C4CONTEXT: re.compile(r'^\s*C4Context', re.MULTILINE),
    }
    
    # Common syntax patterns for validation
    NODE_ID_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
    EDGE_PATTERNS = {
        'arrow': re.compile(r'-->|->|==>|=>|-.->|<-->|<->|<==>')
    }
    
    def __init__(self):
        """Initialize the validator."""
        self._init_validation_rules()
    
    def _init_validation_rules(self):
        """Initialize diagram-specific validation rules."""
        self.validation_rules = {
            DiagramType.FLOWCHART: self._validate_flowchart,
            DiagramType.SEQUENCE: self._validate_sequence,
            DiagramType.CLASS: self._validate_class,
            # Add more specific validators as needed
        }
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate Mermaid diagram code.
        
        Args:
            code: The Mermaid diagram code to validate
            
        Returns:
            ValidationResult with detailed error information
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                diagram_type=None,
                errors=[ValidationError(
                    line=None,
                    column=None,
                    message="Empty diagram code"
                )],
                warnings=[],
                metadata={}
            )
        
        # Detect diagram type
        diagram_type = self._detect_diagram_type(code)
        if not diagram_type:
            return ValidationResult(
                is_valid=False,
                diagram_type=None,
                errors=[ValidationError(
                    line=1,
                    column=1,
                    message="Unknown or invalid diagram type",
                    suggestion="Start with a valid diagram declaration like 'graph TD' or 'sequenceDiagram'"
                )],
                warnings=[],
                metadata={}
            )
        
        # Run generic validations
        errors, warnings = self._run_generic_validations(code)
        
        # Run diagram-specific validations
        if diagram_type in self.validation_rules:
            specific_errors, specific_warnings = self.validation_rules[diagram_type](code)
            errors.extend(specific_errors)
            warnings.extend(specific_warnings)
        
        # Extract metadata
        metadata = self._extract_metadata(code, diagram_type)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            diagram_type=diagram_type,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _detect_diagram_type(self, code: str) -> Optional[DiagramType]:
        """Detect the diagram type from code."""
        for diagram_type, pattern in self.DIAGRAM_PATTERNS.items():
            if pattern.search(code):
                return diagram_type
        return None
    
    def _run_generic_validations(self, code: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Run validations common to all diagram types."""
        errors = []
        warnings = []
        lines = code.split('\n')
        
        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            # Check for unclosed quotes
            if line.count('"') % 2 != 0:
                errors.append(ValidationError(
                    line=i,
                    column=line.rfind('"') + 1,
                    message="Unclosed quote",
                    suggestion="Add closing quote"
                ))
            
            # Check for unmatched brackets
            open_brackets = line.count('[') + line.count('{') + line.count('(')
            close_brackets = line.count(']') + line.count('}') + line.count(')')
            if open_brackets != close_brackets:
                errors.append(ValidationError(
                    line=i,
                    column=len(line),
                    message="Unmatched brackets",
                    suggestion="Check bracket pairing"
                ))
            
            # Warn about very long lines
            if len(line) > 120:
                warnings.append(ValidationError(
                    line=i,
                    column=120,
                    message="Line exceeds recommended length",
                    severity="warning",
                    suggestion="Consider breaking into multiple lines"
                ))
        
        return errors, warnings
    
    def _validate_flowchart(self, code: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate flowchart-specific syntax."""
        errors = []
        warnings = []
        
        # Extract nodes and edges
        nodes = set()
        lines = code.split('\n')
        
        for i, line in enumerate(lines[1:], 2):  # Skip diagram declaration
            # Simple node detection (this is a simplified version)
            if '-->' in line or '-.->' in line:
                parts = re.split(r'-->|-.->', line)
                if len(parts) >= 2:
                    source = parts[0].strip().split('[')[0].strip()
                    target = parts[1].strip().split('[')[0].strip()
                    
                    # Validate node IDs
                    for node_id in [source, target]:
                        if node_id and not self.NODE_ID_PATTERN.match(node_id):
                            errors.append(ValidationError(
                                line=i,
                                column=line.find(node_id) + 1,
                                message=f"Invalid node ID: '{node_id}'",
                                suggestion="Node IDs must start with a letter and contain only letters, numbers, and underscores"
                            ))
                    
                    nodes.update([source, target])
        
        # Warn about isolated nodes
        if len(nodes) == 1:
            warnings.append(ValidationError(
                line=None,
                column=None,
                message="Diagram contains only one node",
                severity="warning",
                suggestion="Add connections or more nodes"
            ))
        
        return errors, warnings
    
    def _validate_sequence(self, code: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate sequence diagram-specific syntax."""
        errors = []
        warnings = []
        
        # Check for participant declarations
        has_participants = 'participant' in code or 'actor' in code
        if not has_participants:
            warnings.append(ValidationError(
                line=None,
                column=None,
                message="No participants declared",
                severity="warning",
                suggestion="Consider declaring participants explicitly with 'participant' or 'actor'"
            ))
        
        return errors, warnings
    
    def _validate_class(self, code: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate class diagram-specific syntax."""
        errors = []
        warnings = []
        
        # Check for class definitions
        if 'class' not in code.lower():
            errors.append(ValidationError(
                line=None,
                column=None,
                message="No class definitions found",
                suggestion="Add class definitions using 'class ClassName'"
            ))
        
        return errors, warnings
    
    def _extract_metadata(self, code: str, diagram_type: DiagramType) -> Dict[str, Any]:
        """Extract metadata about the diagram."""
        lines = code.split('\n')
        
        metadata = {
            'type': diagram_type.value,
            'line_count': len(lines),
            'char_count': len(code),
            'has_title': 'title' in code.lower(),
            'has_style': 'style' in code or 'classDef' in code,
        }
        
        # Count nodes and edges for flowcharts
        if diagram_type == DiagramType.FLOWCHART:
            node_count = len(re.findall(r'\b\w+\[', code))
            edge_count = len(re.findall(r'-->|->|==>|-.->|<-->', code))
            metadata.update({
                'node_count': node_count,
                'edge_count': edge_count,
                'complexity': node_count + edge_count
            })
        
        return metadata
    
    def sanitize(self, code: str) -> str:
        """
        Sanitize Mermaid code to prevent injection attacks.
        
        Args:
            code: Raw Mermaid code
            
        Returns:
            Sanitized code safe for rendering
        """
        # Remove potential script injections
        code = re.sub(r'<script[^>]*>.*?</script>', '', code, flags=re.IGNORECASE | re.DOTALL)
        code = re.sub(r'javascript:', '', code, flags=re.IGNORECASE)
        code = re.sub(r'on\w+\s*=', '', code, flags=re.IGNORECASE)
        
        # Remove HTML tags except those allowed in Mermaid
        code = re.sub(r'<(?!br\s*/?>)[^>]+>', '', code)
        
        # Escape special characters in strings
        # This is a simplified version - real implementation would be more thorough
        
        return code.strip()
    
    def fix_common_errors(self, code: str) -> str:
        """
        Attempt to fix common syntax errors automatically.
        
        Args:
            code: Mermaid code with potential errors
            
        Returns:
            Fixed code (best effort)
        """
        # Fix missing diagram declaration
        if not any(pattern.search(code) for pattern in self.DIAGRAM_PATTERNS.values()):
            # Default to flowchart if no type specified
            code = f"graph TD\n{code}"
        
        # Fix unclosed quotes
        lines = code.split('\n')
        fixed_lines = []
        for line in lines:
            if line.count('"') % 2 != 0:
                line += '"'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)