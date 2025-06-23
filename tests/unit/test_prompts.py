"""Unit tests for prompt generation"""
import pytest
from src.sailor_mcp.prompts import PromptGenerator, DiagramPrompt


class TestPromptGenerator:
    """Test cases for PromptGenerator"""
    
    def test_get_flowchart_prompt_basic(self):
        """Test basic flowchart prompt generation"""
        prompt = PromptGenerator.get_flowchart_prompt("User Registration")
        
        assert "User Registration" in prompt
        assert "Starting Point" in prompt
        assert "Main Steps" in prompt
        assert "Decision Points" in prompt
        assert "End Points" in prompt
        assert "Style Preferences" in prompt
    
    def test_get_flowchart_prompt_with_complexity(self):
        """Test flowchart prompt with different complexity levels"""
        simple = PromptGenerator.get_flowchart_prompt("Process", "simple")
        medium = PromptGenerator.get_flowchart_prompt("Process", "medium")
        complex = PromptGenerator.get_flowchart_prompt("Process", "complex")
        
        assert "simple" in simple
        assert "medium" in medium
        assert "complex" in complex
    
    def test_get_sequence_prompt(self):
        """Test sequence diagram prompt generation"""
        prompt = PromptGenerator.get_sequence_prompt("Payment Flow", "4")
        
        assert "Payment Flow" in prompt
        assert "4 main actors" in prompt
        assert "Participants" in prompt
        assert "Initial Action" in prompt
        assert "Message Flow" in prompt
        assert "Response Types" in prompt
        assert "Special Elements" in prompt
    
    def test_get_architecture_prompt(self):
        """Test architecture diagram prompt generation"""
        components = ["Frontend", "API", "Database"]
        prompt = PromptGenerator.get_architecture_prompt("E-commerce System", components)
        
        assert "E-commerce System" in prompt
        assert "Frontend, API, Database" in prompt
        assert "Component Details" in prompt
        assert "Connections" in prompt
        assert "External Dependencies" in prompt
        assert "Architecture Pattern" in prompt
        assert "Deployment Context" in prompt
    
    def test_get_architecture_prompt_empty_components(self):
        """Test architecture prompt with empty components list"""
        prompt = PromptGenerator.get_architecture_prompt("System", [])
        
        assert "your components" in prompt
        assert "System" in prompt
    
    def test_get_data_viz_prompt_pie(self):
        """Test pie chart data visualization prompt"""
        prompt = PromptGenerator.get_data_viz_prompt("percentage", "Market Share")
        
        assert "pie chart" in prompt
        assert "Market Share" in prompt
        assert "Categories and Values" in prompt
        assert "Color Preferences" in prompt
        assert "Desktop: 45%" in prompt  # Example data
    
    def test_get_data_viz_prompt_timeline(self):
        """Test timeline visualization prompt"""
        prompt = PromptGenerator.get_data_viz_prompt("timeline", "Project History")
        
        assert "timeline" in prompt
        assert "Project History" in prompt
        assert "Events with Dates" in prompt
        assert "YYYY-MM-DD" in prompt
        assert "Grouping" in prompt
        assert "Horizontal or vertical" in prompt
    
    def test_get_data_viz_prompt_comparison(self):
        """Test comparison chart prompt"""
        prompt = PromptGenerator.get_data_viz_prompt("comparison", "Quarterly Revenue")
        
        assert "comparison chart" in prompt
        assert "Quarterly Revenue" in prompt
        assert "Data Points" in prompt
        assert "Units" in prompt
        assert "Comparison Type" in prompt
        assert "Q1 2024" in prompt  # Example data
    
    def test_get_data_viz_prompt_bar(self):
        """Test bar chart prompt (alternative to comparison)"""
        prompt = PromptGenerator.get_data_viz_prompt("bar chart", "Sales Data")
        
        assert "comparison chart" in prompt
        assert "Sales Data" in prompt
        assert "bars" in prompt
    
    def test_get_data_viz_prompt_generic(self):
        """Test generic data visualization prompt"""
        prompt = PromptGenerator.get_data_viz_prompt("custom", "My Data")
        
        assert "My Data" in prompt
        assert "custom visualization" in prompt
        assert "Data Points" in prompt
        assert "Visual Preference" in prompt
    
    def test_get_gantt_prompt(self):
        """Test Gantt chart prompt generation"""
        prompt = PromptGenerator.get_gantt_prompt("Website Redesign", "3 months")
        
        assert "Website Redesign" in prompt
        assert "3 months" in prompt
        assert "Project Phases" in prompt
        assert "Tasks per Phase" in prompt
        assert "Dependencies" in prompt
        assert "Resources" in prompt
        assert "Critical Path" in prompt
        assert "Visual Preferences" in prompt
    
    def test_get_state_diagram_prompt(self):
        """Test state diagram prompt generation"""
        prompt = PromptGenerator.get_state_diagram_prompt("Order Processing System")
        
        assert "Order Processing System" in prompt
        assert "Initial State" in prompt
        assert "States" in prompt
        assert "Transitions" in prompt
        assert "Final States" in prompt
        assert "Special Behaviors" in prompt
        assert "parallel states" in prompt
    
    def test_get_er_diagram_prompt(self):
        """Test ER diagram prompt generation"""
        prompt = PromptGenerator.get_er_diagram_prompt("E-commerce Database")
        
        assert "E-commerce Database" in prompt
        assert "Entities" in prompt
        assert "Attributes" in prompt
        assert "Relationships" in prompt
        assert "Cardinality" in prompt
        assert "Business Rules" in prompt
        assert "Customer, Order, Product" in prompt  # Examples
    
    def test_get_class_diagram_prompt(self):
        """Test class diagram prompt generation"""
        prompt = PromptGenerator.get_class_diagram_prompt("Banking System")
        
        assert "Banking System" in prompt
        assert "Classes" in prompt
        assert "Class Details" in prompt
        assert "Attributes" in prompt
        assert "Methods" in prompt
        assert "Relationships" in prompt
        assert "Visibility" in prompt
        assert "Interfaces/Abstract Classes" in prompt
        assert "Design Patterns" in prompt
    
    def test_get_mindmap_prompt(self):
        """Test mindmap prompt generation"""
        prompt = PromptGenerator.get_mindmap_prompt("Machine Learning")
        
        assert "Machine Learning" in prompt
        assert "Central Theme" in prompt
        assert "Main Branches" in prompt
        assert "Sub-branches" in prompt
        assert "Depth" in prompt
        assert "Special Elements" in prompt
        assert "Style Preferences" in prompt
        assert "icons or emojis" in prompt
    
    def test_parse_user_response_basic(self):
        """Test basic user response parsing"""
        user_input = """1. Starting point: User clicks login
2. Main steps: Validate -> Authenticate -> Redirect
3. Decision: Is valid? Yes/No"""
        
        result = PromptGenerator.parse_user_response("flowchart", user_input)
        
        assert result['raw_input'] == user_input
        assert result['prompt_type'] == "flowchart"
        assert '1' in result['numbered_responses']
        assert '2' in result['numbered_responses']
        assert '3' in result['numbered_responses']
        assert "User clicks login" in result['numbered_responses']['1']
    
    def test_parse_user_response_with_style(self):
        """Test parsing user response with style preferences"""
        user_input = """I want a dark theme with hand-drawn look.
The diagram should flow from left to right.
Use a transparent background."""
        
        result = PromptGenerator.parse_user_response("flowchart", user_input)
        
        assert result.get('theme') == 'dark'
        assert result.get('look') in ['hand-drawn', 'handdrawn']
        assert result.get('background') == 'transparent'
    
    def test_parse_user_response_direction_variants(self):
        """Test parsing different direction specifications"""
        test_cases = [
            ("Make it top to bottom", 'top'),
            ("Use TB direction", 'tb'),
            ("Flow from left to right", 'left'),
            ("LR layout please", 'lr'),
            ("bottom up approach", 'bottom'),
            ("right to left flow", 'right')
        ]
        
        for input_text, expected_dir in test_cases:
            result = PromptGenerator.parse_user_response("flowchart", input_text)
            assert result.get('direction') == expected_dir
    
    def test_parse_user_response_multiline_numbered(self):
        """Test parsing multiline numbered responses"""
        user_input = """1. Components:
   - Frontend: React app
   - Backend: Python Flask
   - Database: PostgreSQL
2. Connections:
   Frontend -> Backend via REST API
   Backend -> Database via SQLAlchemy"""
        
        result = PromptGenerator.parse_user_response("architecture", user_input)
        
        assert '1' in result['numbered_responses']
        assert '2' in result['numbered_responses']
        assert "Frontend: React app" in result['numbered_responses']['1']
        assert "Frontend -> Backend" in result['numbered_responses']['2']
    
    def test_parse_user_response_empty(self):
        """Test parsing empty response"""
        result = PromptGenerator.parse_user_response("flowchart", "")
        
        assert result['raw_input'] == ""
        assert result['prompt_type'] == "flowchart"
        assert result['numbered_responses'] == {}
    
    def test_parse_user_response_no_numbers(self):
        """Test parsing response without numbered items"""
        user_input = "Just create a simple flowchart showing the login process"
        
        result = PromptGenerator.parse_user_response("flowchart", user_input)
        
        assert result['raw_input'] == user_input
        assert result['numbered_responses'] == {}
    
    def test_diagram_prompt_dataclass(self):
        """Test DiagramPrompt dataclass"""
        questions = [
            {"q": "What is the starting point?", "type": "text"},
            {"q": "How many steps?", "type": "number"}
        ]
        examples = {"simple": "A -> B -> C", "complex": "A -> B -> C -> D"}
        
        prompt = DiagramPrompt(
            name="test_prompt",
            description="Test diagram prompt",
            questions=questions,
            examples=examples
        )
        
        assert prompt.name == "test_prompt"
        assert prompt.description == "Test diagram prompt"
        assert len(prompt.questions) == 2
        assert prompt.examples["simple"] == "A -> B -> C"
    
    def test_diagram_prompt_no_examples(self):
        """Test DiagramPrompt without examples"""
        prompt = DiagramPrompt(
            name="minimal",
            description="Minimal prompt",
            questions=[]
        )
        
        assert prompt.name == "minimal"
        assert prompt.examples is None