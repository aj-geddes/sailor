#!/usr/bin/env python3
"""
Test script for Phase 2 enhanced MCP tools
Tests the new diagram generation and manipulation capabilities
"""

import asyncio
import json
from sailor_mcp.validators import MermaidValidator
from sailor_mcp.server import (
    generate_from_code,
    generate_from_data, 
    modify_diagram,
    merge_diagrams,
    extract_subgraph,
    optimize_layout
)

async def test_generate_from_code():
    """Test generating diagrams from source code"""
    print("🔧 Testing generate_from_code...")
    
    # Test Python class diagram generation
    python_code = '''
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self._id = None
    
    def login(self):
        pass
    
    def _validate_email(self):
        pass

class Admin(User):
    def __init__(self, name, email, role):
        super().__init__(name, email)
        self.role = role
    
    def manage_users(self):
        pass
    '''
    
    result = await generate_from_code(python_code, "python", "class")
    print(f"✅ Generated class diagram with {result.get('classes_found', 0)} classes")
    print("Generated code preview:")
    print(result['code'][:200] + "..." if len(result['code']) > 200 else result['code'])
    print()

async def test_generate_from_data():
    """Test generating diagrams from data"""
    print("🔧 Testing generate_from_data...")
    
    # Test JSON to ER diagram
    json_data = '''
    {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "orders": [101, 102]},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "orders": [103]}
        ],
        "orders": [
            {"id": 101, "total": 99.99, "items": ["A", "B"]},
            {"id": 102, "total": 149.99, "items": ["C"]}
        ]
    }
    '''
    
    result = await generate_from_data(json_data, "json", "er")
    print(f"✅ Generated ER diagram with {result.get('entities_found', 0)} entities")
    print("Generated code preview:")
    print(result['code'][:200] + "..." if len(result['code']) > 200 else result['code'])
    print()

async def test_modify_diagram():
    """Test diagram modification"""
    print("🔧 Testing modify_diagram...")
    
    base_diagram = """flowchart TD
    A[Start] --> B[Process]
    B --> C[End]"""
    
    modifications = [
        {"action": "add_node", "target": "Auth", "value": "Authentication"},
        {"action": "add_relationship", "target": "A->Auth", "value": ""},
        {"action": "modify_label", "target": "Process", "value": "Process Data"}
    ]
    
    result = await modify_diagram(base_diagram, modifications)
    print(f"✅ Applied {len(result.get('modifications_applied', []))} modifications")
    print("Modifications applied:", result.get('modifications_applied', []))
    print()

async def test_merge_diagrams():
    """Test diagram merging"""
    print("🔧 Testing merge_diagrams...")
    
    diagram1 = """flowchart TD
    A[Start] --> B[Process1]
    B --> C[End]"""
    
    diagram2 = """flowchart TD
    A[Start] --> D[Process2] 
    D --> C[End]"""
    
    result = await merge_diagrams(diagram1, diagram2, "deduplicate")
    print(f"✅ Merged diagrams using 'deduplicate' strategy")
    print("Merge success:", result['success'])
    print()

async def test_extract_subgraph():
    """Test subgraph extraction"""
    print("🔧 Testing extract_subgraph...")
    
    large_diagram = """flowchart TD
    subgraph Auth
        Login[Login Form]
        Verify[Verify Credentials]
    end
    
    subgraph Main
        Dashboard[Dashboard]
        Profile[User Profile]
    end
    
    Login --> Verify
    Verify --> Dashboard
    Dashboard --> Profile"""
    
    result = await extract_subgraph(large_diagram, "Auth", True)
    print(f"✅ Extracted {result.get('nodes_extracted', 0)} nodes from Auth subgraph")
    print(f"Extracted {result.get('lines_extracted', 0)} lines")
    print()

async def test_optimize_layout():
    """Test layout optimization"""
    print("🔧 Testing optimize_layout...")
    
    messy_diagram = """flowchart TD
    A --> B
    C --> D
    B --> E
    A --> C
    E --> F
    D --> F"""
    
    result = await optimize_layout(messy_diagram, "clarity")
    print(f"✅ Optimized layout from {result.get('original_lines', 0)} to {result.get('optimized_lines', 0)} lines")
    print(f"Optimization goal: {result.get('optimization_goal', 'N/A')}")
    print()

async def main():
    """Run all tests"""
    print("🚀 Testing Sailor Phase 2 Enhanced Tools\n")
    
    try:
        await test_generate_from_code()
        await test_generate_from_data()
        await test_modify_diagram()
        await test_merge_diagrams()
        await test_extract_subgraph()
        await test_optimize_layout()
        
        print("🎉 All Phase 2 tools tested successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())