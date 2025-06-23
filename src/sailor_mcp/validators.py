"""Mermaid code validation module"""
from typing import Dict, Any, List
import re


class MermaidValidator:
    """Validates Mermaid diagram syntax and structure"""
    
    DIAGRAM_TYPES = {
        'graph': ['TD', 'TB', 'BT', 'LR', 'RL'],
        'flowchart': ['TD', 'TB', 'BT', 'LR', 'RL'],
        'sequenceDiagram': [],
        'classDiagram': [],
        'stateDiagram': [],
        'stateDiagram-v2': [],
        'erDiagram': [],
        'journey': [],
        'gantt': [],
        'pie': [],
        'quadrantChart': [],
        'requirementDiagram': [],
        'gitGraph': [],
        'mindmap': [],
        'timeline': [],
        'zenuml': [],
        'sankey-beta': [],
        'block-beta': [],
        'architecture-beta': []
    }
    
    @staticmethod
    def validate(code: str) -> Dict[str, Any]:
        """
        Validate Mermaid code syntax and structure
        
        Args:
            code: Mermaid diagram code to validate
            
        Returns:
            Dictionary with validation results including:
            - valid: Boolean indicating if code is valid
            - errors: List of error messages
            - warnings: List of warning messages
            - diagram_type: Detected diagram type
            - line_count: Number of lines in the code
        """
        errors = []
        warnings = []
        
        # Basic validation
        if not code or not code.strip():
            errors.append("Empty diagram code")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        lines = code.strip().split('\n')
        first_line = lines[0].strip()
        
        # Check diagram type
        valid_start = False
        diagram_type = "unknown"
        
        # Check for longer type names first to avoid false matches
        sorted_types = sorted(MermaidValidator.DIAGRAM_TYPES.items(), 
                            key=lambda x: len(x[0]), reverse=True)
        
        for dtype, directions in sorted_types:
            if first_line.startswith(dtype):
                valid_start = True
                diagram_type = dtype
                
                # Check direction for graph/flowchart
                if directions and dtype in ['graph', 'flowchart']:
                    has_valid_direction = any(
                        first_line.startswith(f"{dtype} {d}") for d in directions
                    )
                    if not has_valid_direction:
                        warnings.append(
                            f"Missing or invalid direction for {dtype}. "
                            f"Use one of: {', '.join(directions)}"
                        )
                break
        
        if not valid_start:
            errors.append(
                f"Invalid diagram type. First line should start with one of: "
                f"{', '.join(MermaidValidator.DIAGRAM_TYPES.keys())}"
            )
        
        # Check bracket matching
        brackets = [
            ('{', '}', 'brackets'),
            ('(', ')', 'parentheses'),
            ('[', ']', 'square brackets')
        ]
        
        for open_char, close_char, name in brackets:
            open_count = code.count(open_char)
            close_count = code.count(close_char)
            if open_count != close_count:
                errors.append(
                    f"Mismatched {name}: {open_count} opening, {close_count} closing"
                )
        
        # Check for unclosed strings
        quote_count = code.count('"')
        if quote_count % 2 != 0:
            errors.append("Unclosed string literal (odd number of quotes)")
        
        # Diagram-specific validation
        if diagram_type == 'graph' or diagram_type == 'flowchart':
            MermaidValidator._validate_flowchart(code, warnings)
        elif diagram_type == 'sequenceDiagram':
            MermaidValidator._validate_sequence(code, warnings)
        elif diagram_type == 'gantt':
            MermaidValidator._validate_gantt(code, warnings)
        elif diagram_type == 'classDiagram':
            MermaidValidator._validate_class(code, warnings)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "line_count": len(lines),
            "diagram_type": diagram_type
        }
    
    @staticmethod
    def _validate_flowchart(code: str, warnings: List[str]) -> None:
        """Validate flowchart-specific syntax"""
        # Check for empty nodes
        if '[]' in code or '{}' in code or '()' in code:
            warnings.append("Empty node labels detected")
        
        # Check for connections
        if '-->' not in code and '---' not in code and '-.->':
            warnings.append("No connections found in flowchart")
        
        # Check for node definitions
        node_pattern = r'([A-Za-z0-9_]+)[\[\{\(]'
        nodes = re.findall(node_pattern, code)
        if not nodes:
            warnings.append("No node definitions found")
    
    @staticmethod
    def _validate_sequence(code: str, warnings: List[str]) -> None:
        """Validate sequence diagram syntax"""
        if 'participant' not in code:
            warnings.append("No participants defined in sequence diagram")
        
        if '->>' not in code and '-->>' not in code and '-)' not in code:
            warnings.append("No messages found in sequence diagram")
    
    @staticmethod
    def _validate_gantt(code: str, warnings: List[str]) -> None:
        """Validate Gantt chart syntax"""
        if 'title' not in code:
            warnings.append("No title defined for Gantt chart")
        
        if 'section' not in code:
            warnings.append("No sections defined in Gantt chart")
        
        # Check for date format
        if 'dateFormat' not in code:
            warnings.append("No dateFormat specified for Gantt chart")
    
    @staticmethod
    def _validate_class(code: str, warnings: List[str]) -> None:
        """Validate class diagram syntax"""
        if 'class ' not in code:
            warnings.append("No class definitions found")
        
        # Check for relationships
        relationship_patterns = ['<|--', '--|>', '*--', '--*', 'o--', '--o']
        has_relationship = any(pattern in code for pattern in relationship_patterns)
        if not has_relationship:
            warnings.append("No class relationships defined")
    
    @staticmethod
    def fix_common_errors(code: str) -> str:
        """
        Attempt to fix common Mermaid code errors
        
        Args:
            code: Mermaid code with potential errors
            
        Returns:
            Fixed code
        """
        fixed_code = code
        
        # Fix missing direction for graph
        if fixed_code.startswith('graph') and not any(
            d in fixed_code.split('\n')[0] for d in ['TD', 'TB', 'BT', 'LR', 'RL']
        ):
            fixed_code = fixed_code.replace('graph', 'graph TD', 1)
        
        # Fix common typos
        replacements = {
            'sequencediagram': 'sequenceDiagram',
            'classdiagram': 'classDiagram',
            'statediagram': 'stateDiagram',
            'erdiagram': 'erDiagram',
        }
        
        for typo, correct in replacements.items():
            if fixed_code.lower().startswith(typo):
                fixed_code = fixed_code.replace(typo, correct, 1)
                fixed_code = fixed_code.replace(typo.capitalize(), correct, 1)
        
        return fixed_code