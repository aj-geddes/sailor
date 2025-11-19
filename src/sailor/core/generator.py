"""
AI-powered diagram generation with template support.
"""
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import structlog

from .validator import DiagramType, MermaidValidator


logger = structlog.get_logger()


@dataclass
class GenerationResult:
    """Result of diagram generation."""
    success: bool
    code: str
    diagram_type: Optional[DiagramType] = None
    suggestions: List[str] = None
    alternatives: List[str] = None
    error: Optional[str] = None


@dataclass
class DiagramTemplate:
    """Template for diagram generation."""
    name: str
    type: DiagramType
    description: str
    code: str
    tags: List[str]
    complexity: str  # simple, medium, complex
    use_cases: List[str]


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # For future local model support


class DiagramGenerator:
    """
    AI-powered Mermaid diagram generator with template support.
    
    Features:
    - Natural language to diagram conversion
    - Multiple AI provider support
    - Template-based generation
    - Context-aware suggestions
    - Diagram enhancement and optimization
    """
    
    def __init__(self):
        """Initialize the generator."""
        self.validator = MermaidValidator()
        self.templates = self._load_templates()
        self.models: Dict[AIProvider, Any] = {}
        
        # System prompt for diagram generation
        self.system_prompt = """You are an expert at creating Mermaid diagrams. 
Your task is to generate clear, well-structured, and syntactically correct Mermaid diagrams.

Guidelines:
1. Choose the most appropriate diagram type for the content
2. Use clear and concise labels
3. Maintain proper syntax for the chosen diagram type
4. Keep diagrams readable and not overly complex
5. Use proper node IDs (alphanumeric, starting with letter)
6. Include only the Mermaid code, no explanations

When the user describes what they want, analyze their needs and create the best diagram to represent their information."""
        
        # Few-shot examples for better generation
        self.few_shot_examples = [
            {
                "input": "Show a simple login flow",
                "output": """flowchart TD
    A[User] --> B[Login Page]
    B --> C{Credentials Valid?}
    C -->|Yes| D[Dashboard]
    C -->|No| E[Error Message]
    E --> B"""
            },
            {
                "input": "Database schema for a blog with users, posts, and comments",
                "output": """erDiagram
    USER ||--o{ POST : writes
    USER ||--o{ COMMENT : writes
    POST ||--o{ COMMENT : has
    
    USER {
        int id PK
        string username
        string email
        datetime created_at
    }
    
    POST {
        int id PK
        string title
        text content
        int user_id FK
        datetime published_at
    }
    
    COMMENT {
        int id PK
        text content
        int user_id FK
        int post_id FK
        datetime created_at
    }"""
            }
        ]
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AI models."""
        if config is None:
            config = {}
        
        # Initialize OpenAI
        if config.get("openai_api_key"):
            self.models[AIProvider.OPENAI] = ChatOpenAI(
                api_key=config["openai_api_key"],
                model=config.get("openai_model", "gpt-4"),
                temperature=0.7
            )
        
        # Initialize Anthropic
        if config.get("anthropic_api_key"):
            self.models[AIProvider.ANTHROPIC] = ChatAnthropic(
                api_key=config["anthropic_api_key"],
                model=config.get("anthropic_model", "claude-3-sonnet-20240229"),
                temperature=0.7
            )
        
        logger.info("Diagram generator initialized", providers=list(self.models.keys()))
    
    def _load_templates(self) -> Dict[DiagramType, List[DiagramTemplate]]:
        """Load diagram templates."""
        templates = {
            DiagramType.FLOWCHART: [
                DiagramTemplate(
                    name="Basic Process Flow",
                    type=DiagramType.FLOWCHART,
                    description="Simple linear process flow",
                    code="""flowchart TD
    A[Start] --> B[Process Step 1]
    B --> C[Process Step 2]
    C --> D{Decision Point}
    D -->|Option A| E[Result A]
    D -->|Option B| F[Result B]
    E --> G[End]
    F --> G""",
                    tags=["process", "workflow", "basic"],
                    complexity="simple",
                    use_cases=["Business processes", "User flows", "Algorithms"]
                ),
                DiagramTemplate(
                    name="Swimlane Process",
                    type=DiagramType.FLOWCHART,
                    description="Process flow with multiple actors",
                    code="""flowchart TB
    subgraph Customer
        A[Place Order] --> B[Receive Confirmation]
    end
    
    subgraph System
        B --> C[Process Payment]
        C --> D[Update Inventory]
    end
    
    subgraph Warehouse
        D --> E[Pick Items]
        E --> F[Ship Order]
    end
    
    F --> G[Delivery to Customer]""",
                    tags=["swimlane", "multi-actor", "business"],
                    complexity="medium",
                    use_cases=["Cross-functional processes", "System interactions"]
                )
            ],
            DiagramType.SEQUENCE: [
                DiagramTemplate(
                    name="API Request Flow",
                    type=DiagramType.SEQUENCE,
                    description="REST API interaction sequence",
                    code="""sequenceDiagram
    participant C as Client
    participant S as Server
    participant DB as Database
    
    C->>+S: POST /api/users
    S->>+DB: INSERT user data
    DB-->>-S: User ID
    S-->>-C: 201 Created + User object""",
                    tags=["api", "rest", "backend"],
                    complexity="simple",
                    use_cases=["API documentation", "System integration", "Backend flows"]
                )
            ],
            DiagramType.CLASS: [
                DiagramTemplate(
                    name="Basic OOP Structure",
                    type=DiagramType.CLASS,
                    description="Object-oriented class hierarchy",
                    code="""classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    
    class Dog {
        +String breed
        +bark()
        +wagTail()
    }
    
    class Cat {
        +String color
        +meow()
        +purr()
    }
    
    Animal <|-- Dog
    Animal <|-- Cat""",
                    tags=["oop", "inheritance", "design"],
                    complexity="simple",
                    use_cases=["Software design", "Code documentation", "Architecture"]
                )
            ]
        }
        
        return templates
    
    async def generate_from_description(
        self,
        description: str,
        diagram_type: Optional[str] = None,
        provider: AIProvider = AIProvider.OPENAI,
        enhance: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate Mermaid diagram from natural language description.
        
        Args:
            description: Natural language description
            diagram_type: Preferred diagram type (optional)
            provider: AI provider to use
            enhance: Whether to enhance the generated diagram
            context: Additional context for generation
            
        Returns:
            GenerationResult with generated code
        """
        try:
            # Check if provider is available
            if provider not in self.models:
                # Fallback to template matching
                return self._generate_from_template(description, diagram_type)
            
            # Create prompt
            prompt = self._create_generation_prompt(description, diagram_type, context)
            
            # Generate with AI
            model = self.models[provider]
            response = await model.agenerate([prompt])
            generated_code = response.generations[0][0].text.strip()
            
            # Clean up the response (remove markdown code blocks if present)
            generated_code = self._clean_generated_code(generated_code)
            
            # Validate generated code
            validation = self.validator.validate(generated_code)
            
            # Enhance if requested and valid
            suggestions = []
            alternatives = []
            
            if enhance and validation.is_valid:
                suggestions = await self._generate_suggestions(generated_code, description)
                alternatives = await self._generate_alternatives(generated_code, description)
            
            logger.info(
                "Diagram generated",
                provider=provider.value,
                valid=validation.is_valid,
                diagram_type=validation.diagram_type.value if validation.diagram_type else None
            )
            
            return GenerationResult(
                success=validation.is_valid,
                code=generated_code,
                diagram_type=validation.diagram_type,
                suggestions=suggestions,
                alternatives=alternatives,
                error=validation.errors[0].message if validation.errors else None
            )
            
        except Exception as e:
            logger.error("Generation failed", error=str(e))
            return GenerationResult(
                success=False,
                code="",
                error=str(e)
            )
    
    def _create_generation_prompt(
        self,
        description: str,
        diagram_type: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> List[Any]:
        """Create prompt for diagram generation."""
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add few-shot examples
        for example in self.few_shot_examples:
            messages.append(HumanMessage(content=example["input"]))
            messages.append(AIMessage(content=example["output"]))
        
        # Build user prompt
        user_prompt = description
        
        if diagram_type:
            user_prompt = f"Create a {diagram_type} diagram: {description}"
        
        if context:
            if context.get("complexity"):
                user_prompt += f"\nComplexity level: {context['complexity']}"
            if context.get("style_hints"):
                user_prompt += f"\nStyle preferences: {context['style_hints']}"
        
        messages.append(HumanMessage(content=user_prompt))
        
        return messages
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated code."""
        # Remove markdown code blocks
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1] == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        return code.strip()
    
    def _generate_from_template(
        self,
        description: str,
        diagram_type: Optional[str]
    ) -> GenerationResult:
        """Generate diagram using template matching."""
        # Simple keyword matching for demo
        description_lower = description.lower()
        
        # Try to detect diagram type from description
        if not diagram_type:
            if any(word in description_lower for word in ["flow", "process", "workflow"]):
                diagram_type = "flowchart"
            elif any(word in description_lower for word in ["sequence", "interaction", "api"]):
                diagram_type = "sequence"
            elif any(word in description_lower for word in ["class", "object", "inheritance"]):
                diagram_type = "class"
            else:
                diagram_type = "flowchart"  # Default
        
        # Find matching template
        diagram_enum = DiagramType(diagram_type)
        templates = self.templates.get(diagram_enum, [])
        
        if templates:
            # Return first template as base (in real implementation, do better matching)
            template = templates[0]
            return GenerationResult(
                success=True,
                code=template.code,
                diagram_type=diagram_enum,
                suggestions=["Consider customizing node labels", "Add more specific details"],
                alternatives=None
            )
        
        # Fallback
        return GenerationResult(
            success=False,
            code="",
            error="Could not generate diagram from description"
        )
    
    async def _generate_suggestions(
        self,
        code: str,
        original_description: str
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Analyze code
        validation = self.validator.validate(code)
        
        # Basic suggestions based on metadata
        if validation.metadata.get("node_count", 0) < 3:
            suggestions.append("Consider adding more detail to your diagram")
        
        if not validation.metadata.get("has_style"):
            suggestions.append("Add styling with 'style' or 'classDef' for better visual hierarchy")
        
        if validation.metadata.get("complexity", 0) > 20:
            suggestions.append("Consider breaking this into multiple smaller diagrams")
        
        return suggestions
    
    async def _generate_alternatives(
        self,
        code: str,
        description: str
    ) -> List[str]:
        """Generate alternative diagram representations."""
        # In a real implementation, use AI to suggest different diagram types
        return []
    
    def get_templates(self, diagram_type: Optional[str] = None) -> List[DiagramTemplate]:
        """Get available templates."""
        if diagram_type:
            try:
                diagram_enum = DiagramType(diagram_type)
                return self.templates.get(diagram_enum, [])
            except ValueError:
                return []
        
        # Return all templates
        all_templates = []
        for templates in self.templates.values():
            all_templates.extend(templates)
        return all_templates
    
    def enhance_diagram(self, code: str, enhancement_type: str = "clarity") -> str:
        """
        Enhance existing diagram.
        
        Enhancement types:
        - clarity: Improve labels and structure
        - style: Add visual styling
        - optimize: Reduce complexity
        """
        # This would use AI to enhance the diagram
        # For now, return as-is
        return code