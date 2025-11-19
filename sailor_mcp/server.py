"""
MCP Server for Sailor Mermaid Diagram Generation
Implements Model Context Protocol standards as documented in /docs/index.md
"""

import asyncio
from typing import Any, Dict, Optional, List
import os
import sys
import re

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import components as documented in architecture
from validators import MermaidValidator
from renderer import MermaidRenderer  
from prompts import DiagramPrompts
from mermaid_resources import MermaidResources

# Initialize components as shown in architecture diagram
validator = MermaidValidator()
renderer = MermaidRenderer()
prompts = DiagramPrompts()
resources = MermaidResources()

# Create FastMCP server instance following SDK standards
mcp = FastMCP(
    name="sailor-mermaid",
    version="1.0.0"
)

# Tool input schemas following MCP structured output standards
class GenerateDiagramInput(BaseModel):
    """Input schema for diagram generation tool."""
    description: str = Field(description="Natural language description of the diagram")
    diagram_type: Optional[str] = Field(default="flowchart", description="Type of diagram (flowchart, sequence, class, etc.)")
    theme: Optional[str] = Field(default="default", description="Theme (default, dark, forest, neutral)")
    style: Optional[str] = Field(default="classic", description="Style (classic, handDrawn)")

class ValidateInput(BaseModel):
    """Input schema for validation tool."""
    code: str = Field(description="Mermaid diagram code to validate")

class RenderInput(BaseModel):
    """Input schema for rendering tool."""
    code: str = Field(description="Mermaid diagram code to render")
    theme: Optional[str] = Field(default="default", description="Theme for rendering")
    format: Optional[str] = Field(default="png", description="Output format (png, svg, pdf)")
    transparent: Optional[bool] = Field(default=False, description="Transparent background")

# Output schemas following MCP structured output standards
class DiagramOutput(BaseModel):
    """Output schema for diagram generation."""
    code: str = Field(description="Generated Mermaid diagram code")
    diagram_type: str = Field(description="Detected or specified diagram type")
    valid: bool = Field(description="Whether the generated code is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors if any")

class ValidationOutput(BaseModel):
    """Output schema for validation."""
    valid: bool = Field(description="Whether the code is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    diagram_type: Optional[str] = Field(description="Detected diagram type")

class RenderOutput(BaseModel):
    """Output schema for rendering."""
    success: bool = Field(description="Whether rendering was successful")
    data: Optional[str] = Field(description="Base64 encoded image data")
    format: str = Field(description="Output format used")
    error: Optional[str] = Field(description="Error message if rendering failed")

# MCP Tools following documented architecture
@mcp.tool
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart", 
    theme: str = "default",
    style: str = "classic"
) -> DiagramOutput:
    """Generate Mermaid diagram from natural language description."""
    try:
        # Use prompts module to generate diagram
        result = await prompts.generate_diagram(
            description=description,
            diagram_type=diagram_type,
            theme=theme,
            style=style
        )
        
        if not result.success:
            return DiagramOutput(
                code="",
                diagram_type=diagram_type,
                valid=False,
                errors=[result.error or "Generation failed"]
            )
        
        # Validate generated code
        validation = validator.validate(result.code)
        
        return DiagramOutput(
            code=result.code,
            diagram_type=validation.diagram_type or diagram_type,
            valid=validation.is_valid,
            errors=[e.message for e in validation.errors] if validation.errors else []
        )
        
    except Exception as e:
        return DiagramOutput(
            code="",
            diagram_type=diagram_type,
            valid=False,
            errors=[str(e)]
        )

@mcp.tool
async def validate_and_render_mermaid(
    code: str,
    theme: str = "default",
    format: str = "png", 
    transparent: bool = False
) -> RenderOutput:
    """Validate and render Mermaid diagram code."""
    try:
        # First validate the code
        validation = validator.validate(code)
        
        if not validation.is_valid:
            return RenderOutput(
                success=False,
                data=None,
                format=format,
                error=f"Validation failed: {', '.join([e.message for e in validation.errors])}"
            )
        
        # Render the diagram
        result = await renderer.render(
            code=code,
            theme=theme,
            output_format=format,
            transparent_background=transparent
        )
        
        return RenderOutput(
            success=result.success,
            data=result.data,
            format=format,
            error=result.error
        )
        
    except Exception as e:
        return RenderOutput(
            success=False,
            data=None,
            format=format,
            error=str(e)
        )

@mcp.tool
async def get_mermaid_examples(diagram_type: Optional[str] = None) -> Dict[str, Any]:
    """Get example diagrams for learning and reference."""
    try:
        examples = resources.get_examples(diagram_type)
        return {
            "success": True,
            "examples": examples,
            "diagram_type": diagram_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "examples": []
        }

# Additional MCP Tools for enhanced LLM assistance
@mcp.tool
async def analyze_diagram(code: str) -> Dict[str, Any]:
    """Analyze a Mermaid diagram to extract structure, relationships, and meaning."""
    try:
        # Validate the diagram first
        validation = validator.validate(code)
        if not validation.is_valid:
            return {
                "success": False,
                "error": "Invalid diagram code",
                "validation_errors": [e.message for e in validation.errors]
            }
        
        # Analyze the diagram structure
        lines = code.strip().split('\n')
        diagram_type = validation.diagram_type
        
        analysis = {
            "diagram_type": diagram_type,
            "line_count": len(lines),
            "nodes": [],
            "relationships": [],
            "complexity": "low"  # Will be calculated
        }
        
        if diagram_type == "flowchart":
            # Extract nodes and relationships
            node_pattern = r'(\w+)\[(.*?)\]|\w+\((.*?)\)|\w+\{(.*?)\}'
            relationship_pattern = r'(\w+)\s*--.*?-->\s*(\w+)|(\w+)\s*-->\s*(\w+)'
            
            import re
            for line in lines[1:]:  # Skip diagram declaration
                # Find nodes
                for match in re.finditer(node_pattern, line):
                    node_id = match.group(0).split('[')[0].split('(')[0].split('{')[0]
                    if node_id and node_id not in ['graph', 'flowchart']:
                        analysis["nodes"].append(node_id)
                
                # Find relationships
                for match in re.finditer(relationship_pattern, line):
                    if match.group(1) and match.group(2):
                        analysis["relationships"].append({
                            "from": match.group(1),
                            "to": match.group(2),
                            "type": "directed"
                        })
                    elif match.group(3) and match.group(4):
                        analysis["relationships"].append({
                            "from": match.group(3),
                            "to": match.group(4),
                            "type": "directed"
                        })
        
        # Calculate complexity
        node_count = len(set(analysis["nodes"]))
        relationship_count = len(analysis["relationships"])
        
        if node_count > 10 or relationship_count > 15:
            analysis["complexity"] = "high"
        elif node_count > 5 or relationship_count > 7:
            analysis["complexity"] = "medium"
        
        analysis["summary"] = f"A {analysis['complexity']} complexity {diagram_type} diagram with {node_count} unique nodes and {relationship_count} relationships"
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def suggest_improvements(code: str, focus: Optional[str] = None) -> Dict[str, Any]:
    """Suggest improvements for a Mermaid diagram based on best practices."""
    try:
        validation = validator.validate(code)
        suggestions = []
        
        # General suggestions
        lines = code.strip().split('\n')
        
        # Check for descriptive node labels
        if any('[' in line and ']' in line for line in lines):
            unlabeled_nodes = []
            import re
            for line in lines:
                # Find nodes without labels (just IDs)
                if '-->' in line:
                    parts = line.split('-->')
                    for part in parts:
                        node = part.strip().split()[0]
                        if node.isalnum() and len(node) <= 3:
                            unlabeled_nodes.append(node)
            
            if unlabeled_nodes:
                suggestions.append({
                    "type": "clarity",
                    "message": f"Consider adding descriptive labels to nodes: {', '.join(set(unlabeled_nodes))}",
                    "example": f"{unlabeled_nodes[0]}[Descriptive Label]"
                })
        
        # Check for consistent arrow styles
        arrow_styles = set()
        for line in lines:
            if '-->' in line:
                arrow_styles.add('-->')
            if '--->' in line:
                arrow_styles.add('--->')
            if '-..->' in line:
                arrow_styles.add('-..->')
        
        if len(arrow_styles) > 1:
            suggestions.append({
                "type": "consistency",
                "message": "Use consistent arrow styles throughout the diagram",
                "found": list(arrow_styles)
            })
        
        # Diagram-specific suggestions
        if validation.diagram_type == "flowchart" and focus != "minimal":
            # Check for start/end nodes
            has_start = any('start' in line.lower() for line in lines)
            has_end = any('end' in line.lower() for line in lines)
            
            if not has_start:
                suggestions.append({
                    "type": "structure",
                    "message": "Consider adding a clear Start node",
                    "example": "Start[Start Process]"
                })
            
            if not has_end:
                suggestions.append({
                    "type": "structure", 
                    "message": "Consider adding a clear End node",
                    "example": "End[Process Complete]"
                })
        
        # Check for comments
        has_comments = any('%% ' in line for line in lines)
        if not has_comments and len(lines) > 10:
            suggestions.append({
                "type": "documentation",
                "message": "Consider adding comments to explain complex sections",
                "example": "%% This section handles user authentication"
            })
        
        return {
            "success": True,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def convert_diagram_style(code: str, target_style: str) -> Dict[str, Any]:
    """Convert a diagram between different Mermaid styles (e.g., flowchart to graph, different arrow styles)."""
    try:
        validation = validator.validate(code)
        if not validation.is_valid:
            return {
                "success": False,
                "error": "Invalid diagram code"
            }
        
        converted_code = code
        
        # Handle flowchart/graph conversion
        if target_style == "graph" and validation.diagram_type == "flowchart":
            converted_code = converted_code.replace("flowchart", "graph", 1)
        elif target_style == "flowchart" and "graph" in code.lower():
            converted_code = converted_code.replace("graph", "flowchart", 1)
        
        # Handle arrow style conversions
        if target_style == "dotted":
            converted_code = converted_code.replace("-->", "-.->")
            converted_code = converted_code.replace("---", "-.-")
        elif target_style == "thick":
            converted_code = converted_code.replace("-->", "==>")
            converted_code = converted_code.replace("---", "===")
        elif target_style == "normal":
            converted_code = converted_code.replace("-.->", "-->")
            converted_code = converted_code.replace("==>", "-->")
            converted_code = converted_code.replace("===", "---")
        
        return {
            "success": True,
            "original_code": code,
            "converted_code": converted_code,
            "target_style": target_style
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Phase 2 Enhanced Tools for Advanced Diagram Generation
@mcp.tool
async def generate_from_code(code: str, language: str = "python", diagram_type: str = "class") -> Dict[str, Any]:
    """Generate Mermaid diagrams from source code analysis."""
    try:
        import re
        
        if diagram_type == "class" and language == "python":
            # Parse Python code for class diagram
            class_pattern = r'class\s+(\w+)(?:\(([^)]+)\))?:'
            method_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            attribute_pattern = r'self\.(\w+)\s*='
            
            classes = {}
            current_class = None
            
            lines = code.split('\n')
            for i, line in enumerate(lines):
                # Find class definitions
                class_match = re.match(class_pattern, line)
                if class_match:
                    class_name = class_match.group(1)
                    parent = class_match.group(2)
                    current_class = class_name
                    classes[class_name] = {
                        'parent': parent.strip() if parent else None,
                        'methods': [],
                        'attributes': set()
                    }
                
                # Find methods
                if current_class and line.strip().startswith('def '):
                    method_match = re.match(r'\s*def\s+(\w+)\s*\([^)]*\):', line)
                    if method_match:
                        method_name = method_match.group(1)
                        visibility = '+' if not method_name.startswith('_') else '-'
                        classes[current_class]['methods'].append(f"{visibility}{method_name}()")
                
                # Find attributes
                if current_class and 'self.' in line:
                    attr_matches = re.findall(attribute_pattern, line)
                    for attr in attr_matches:
                        if not attr.startswith('_'):
                            classes[current_class]['attributes'].add(f"+{attr}")
                        else:
                            classes[current_class]['attributes'].add(f"-{attr}")
            
            # Generate Mermaid class diagram
            mermaid_code = "classDiagram\n"
            
            # Add class definitions
            for class_name, info in classes.items():
                mermaid_code += f"    class {class_name} {{\n"
                for attr in sorted(info['attributes']):
                    mermaid_code += f"        {attr}\n"
                for method in info['methods']:
                    mermaid_code += f"        {method}\n"
                mermaid_code += "    }\n"
                
                # Add inheritance relationships
                if info['parent']:
                    mermaid_code += f"    {info['parent']} <|-- {class_name}\n"
            
            return {
                "success": True,
                "code": mermaid_code,
                "diagram_type": "class",
                "language": language,
                "classes_found": len(classes)
            }
            
        elif diagram_type == "flowchart" and language in ["python", "javascript"]:
            # Generate flowchart from function logic
            function_pattern = r'(?:def|function)\s+(\w+)\s*\([^)]*\):'
            if_pattern = r'if\s+(.+):'
            for_pattern = r'for\s+.+\s+in\s+.+:'
            while_pattern = r'while\s+(.+):'
            
            mermaid_code = "flowchart TD\n"
            node_id = 1
            
            # Simple flow analysis
            lines = code.split('\n')
            indent_stack = []
            
            for line in lines:
                stripped = line.strip()
                
                if re.match(function_pattern, stripped):
                    func_name = re.match(function_pattern, stripped).group(1)
                    mermaid_code += f"    Start[Start {func_name}]\n"
                elif re.match(if_pattern, stripped):
                    condition = re.match(if_pattern, stripped).group(1)
                    mermaid_code += f"    Node{node_id}{{{{If {condition}?}}}}\n"
                    node_id += 1
                elif re.match(for_pattern, stripped) or re.match(while_pattern, stripped):
                    mermaid_code += f"    Node{node_id}[Loop]\n"
                    node_id += 1
            
            return {
                "success": True,
                "code": mermaid_code,
                "diagram_type": "flowchart",
                "language": language
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported combination: {language} to {diagram_type}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def generate_from_data(data: str, data_format: str = "json", diagram_type: str = "er") -> Dict[str, Any]:
    """Generate diagrams from structured data (JSON/CSV)."""
    try:
        import json
        import csv
        from io import StringIO
        
        if data_format == "json" and diagram_type == "er":
            # Parse JSON to create ER diagram
            parsed_data = json.loads(data)
            mermaid_code = "erDiagram\n"
            
            # Analyze JSON structure for entities and relationships
            entities = {}
            
            if isinstance(parsed_data, list) and parsed_data:
                # Analyze first item for structure
                sample = parsed_data[0]
                if isinstance(sample, dict):
                    entity_name = "Entity"
                    entities[entity_name] = []
                    
                    for key, value in sample.items():
                        if isinstance(value, (str, int, float, bool)):
                            attr_type = type(value).__name__
                            entities[entity_name].append(f"{key} {attr_type}")
                        elif isinstance(value, dict):
                            # Nested object suggests relationship
                            related_entity = key.capitalize()
                            mermaid_code += f"    {entity_name} ||--|| {related_entity} : has\n"
                        elif isinstance(value, list):
                            # List suggests one-to-many relationship
                            related_entity = key.capitalize()
                            mermaid_code += f"    {entity_name} ||--o{{ {related_entity} : has-many\n"
            
            elif isinstance(parsed_data, dict):
                # Each key could be an entity
                for entity_name, entity_data in parsed_data.items():
                    if isinstance(entity_data, list) and entity_data:
                        sample = entity_data[0] if isinstance(entity_data[0], dict) else None
                        if sample:
                            entities[entity_name] = []
                            for key, value in sample.items():
                                attr_type = type(value).__name__
                                entities[entity_name].append(f"{key} {attr_type}")
            
            # Add entity definitions
            for entity_name, attributes in entities.items():
                mermaid_code += f"    {entity_name} {{\n"
                for attr in attributes[:10]:  # Limit to 10 attributes for readability
                    mermaid_code += f"        {attr}\n"
                mermaid_code += "    }\n"
            
            return {
                "success": True,
                "code": mermaid_code,
                "diagram_type": "er",
                "entities_found": len(entities)
            }
            
        elif data_format == "csv" and diagram_type == "flowchart":
            # Parse CSV to create process flow
            csv_reader = csv.DictReader(StringIO(data))
            rows = list(csv_reader)
            
            if not rows:
                return {"success": False, "error": "No data in CSV"}
            
            mermaid_code = "flowchart TD\n"
            
            # Look for columns that suggest flow (from/to, source/target, etc.)
            headers = rows[0].keys()
            from_col = next((h for h in headers if h.lower() in ['from', 'source', 'start']), None)
            to_col = next((h for h in headers if h.lower() in ['to', 'target', 'end']), None)
            
            if from_col and to_col:
                for row in rows:
                    from_node = row[from_col].replace(' ', '_')
                    to_node = row[to_col].replace(' ', '_')
                    mermaid_code += f"    {from_node} --> {to_node}\n"
            else:
                # Create sequential flow from rows
                for i, row in enumerate(rows):
                    node_label = next(iter(row.values()))
                    mermaid_code += f"    Node{i}[{node_label}]\n"
                    if i > 0:
                        mermaid_code += f"    Node{i-1} --> Node{i}\n"
            
            return {
                "success": True,
                "code": mermaid_code,
                "diagram_type": "flowchart",
                "rows_processed": len(rows)
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported format combination: {data_format} to {diagram_type}"
            }
            
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def modify_diagram(code: str, modifications: List[Dict[str, str]]) -> Dict[str, Any]:
    """Apply specific modifications to an existing diagram."""
    try:
        modified_code = code
        applied_modifications = []
        
        for mod in modifications:
            action = mod.get('action', '')
            target = mod.get('target', '')
            value = mod.get('value', '')
            
            if action == 'add_node':
                # Add a new node to the diagram
                diagram_type = modified_code.split('\n')[0].strip()
                if 'flowchart' in diagram_type or 'graph' in diagram_type:
                    modified_code += f"\n    {target}[{value}]"
                    applied_modifications.append(f"Added node: {target}")
                    
            elif action == 'add_relationship':
                # Add a relationship between nodes
                from_node = target.split('->')[0].strip()
                to_node = target.split('->')[1].strip() if '->' in target else value
                modified_code += f"\n    {from_node} --> {to_node}"
                applied_modifications.append(f"Added relationship: {from_node} -> {to_node}")
                
            elif action == 'modify_label':
                # Change node label
                old_label = target
                new_label = value
                # Simple replacement - could be more sophisticated
                modified_code = modified_code.replace(f"[{old_label}]", f"[{new_label}]")
                applied_modifications.append(f"Changed label: {old_label} -> {new_label}")
                
            elif action == 'add_subgraph':
                # Add a subgraph
                modified_code += f"\n    subgraph {target}\n        {value}\n    end"
                applied_modifications.append(f"Added subgraph: {target}")
                
            elif action == 'change_style':
                # Change arrow or node style
                if 'arrow' in target:
                    modified_code = modified_code.replace('-->', value)
                    applied_modifications.append(f"Changed arrow style to: {value}")
        
        # Validate the modified diagram
        validation = validator.validate(modified_code)
        
        return {
            "success": validation.is_valid,
            "code": modified_code,
            "modifications_applied": applied_modifications,
            "validation_errors": [e.message for e in validation.errors] if validation.errors else []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def merge_diagrams(diagram1: str, diagram2: str, merge_strategy: str = "combine") -> Dict[str, Any]:
    """Merge two diagrams intelligently."""
    try:
        # Extract diagram types
        lines1 = diagram1.strip().split('\n')
        lines2 = diagram2.strip().split('\n')
        
        type1 = lines1[0].strip()
        type2 = lines2[0].strip()
        
        # Check if diagram types are compatible
        if type1.split()[0] != type2.split()[0]:
            return {
                "success": False,
                "error": f"Cannot merge different diagram types: {type1} and {type2}"
            }
        
        if merge_strategy == "combine":
            # Simple combination - merge all content
            merged_code = lines1[0] + '\n'
            
            # Add content from first diagram (skip header)
            merged_code += '\n'.join(lines1[1:])
            
            # Add content from second diagram (skip header)
            merged_code += '\n' + '\n'.join(lines2[1:])
            
        elif merge_strategy == "deduplicate":
            # Remove duplicate nodes and relationships
            merged_code = lines1[0] + '\n'
            
            seen_lines = set()
            
            # Process both diagrams
            for line in lines1[1:] + lines2[1:]:
                normalized = line.strip()
                if normalized and normalized not in seen_lines:
                    merged_code += line + '\n'
                    seen_lines.add(normalized)
        
        elif merge_strategy == "overlay":
            # Keep structure from first, add unique elements from second
            merged_code = diagram1
            
            # Extract unique elements from diagram2
            for line in lines2[1:]:
                if line.strip() and line.strip() not in diagram1:
                    merged_code += '\n' + line
        
        else:
            return {
                "success": False,
                "error": f"Unknown merge strategy: {merge_strategy}"
            }
        
        # Validate merged diagram
        validation = validator.validate(merged_code)
        
        return {
            "success": validation.is_valid,
            "code": merged_code,
            "merge_strategy": merge_strategy,
            "validation_errors": [e.message for e in validation.errors] if validation.errors else []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def extract_subgraph(code: str, target: str, include_connections: bool = True) -> Dict[str, Any]:
    """Extract a portion of a larger diagram."""
    try:
        lines = code.strip().split('\n')
        diagram_type = lines[0].strip()
        
        extracted_lines = [diagram_type]
        target_nodes = set()
        
        # Find target subgraph or nodes
        in_target_subgraph = False
        subgraph_level = 0
        
        for line in lines[1:]:
            stripped = line.strip()
            
            # Check for subgraph
            if f"subgraph {target}" in line:
                in_target_subgraph = True
                subgraph_level = 1
                extracted_lines.append(line)
            elif in_target_subgraph:
                if "subgraph" in stripped:
                    subgraph_level += 1
                elif "end" in stripped:
                    subgraph_level -= 1
                    extracted_lines.append(line)
                    if subgraph_level == 0:
                        in_target_subgraph = False
                else:
                    extracted_lines.append(line)
                    # Extract node names
                    if '-->' in stripped or '---' in stripped:
                        parts = re.split(r'-->|---', stripped)
                        for part in parts:
                            node = part.strip().split('[')[0].strip()
                            if node:
                                target_nodes.add(node)
            
            # Look for specific node references
            elif target in stripped:
                extracted_lines.append(line)
                if '-->' in stripped or '---' in stripped:
                    parts = re.split(r'-->|---', stripped)
                    for part in parts:
                        node = part.strip().split('[')[0].strip()
                        if node:
                            target_nodes.add(node)
        
        # If include_connections, find all connections to/from target nodes
        if include_connections and target_nodes:
            for line in lines[1:]:
                for node in target_nodes:
                    if node in line and line not in extracted_lines:
                        extracted_lines.append(line)
        
        extracted_code = '\n'.join(extracted_lines)
        
        return {
            "success": True,
            "code": extracted_code,
            "nodes_extracted": len(target_nodes),
            "lines_extracted": len(extracted_lines) - 1  # Excluding header
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
async def optimize_layout(code: str, optimization_goal: str = "clarity") -> Dict[str, Any]:
    """Optimize diagram layout for better readability."""
    try:
        lines = code.strip().split('\n')
        diagram_type = lines[0].strip()
        
        optimized_lines = [diagram_type]
        
        if optimization_goal == "clarity":
            # Group related nodes, improve spacing
            nodes = {}
            relationships = []
            subgraphs = {}
            current_subgraph = None
            
            for line in lines[1:]:
                stripped = line.strip()
                
                if 'subgraph' in stripped and not 'end' in stripped:
                    current_subgraph = stripped
                    subgraphs[current_subgraph] = []
                elif 'end' in stripped and current_subgraph:
                    current_subgraph = None
                elif '-->' in stripped or '---' in stripped:
                    relationships.append(line)
                    # Extract nodes from relationships
                    parts = re.split(r'-->|---', stripped)
                    for part in parts:
                        node_match = re.match(r'(\w+)(\[.*?\])?', part.strip())
                        if node_match:
                            node_id = node_match.group(1)
                            node_label = node_match.group(2) or ''
                            if current_subgraph:
                                subgraphs[current_subgraph].append((node_id, node_label))
                            else:
                                nodes[node_id] = node_label
                elif '[' in stripped and ']' in stripped:
                    # Standalone node definition
                    node_match = re.match(r'(\w+)(\[.*?\])', stripped)
                    if node_match:
                        node_id = node_match.group(1)
                        node_label = node_match.group(2)
                        if current_subgraph:
                            subgraphs[current_subgraph].append((node_id, node_label))
                        else:
                            nodes[node_id] = node_label
            
            # Rebuild with better organization
            # First, add standalone nodes
            for node_id, label in nodes.items():
                optimized_lines.append(f"    {node_id}{label}")
            
            # Add subgraphs
            for subgraph, sg_nodes in subgraphs.items():
                optimized_lines.append(f"    {subgraph}")
                for node_id, label in sg_nodes:
                    optimized_lines.append(f"        {node_id}{label}")
                optimized_lines.append("    end")
            
            # Add relationships at the end
            optimized_lines.append("")  # Empty line for clarity
            optimized_lines.extend(relationships)
            
        elif optimization_goal == "compact":
            # Remove extra whitespace, combine similar relationships
            for line in lines[1:]:
                stripped = line.strip()
                if stripped:  # Skip empty lines
                    optimized_lines.append(f"    {stripped}")
        
        elif optimization_goal == "hierarchical":
            # Attempt to arrange in hierarchical levels
            # This is a simplified version - real implementation would analyze dependencies
            optimized_lines.extend(lines[1:])
            
        optimized_code = '\n'.join(optimized_lines)
        
        return {
            "success": True,
            "code": optimized_code,
            "optimization_goal": optimization_goal,
            "original_lines": len(lines),
            "optimized_lines": len(optimized_lines)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# MCP Resources following documented architecture
@mcp.resource("diagram://list")
async def list_diagrams() -> str:
    """List available diagram types and examples."""
    return resources.list_diagram_types()

@mcp.resource("template://{diagram_type}")
async def get_template(diagram_type: str) -> str:
    """Get template for specific diagram type."""
    return resources.get_template(diagram_type)

# New enhanced resources
@mcp.resource("syntax://mermaid/{diagram_type}")
async def get_syntax_reference(diagram_type: str) -> str:
    """Get complete syntax reference for a diagram type."""
    syntax_guides = {
        "flowchart": """# Flowchart Syntax Reference

## Basic Nodes
- Simple: A
- With text: A[Text]
- Round edges: A(Text)
- Stadium shape: A([Text])
- Subroutine: A[[Text]]
- Cylindrical: A[(Database)]
- Circle: A((Text))
- Diamond: A{Text}
- Hexagon: A{{Text}}

## Arrows
- Basic: A --> B
- With text: A -->|text| B
- Dotted: A -.-> B
- Thick: A ==> B
- Multidirectional: A <--> B

## Subgraphs
subgraph title
    A --> B
end""",
        "sequence": """# Sequence Diagram Syntax Reference

## Participants
- participant A
- actor B
- participant C as Charlie

## Messages  
- Solid line: A->>B: Message
- Dotted line: A-->>B: Message
- Solid with X: A-xB: Message
- Dotted with X: A--xB: Message

## Activation
- activate A
- deactivate A
- A->>+B: Message (auto activate)
- B-->>-A: Reply (auto deactivate)

## Notes
- Note right of A: Text
- Note left of B: Text
- Note over A,B: Text""",
        "class": """# Class Diagram Syntax Reference

## Class Definition
class ClassName {
    +public attribute
    -private attribute
    #protected attribute
    ~package attribute
    +public method()
    -private method()
    +abstract method()*
    +static method()$
}

## Relationships
- Inheritance: Animal <|-- Dog
- Composition: Car *-- Engine
- Aggregation: University o-- Student
- Association: Student --> Course
- Link: Student -- Course

## Multiplicity
- 0..1: Zero or One
- 1: Only 1
- 0..*: Zero or More
- *: Many
- 1..*: One or More
- n: n {n>1}"""
    }
    
    return syntax_guides.get(diagram_type, f"Syntax guide for {diagram_type} not yet available.")

@mcp.resource("best_practices://{diagram_type}") 
async def get_best_practices(diagram_type: str) -> str:
    """Get best practices for creating effective diagrams."""
    practices = {
        "flowchart": """# Flowchart Best Practices

1. **Clear Start and End**: Always include clear start and end nodes
2. **Descriptive Labels**: Use action verbs in process boxes (e.g., "Validate Input" not just "Validation")
3. **Consistent Flow**: Top-to-bottom or left-to-right, pick one and stick to it
4. **Decision Points**: Use diamond shapes for decisions with Yes/No or True/False paths
5. **Avoid Crossing Lines**: Reorganize to minimize line crossings
6. **Group Related Items**: Use subgraphs to group related processes
7. **Color Coding**: Use colors to indicate different types of operations
8. **Keep It Simple**: If it's too complex, break into multiple diagrams""",
        "sequence": """# Sequence Diagram Best Practices

1. **Left to Right**: Order participants by when they first appear
2. **Clear Names**: Use role names, not specific person names
3. **Activation Boxes**: Show when objects are active
4. **Return Messages**: Always show return messages for clarity
5. **Self-Calls**: Use self-referencing arrows for internal processing
6. **Time Order**: Messages flow top to bottom chronologically
7. **Group Related**: Use alt/opt/loop blocks for complex flows
8. **Avoid Clutter**: Hide internal details that don't add value"""
    }
    
    return practices.get(diagram_type, f"Best practices for {diagram_type} coming soon!")

# Phase 2 Enhanced Resources
@mcp.resource("examples://by_industry/{industry}")
async def get_industry_examples(industry: str) -> str:
    """Get industry-specific diagram examples."""
    industry_examples = {
        "healthcare": """# Healthcare Industry Diagram Examples

## Patient Flow Diagram
```mermaid
flowchart TD
    A[Patient Arrives] --> B{Emergency?}
    B -->|Yes| C[Triage]
    B -->|No| D[Registration]
    C --> E[Emergency Treatment]
    D --> F[Waiting Room]
    F --> G[Consultation]
    G --> H{Needs Tests?}
    H -->|Yes| I[Lab/Imaging]
    H -->|No| J[Treatment Plan]
    I --> J
    J --> K[Discharge]
```

## Healthcare System Architecture
```mermaid
flowchart TD
    subgraph "Patient Layer"
        Mobile[Mobile App]
        Web[Web Portal]
    end
    
    subgraph "API Gateway"
        Gateway[API Gateway]
    end
    
    subgraph "Services"
        Auth[Authentication]
        Patient[Patient Service]
        Appointment[Appointment Service]
        Medical[Medical Records]
    end
    
    subgraph "Data Layer"
        PatientDB[(Patient DB)]
        MedicalDB[(Medical Records)]
        HL7[HL7 Interface]
    end
    
    Mobile --> Gateway
    Web --> Gateway
    Gateway --> Auth
    Gateway --> Patient
    Gateway --> Appointment
    Gateway --> Medical
    Patient --> PatientDB
    Medical --> MedicalDB
    Medical --> HL7
```""",
        "finance": """# Finance Industry Diagram Examples

## Payment Processing Flow
```mermaid
sequenceDiagram
    participant Customer
    participant Merchant
    participant PaymentGateway
    participant Bank
    participant CardNetwork
    
    Customer->>Merchant: Initiate Payment
    Merchant->>PaymentGateway: Process Payment Request
    PaymentGateway->>PaymentGateway: Validate & Tokenize
    PaymentGateway->>CardNetwork: Authorization Request
    CardNetwork->>Bank: Verify Funds
    Bank-->>CardNetwork: Authorization Response
    CardNetwork-->>PaymentGateway: Authorization Result
    PaymentGateway-->>Merchant: Payment Status
    Merchant-->>Customer: Transaction Complete
```

## Banking System Architecture
```mermaid
classDiagram
    class Account {
        +String accountNumber
        +Decimal balance
        +AccountType type
        +deposit(amount)
        +withdraw(amount)
        +getBalance()
    }
    
    class Customer {
        +String customerId
        +String name
        +String email
        +List~Account~ accounts
        +addAccount(account)
        +getAccounts()
    }
    
    class Transaction {
        +String transactionId
        +TransactionType type
        +Decimal amount
        +DateTime timestamp
        +execute()
        +reverse()
    }
    
    class SecurityModule {
        +authenticate(credentials)
        +authorize(action)
        +encryptData(data)
        +auditLog(action)
    }
    
    Customer "1" --> "*" Account : owns
    Account "1" --> "*" Transaction : has
    Transaction ..> SecurityModule : uses
```""",
        "ecommerce": """# E-commerce Industry Diagram Examples

## Order Processing Flow
```mermaid
flowchart TD
    Start[Customer Browses] --> AddCart[Add to Cart]
    AddCart --> Review[Review Cart]
    Review --> Checkout{Proceed to Checkout?}
    Checkout -->|No| Start
    Checkout -->|Yes| Login{Logged In?}
    Login -->|No| Guest[Guest Checkout]
    Login -->|Yes| Address[Shipping Address]
    Guest --> Address
    Address --> Payment[Payment Method]
    Payment --> Confirm[Confirm Order]
    Confirm --> Process[Process Payment]
    Process --> Success{Payment Success?}
    Success -->|No| Payment
    Success -->|Yes| Order[Create Order]
    Order --> Email[Send Confirmation]
    Email --> Fulfillment[Start Fulfillment]
```

## Microservices Architecture
```mermaid
flowchart TD
    subgraph "Frontend"
        WebApp[Web Application]
        MobileApp[Mobile App]
    end
    
    subgraph "API Layer"
        Gateway[API Gateway]
        LoadBalancer[Load Balancer]
    end
    
    subgraph "Microservices"
        UserService[User Service]
        ProductService[Product Service]
        CartService[Cart Service]
        OrderService[Order Service]
        PaymentService[Payment Service]
        NotificationService[Notification Service]
    end
    
    subgraph "Data Stores"
        UserDB[(User DB)]
        ProductDB[(Product DB)]
        OrderDB[(Order DB)]
        Cache[(Redis Cache)]
    end
    
    subgraph "External"
        PaymentGW[Payment Gateway]
        EmailService[Email Service]
        Analytics[Analytics]
    end
    
    WebApp --> Gateway
    MobileApp --> Gateway
    Gateway --> LoadBalancer
    LoadBalancer --> UserService
    LoadBalancer --> ProductService
    LoadBalancer --> CartService
    LoadBalancer --> OrderService
    UserService --> UserDB
    ProductService --> ProductDB
    OrderService --> OrderDB
    CartService --> Cache
    PaymentService --> PaymentGW
    NotificationService --> EmailService
    OrderService --> Analytics
```"""
    }
    
    return industry_examples.get(industry, f"Examples for {industry} industry coming soon!")

@mcp.resource("examples://by_complexity/{level}")
async def get_complexity_examples(level: str) -> str:
    """Get examples organized by complexity level."""
    complexity_examples = {
        "beginner": """# Beginner Level Diagram Examples

## Simple Flow
```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
```

## Basic Sequence
```mermaid
sequenceDiagram
    Alice->>Bob: Hello Bob!
    Bob-->>Alice: Hi Alice!
```

## Simple Class
```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
```""",
        "intermediate": """# Intermediate Level Diagram Examples

## Decision Flow
```mermaid
flowchart TD
    A[Receive Request] --> B{Valid Request?}
    B -->|Yes| C[Process Request]
    B -->|No| D[Return Error]
    C --> E{Success?}
    E -->|Yes| F[Send Response]
    E -->|No| G[Log Error]
    G --> D
    D --> H[End]
    F --> H
```

## API Interaction Sequence
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    participant Cache
    
    Client->>API: GET /users/123
    API->>Cache: Check cache
    Cache-->>API: Cache miss
    API->>Database: Query user
    Database-->>API: User data
    API->>Cache: Store in cache
    API-->>Client: Return user
```

## System Components
```mermaid
classDiagram
    class UserController {
        -UserService service
        +getUser(id)
        +createUser(data)
        +updateUser(id, data)
        +deleteUser(id)
    }
    
    class UserService {
        -UserRepository repo
        -CacheService cache
        +findById(id)
        +save(user)
        +update(user)
        +delete(id)
    }
    
    class UserRepository {
        +find(id)
        +save(entity)
        +update(entity)
        +delete(id)
    }
    
    class CacheService {
        +get(key)
        +set(key, value)
        +delete(key)
    }
    
    UserController --> UserService : uses
    UserService --> UserRepository : uses
    UserService --> CacheService : uses
```""",
        "advanced": """# Advanced Level Diagram Examples

## Complex Business Process
```mermaid
flowchart TD
    Start[Order Received] --> Validate{Validate Order}
    Validate -->|Invalid| Reject[Reject Order]
    Validate -->|Valid| CheckInventory{Check Inventory}
    
    CheckInventory -->|In Stock| Reserve[Reserve Items]
    CheckInventory -->|Out of Stock| Backorder{Backorder Available?}
    Backorder -->|No| NotifyCustomer[Notify Customer]
    Backorder -->|Yes| CreateBackorder[Create Backorder]
    
    Reserve --> Payment[Process Payment]
    Payment --> PaymentResult{Payment Success?}
    PaymentResult -->|Failed| ReleaseInventory[Release Inventory]
    PaymentResult -->|Success| ConfirmOrder[Confirm Order]
    
    ConfirmOrder --> Split{Split Order?}
    Split -->|Yes| SplitShipments[Create Multiple Shipments]
    Split -->|No| SingleShipment[Create Single Shipment]
    
    SplitShipments --> AssignCarrier[Assign Carriers]
    SingleShipment --> AssignCarrier
    
    AssignCarrier --> GenerateLabels[Generate Shipping Labels]
    GenerateLabels --> NotifyWarehouse[Notify Warehouse]
    NotifyWarehouse --> UpdateTracking[Update Tracking]
    UpdateTracking --> EmailCustomer[Email Customer]
    
    CreateBackorder --> WaitForStock[Wait for Stock]
    WaitForStock --> StockArrived{Stock Arrived?}
    StockArrived -->|Yes| Reserve
    StockArrived -->|No| WaitForStock
    
    ReleaseInventory --> Reject
    NotifyCustomer --> Reject
    Reject --> End[End]
    EmailCustomer --> End
```

## Distributed System Architecture
```mermaid
flowchart TB
    subgraph "Client Applications"
        WebClient[Web Client]
        MobileClient[Mobile Client]
        APIClient[API Client]
    end
    
    subgraph "CDN Layer"
        CDN[CloudFront CDN]
        Static[Static Assets]
    end
    
    subgraph "Load Balancing"
        ALB[Application Load Balancer]
        NLB[Network Load Balancer]
    end
    
    subgraph "API Gateway Cluster"
        Gateway1[API Gateway 1]
        Gateway2[API Gateway 2]
        Gateway3[API Gateway 3]
    end
    
    subgraph "Service Mesh"
        UserMS[User Microservice]
        AuthMS[Auth Microservice]
        ProductMS[Product Microservice]
        OrderMS[Order Microservice]
        PaymentMS[Payment Microservice]
        InventoryMS[Inventory Microservice]
        NotificationMS[Notification Microservice]
    end
    
    subgraph "Data Layer"
        UserDB[(User DB - PostgreSQL)]
        ProductDB[(Product DB - MongoDB)]
        OrderDB[(Order DB - PostgreSQL)]
        EventStore[(Event Store - Kafka)]
        CacheCluster[(Redis Cluster)]
        SearchCluster[(Elasticsearch)]
    end
    
    subgraph "Infrastructure Services"
        Monitoring[Prometheus + Grafana]
        Logging[ELK Stack]
        Tracing[Jaeger]
        ServiceDiscovery[Consul]
    end
    
    WebClient --> CDN
    MobileClient --> CDN
    APIClient --> NLB
    CDN --> ALB
    NLB --> Gateway1
    ALB --> Gateway1
    ALB --> Gateway2
    ALB --> Gateway3
    
    Gateway1 --> UserMS
    Gateway1 --> AuthMS
    Gateway2 --> ProductMS
    Gateway2 --> OrderMS
    Gateway3 --> PaymentMS
    Gateway3 --> InventoryMS
    
    UserMS --> UserDB
    UserMS --> CacheCluster
    AuthMS --> UserDB
    AuthMS --> CacheCluster
    ProductMS --> ProductDB
    ProductMS --> SearchCluster
    OrderMS --> OrderDB
    OrderMS --> EventStore
    PaymentMS --> EventStore
    InventoryMS --> ProductDB
    InventoryMS --> EventStore
    NotificationMS --> EventStore
    
    UserMS -.-> ServiceDiscovery
    AuthMS -.-> ServiceDiscovery
    ProductMS -.-> ServiceDiscovery
    OrderMS -.-> ServiceDiscovery
    
    UserMS -.-> Monitoring
    AuthMS -.-> Monitoring
    ProductMS -.-> Monitoring
    OrderMS -.-> Monitoring
    
    EventStore --> NotificationMS
    NotificationMS --> EmailService[Email Service]
    NotificationMS --> SMSService[SMS Service]
    NotificationMS --> PushService[Push Service]
```"""
    }
    
    return complexity_examples.get(level, f"Examples for {level} complexity coming soon!")

# MCP Prompts for guided diagram creation
@mcp.prompt("create_system_architecture")
async def create_system_architecture(system_name: str, components: List[str], style: str = "modern") -> str:
    """Structured prompt for creating system architecture diagrams."""
    return f"""Let's create a system architecture diagram for {system_name}.

Components to include:
{chr(10).join(f"- {comp}" for comp in components)}

Please follow these steps:
1. Start with a flowchart TD (top-down) layout
2. Create nodes for each component using descriptive labels
3. Show data flow between components
4. Use subgraphs to group related components
5. Add a database node if data storage is implied
6. Use {style} styling conventions

Example structure:
```mermaid
flowchart TD
    Client[Client Application]
    API[API Gateway]
    
    Client --> API
    
    subgraph Services
        Service1[Component 1]
        Service2[Component 2]
    end
    
    API --> Services
```

Consider:
- Security boundaries (use subgraphs)
- Data flow direction
- External vs internal components
- Synchronous vs asynchronous communication (different arrow styles)
"""

@mcp.prompt("document_user_flow")
async def document_user_flow(process_name: str, user_type: str, steps: List[str]) -> str:
    """Guide for creating user flow diagrams."""
    return f"""Let's document the {process_name} flow for {user_type}.

Key steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}

Structure your diagram as:
1. Clear start point: {user_type} begins {process_name}
2. Show each step as an action node
3. Include decision points with diamond shapes
4. Show error/alternative paths
5. End with clear completion state

Best practices:
- Use verb phrases for actions (e.g., "Click Login Button")
- Show system responses
- Include validation/error handling
- Mark optional vs required steps
- Consider mobile vs desktop differences if applicable

Template:
```mermaid
flowchart TD
    Start[User Starts {process_name}]
    Start --> Step1[{steps[0] if steps else 'First Step'}]
    Step1 --> Decision{{Validation Check}}
    Decision -->|Success| NextStep
    Decision -->|Error| ErrorHandler[Show Error Message]
```
"""

@mcp.prompt("analyze_codebase_structure")
async def analyze_codebase_structure(project_type: str, main_components: List[str], show_dependencies: bool = True) -> str:
    """Guide for creating codebase structure diagrams."""
    return f"""Let's visualize the structure of this {project_type} project.

Main components:
{chr(10).join(f"- {comp}" for comp in main_components)}

Recommended approach:
1. Use a class diagram to show module relationships
2. Group by architectural layers (presentation, business, data)
3. Show key interfaces and dependencies
4. Indicate external dependencies differently

For a {project_type}, consider showing:
- Entry points (main, index, app)
- Core business logic modules  
- Data access layer
- External integrations
- Shared utilities

Example structure:
```mermaid
classDiagram
    class App {
        +start()
        +configure()
    }
    
    class Controller {
        +handleRequest()
        +validateInput()
    }
    
    class Service {
        +businessLogic()
        -dataAccess
    }
    
    App --> Controller : uses
    Controller --> Service : calls
```

Include:
{f"- Dependencies between modules" if show_dependencies else "- Module boundaries only"}
- Public vs private methods (+ vs -)
- Abstract classes/interfaces with <<interface>>
- Inheritance relationships where relevant
"""

# Server lifecycle management following MCP standards
async def main():
    """Main entry point for MCP server."""
    # Default to STDIO transport for direct execution
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())