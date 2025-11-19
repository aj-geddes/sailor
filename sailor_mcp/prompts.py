"""
Diagram Prompts Component
As specified in /docs/index.md Core Components architecture
Handles AI-powered diagram generation connecting to AI APIs (OpenAI/Anthropic)
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of AI diagram generation."""
    success: bool
    code: str = ""
    diagram_type: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DiagramPrompts:
    """
    AI-powered diagram generation using prompts.
    As documented in /docs/index.md architecture - connects to AI APIs.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Template prompts for different diagram types
        self.templates = {
            'flowchart': {
                'system': "You are an expert at creating Mermaid flowchart diagrams. Generate clean, well-structured flowcharts.",
                'examples': [
                    {
                        'description': "User authentication process",
                        'code': """graph TD
    A[User Login] --> B{Valid Credentials?}
    B -->|Yes| C[Generate Token]
    B -->|No| D[Show Error]
    C --> E[Access Granted]
    D --> A"""
                    }
                ]
            },
            'sequence': {
                'system': "You are an expert at creating Mermaid sequence diagrams. Generate clear interaction flows.",
                'examples': [
                    {
                        'description': "API call sequence",
                        'code': """sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database
    
    U->>A: Request Data
    A->>D: Query Database
    D->>A: Return Results
    A->>U: Send Response"""
                    }
                ]
            },
            'class': {
                'system': "You are an expert at creating Mermaid class diagrams. Generate well-structured object models.",
                'examples': [
                    {
                        'description': "Basic inheritance model",
                        'code': """classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    Animal <|-- Dog"""
                    }
                ]
            },
            'state': {
                'system': "You are an expert at creating Mermaid state diagrams. Generate clear state transitions.",
                'examples': []
            },
            'er': {
                'system': "You are an expert at creating Mermaid ER diagrams. Generate database relationship models.",
                'examples': []
            }
        }
    
    async def generate_diagram(self, description: str, diagram_type: str = "flowchart", 
                             theme: str = "default", style: str = "classic") -> GenerationResult:
        """
        Generate Mermaid diagram from natural language description.
        Follows architecture in /docs/index.md connecting to AI APIs.
        """
        try:
            # Get template for diagram type
            template = self.templates.get(diagram_type, self.templates['flowchart'])
            
            # Build prompt
            prompt = self._build_prompt(description, diagram_type, template)
            
            # Try different AI providers
            if self.anthropic_api_key:
                result = await self._generate_with_anthropic(prompt, diagram_type)
                if result.success:
                    return result
            
            if self.openai_api_key:
                result = await self._generate_with_openai(prompt, diagram_type)
                if result.success:
                    return result
            
            # Fallback to template-based generation
            return self._generate_from_template(description, diagram_type, template)
            
        except Exception as e:
            logger.error(f"Diagram generation error: {e}")
            return GenerationResult(
                success=False,
                error=str(e)
            )
    
    def _build_prompt(self, description: str, diagram_type: str, template: Dict) -> str:
        """Build AI prompt for diagram generation."""
        system_msg = template['system']
        
        examples_text = ""
        if template['examples']:
            examples_text = "\n\nExamples:\n"
            for example in template['examples']:
                examples_text += f"\nDescription: {example['description']}\n"
                examples_text += f"Code:\n{example['code']}\n"
        
        prompt = f"""{system_msg}

Generate a Mermaid {diagram_type} diagram based on this description: {description}

{examples_text}

Requirements:
1. Use proper Mermaid syntax for {diagram_type} diagrams
2. Make the diagram clear and well-structured
3. Include relevant nodes, connections, and labels
4. Ensure the output is valid Mermaid code
5. Only return the Mermaid code, no explanations

Mermaid {diagram_type} code:"""
        
        return prompt
    
    async def _generate_with_anthropic(self, prompt: str, diagram_type: str) -> GenerationResult:
        """Generate diagram using Anthropic API."""
        try:
            # Import anthropic only if API key is available
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            response = await asyncio.to_thread(
                client.messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            code = response.content[0].text.strip()
            
            # Clean up the response
            code = self._clean_generated_code(code)
            
            return GenerationResult(
                success=True,
                code=code,
                diagram_type=diagram_type,
                metadata={'provider': 'anthropic', 'model': 'claude-3-sonnet'}
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return GenerationResult(
                success=False,
                error=f"Anthropic API error: {str(e)}"
            )
    
    async def _generate_with_openai(self, prompt: str, diagram_type: str) -> GenerationResult:
        """Generate diagram using OpenAI API."""
        try:
            # Import openai only if API key is available
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up the response
            code = self._clean_generated_code(code)
            
            return GenerationResult(
                success=True,
                code=code,
                diagram_type=diagram_type,
                metadata={'provider': 'openai', 'model': 'gpt-3.5-turbo'}
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return GenerationResult(
                success=False,
                error=f"OpenAI API error: {str(e)}"
            )
    
    def _generate_from_template(self, description: str, diagram_type: str, 
                               template: Dict) -> GenerationResult:
        """Generate diagram using templates as fallback."""
        if diagram_type == 'flowchart':
            code = f"""graph TD
    A[{description}] --> B{{Decision}}
    B -->|Yes| C[Success]
    B -->|No| D[Try Again]
    C --> E[End]
    D --> A"""
        
        elif diagram_type == 'sequence':
            code = f"""sequenceDiagram
    participant User
    participant System
    
    User->>System: {description}
    System->>User: Response"""
        
        elif diagram_type == 'class':
            code = f"""classDiagram
    class Entity {{
        +String name
        +process()
    }}
    
    note for Entity : {description}"""
        
        else:
            # Default to simple flowchart
            code = f"""graph TD
    Start --> Process[{description}]
    Process --> End"""
        
        return GenerationResult(
            success=True,
            code=code,
            diagram_type=diagram_type,
            metadata={'provider': 'template', 'fallback': True}
        )
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean up AI-generated code."""
        # Remove markdown code blocks
        if code.startswith('```'):
            lines = code.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].startswith('```'):
                lines = lines[:-1]
            code = '\n'.join(lines)
        
        # Remove extra whitespace
        code = code.strip()
        
        return code
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported diagram types."""
        return list(self.templates.keys())
    
    def get_example(self, diagram_type: str) -> Optional[str]:
        """Get example code for a diagram type."""
        template = self.templates.get(diagram_type)
        if template and template['examples']:
            return template['examples'][0]['code']
        return None