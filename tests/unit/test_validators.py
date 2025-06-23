"""Unit tests for Mermaid validators"""
import pytest
from src.sailor_mcp.validators import MermaidValidator


class TestMermaidValidator:
    """Test cases for MermaidValidator"""
    
    def test_empty_code_validation(self):
        """Test validation of empty code"""
        result = MermaidValidator.validate("")
        assert not result["valid"]
        assert "Empty diagram code" in result["errors"]
        
        result = MermaidValidator.validate("   \n  \n  ")
        assert not result["valid"]
        assert "Empty diagram code" in result["errors"]
    
    def test_valid_flowchart(self):
        """Test validation of valid flowchart"""
        code = """graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert len(result["errors"]) == 0
        assert result["diagram_type"] == "graph"
        assert result["line_count"] == 4
    
    def test_flowchart_missing_direction(self):
        """Test flowchart with missing direction"""
        code = """graph
    A[Start] --> B[End]"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]  # Still valid, just has warning
        assert any("Missing or invalid direction" in w for w in result["warnings"])
    
    def test_invalid_diagram_type(self):
        """Test invalid diagram type"""
        code = """invalid TD
    A --> B"""
        
        result = MermaidValidator.validate(code)
        assert not result["valid"]
        assert any("Invalid diagram type" in e for e in result["errors"])
    
    def test_mismatched_brackets(self):
        """Test mismatched brackets"""
        code = """graph TD
    A[Start --> B{Decision
    B --> C[End]"""
        
        result = MermaidValidator.validate(code)
        assert not result["valid"]
        assert any("Mismatched square brackets" in e for e in result["errors"])
        assert any("Mismatched brackets" in e for e in result["errors"])
    
    def test_unclosed_string(self):
        """Test unclosed string literal"""
        code = """graph TD
    A["Start] --> B[End]"""
        
        result = MermaidValidator.validate(code)
        assert not result["valid"]
        assert any("Unclosed string literal" in e for e in result["errors"])
    
    def test_valid_sequence_diagram(self):
        """Test valid sequence diagram"""
        code = """sequenceDiagram
    participant Alice
    participant Bob
    Alice->>Bob: Hello Bob!
    Bob-->>Alice: Hi Alice!"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert result["diagram_type"] == "sequenceDiagram"
        assert len(result["errors"]) == 0
    
    def test_sequence_diagram_warnings(self):
        """Test sequence diagram with warnings"""
        code = """sequenceDiagram
    Note: This is just a note"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert any("No participants defined" in w for w in result["warnings"])
        assert any("No messages found" in w for w in result["warnings"])
    
    def test_valid_gantt_chart(self):
        """Test valid Gantt chart"""
        code = """gantt
    title A Gantt Diagram
    dateFormat YYYY-MM-DD
    section Section
    A task :a1, 2024-01-01, 30d
    Another task :after a1, 20d"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert result["diagram_type"] == "gantt"
    
    def test_gantt_chart_warnings(self):
        """Test Gantt chart with warnings"""
        code = """gantt
    A task :a1, 2024-01-01, 30d"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert any("No title defined" in w for w in result["warnings"])
        assert any("No sections defined" in w for w in result["warnings"])
        assert any("No dateFormat specified" in w for w in result["warnings"])
    
    def test_valid_class_diagram(self):
        """Test valid class diagram"""
        code = """classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +bark()
    }
    Animal <|-- Dog"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert result["diagram_type"] == "classDiagram"
    
    def test_empty_node_warning(self):
        """Test empty node detection"""
        code = """graph TD
    A[] --> B{}
    B --> C()"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert any("Empty node labels" in w for w in result["warnings"])
    
    def test_fix_common_errors(self):
        """Test fixing common errors"""
        # Test missing direction
        code = "graph\n    A --> B"
        fixed = MermaidValidator.fix_common_errors(code)
        assert fixed.startswith("graph TD")
        
        # Test typo correction
        code = "sequencediagram\n    A->>B: Hello"
        fixed = MermaidValidator.fix_common_errors(code)
        assert fixed.startswith("sequenceDiagram")
        
        # Test capitalized typo
        code = "Classdiagram\n    class A"
        fixed = MermaidValidator.fix_common_errors(code)
        assert fixed.startswith("classDiagram")
    
    def test_all_diagram_types(self):
        """Test that all diagram types are recognized"""
        diagram_types = [
            ("graph TD\n    A --> B", "graph"),
            ("flowchart LR\n    A --> B", "flowchart"),
            ("sequenceDiagram\n    A->>B: Hi", "sequenceDiagram"),
            ("classDiagram\n    class A", "classDiagram"),
            ("stateDiagram\n    [*] --> State1", "stateDiagram"),
            ("stateDiagram-v2\n    [*] --> State1", "stateDiagram-v2"),
            ("erDiagram\n    CUSTOMER ||--o{ ORDER : places", "erDiagram"),
            ("journey\n    title My Journey", "journey"),
            ("gantt\n    title Gantt", "gantt"),
            ("pie\n    title Pie", "pie"),
            ("mindmap\n    root((Mind))", "mindmap"),
            ("timeline\n    title Timeline", "timeline"),
        ]
        
        for code, expected_type in diagram_types:
            result = MermaidValidator.validate(code)
            assert result["diagram_type"] == expected_type
    
    def test_complex_flowchart_validation(self):
        """Test validation of complex flowchart"""
        code = """graph TB
    A[Christmas] -->|Get money| B(Go shopping)
    B --> C{Let me think}
    C -->|One| D[Laptop]
    C -->|Two| E[iPhone]
    C -->|Three| F[fa:fa-car Car]
    
    subgraph Section
        D --> G[Gift wrap]
        E --> G
        F --> G
    end
    
    G --> H[Give to family]
    H --> I[Happy ending!]"""
        
        result = MermaidValidator.validate(code)
        assert result["valid"]
        assert len(result["errors"]) == 0
        # Count non-empty lines
        assert result["line_count"] == len(code.strip().split('\n'))