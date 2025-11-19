"""
Mermaid Resources Component
As specified in /docs/index.md Core Components architecture
Manages diagram templates, examples, and resource metadata
"""

from typing import Dict, List, Optional, Any
import json


class MermaidResources:
    """
    Manages Mermaid diagram resources and templates.
    As documented in /docs/index.md Core Components architecture.
    """
    
    def __init__(self):
        self.diagram_types = {
            'flowchart': {
                'name': 'Flowchart',
                'description': 'Flow diagrams and process charts',
                'syntax': 'graph TD',
                'example': """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Do this]
    B -->|No| D[Do that]
    C --> E[End]
    D --> E""",
                'templates': [
                    {
                        'name': 'Basic Process',
                        'description': 'Simple process flow',
                        'code': """graph TD
    Start([Start]) --> Input[Get Input]
    Input --> Process[Process Data]
    Process --> Output[Generate Output]
    Output --> End([End])"""
                    },
                    {
                        'name': 'Decision Tree',
                        'description': 'Decision-based flow',
                        'code': """graph TD
    A[Problem] --> B{Is it simple?}
    B -->|Yes| C[Simple Solution]
    B -->|No| D[Complex Analysis]
    D --> E{Need help?}
    E -->|Yes| F[Get Expert Help]
    E -->|No| G[Work Independently]
    C --> H[Complete]
    F --> H
    G --> H"""
                    }
                ]
            },
            'sequence': {
                'name': 'Sequence Diagram',
                'description': 'Interaction sequences between entities',
                'syntax': 'sequenceDiagram',
                'example': """sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob!
    B->>A: Hi Alice!""",
                'templates': [
                    {
                        'name': 'API Call',
                        'description': 'Basic API interaction',
                        'code': """sequenceDiagram
    participant Client
    participant API
    participant Database
    
    Client->>API: Request
    API->>Database: Query
    Database->>API: Data
    API->>Client: Response"""
                    },
                    {
                        'name': 'Authentication Flow',
                        'description': 'User authentication sequence',
                        'code': """sequenceDiagram
    participant User
    participant App
    participant Auth
    participant Database
    
    User->>App: Login Request
    App->>Auth: Validate Credentials
    Auth->>Database: Check User
    Database->>Auth: User Data
    Auth->>App: Auth Token
    App->>User: Login Success"""
                    }
                ]
            },
            'class': {
                'name': 'Class Diagram',
                'description': 'Object-oriented class structures',
                'syntax': 'classDiagram',
                'example': """classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    Animal <|-- Dog""",
                'templates': [
                    {
                        'name': 'Basic Inheritance',
                        'description': 'Simple class inheritance',
                        'code': """classDiagram
    class Vehicle {
        +String brand
        +String model
        +start()
        +stop()
    }
    class Car {
        +int doors
        +openDoors()
    }
    class Motorcycle {
        +boolean hasSidecar
        +wheelie()
    }
    Vehicle <|-- Car
    Vehicle <|-- Motorcycle"""
                    }
                ]
            },
            'state': {
                'name': 'State Diagram', 
                'description': 'State machines and transitions',
                'syntax': 'stateDiagram-v2',
                'example': """stateDiagram-v2
    [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]""",
                'templates': [
                    {
                        'name': 'Simple State Machine',
                        'description': 'Basic state transitions',
                        'code': """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : start
    Processing --> Success : complete
    Processing --> Error : fail
    Success --> [*]
    Error --> Idle : retry
    Error --> [*] : abort"""
                    }
                ]
            },
            'er': {
                'name': 'ER Diagram',
                'description': 'Entity relationship diagrams',
                'syntax': 'erDiagram',
                'example': """erDiagram
    CUSTOMER {
        int id PK
        string name
        string email
    }
    ORDER {
        int id PK
        int customer_id FK
        date order_date
    }
    CUSTOMER ||--o{ ORDER : places""",
                'templates': [
                    {
                        'name': 'Basic Database',
                        'description': 'Simple database schema',
                        'code': """erDiagram
    USER {
        int id PK
        string username UK
        string email UK
        datetime created_at
    }
    POST {
        int id PK
        int user_id FK
        string title
        text content
        datetime created_at
    }
    COMMENT {
        int id PK
        int post_id FK
        int user_id FK
        text content
        datetime created_at
    }
    USER ||--o{ POST : creates
    USER ||--o{ COMMENT : writes
    POST ||--o{ COMMENT : has"""
                    }
                ]
            },
            'gantt': {
                'name': 'Gantt Chart',
                'description': 'Project timelines and schedules',
                'syntax': 'gantt',
                'example': """gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Planning
    Research           :a1, 2024-01-01, 7d
    Design             :a2, after a1, 5d
    section Development
    Implementation     :a3, after a2, 14d
    Testing           :a4, after a3, 7d""",
                'templates': [
                    {
                        'name': 'Software Project',
                        'description': 'Typical software development timeline',
                        'code': """gantt
    title Software Development Project
    dateFormat YYYY-MM-DD
    section Planning
    Requirements       :req, 2024-01-01, 5d
    Design            :design, after req, 7d
    section Development
    Backend           :backend, after design, 14d
    Frontend          :frontend, after design, 14d
    Integration       :integration, after backend, 5d
    section Testing
    Unit Testing      :unit, after backend, 3d
    System Testing    :system, after integration, 5d
    User Testing      :user, after system, 3d"""
                    }
                ]
            },
            'pie': {
                'name': 'Pie Chart',
                'description': 'Statistical pie charts',
                'syntax': 'pie',
                'example': """pie title Survey Results
    "Option A" : 45
    "Option B" : 30
    "Option C" : 15
    "Option D" : 10""",
                'templates': [
                    {
                        'name': 'Market Share',
                        'description': 'Market share distribution',
                        'code': """pie title Market Share Q1 2024
    "Company A" : 35
    "Company B" : 25
    "Company C" : 20
    "Others" : 20"""
                    }
                ]
            },
            'journey': {
                'name': 'User Journey',
                'description': 'User experience flows',
                'syntax': 'journey',
                'example': """journey
    title My working day
    section Go to work
      Make tea: 5: Me
      Go upstairs: 3: Me
      Do work: 1: Me, Cat
    section Go home
      Go downstairs: 5: Me
      Sit down: 5: Me""",
                'templates': [
                    {
                        'name': 'Customer Journey',
                        'description': 'Customer experience flow',
                        'code': """journey
    title Customer Purchase Journey
    section Discovery
      See advertisement: 3: Customer
      Visit website: 4: Customer
      Browse products: 4: Customer
    section Evaluation
      Compare options: 3: Customer
      Read reviews: 5: Customer
      Check pricing: 4: Customer
    section Purchase
      Add to cart: 5: Customer
      Checkout: 3: Customer
      Complete payment: 4: Customer"""
                    }
                ]
            },
            'mindmap': {
                'name': 'Mind Map',
                'description': 'Hierarchical information structure',
                'syntax': 'mindmap',
                'example': """mindmap
  root((mindmap))
    Origins
      Long history
      ::icon(fa fa-book)
      Popularisation
        British popular psychology author Tony Buzan
    Research
      On effectiveness<br/>and features
      On Automatic creation
        Uses
            Creative techniques
            Strategic planning
            Argument mapping
    Tools
      Pen and paper
      Mermaid""",
                'templates': [
                    {
                        'name': 'Project Planning',
                        'description': 'Project breakdown structure',
                        'code': """mindmap
  root((Project))
    Planning
      Requirements
      Timeline
      Resources
    Development
      Design
      Implementation
      Testing
    Deployment
      Production
      Monitoring
      Support"""
                    }
                ]
            }
        }
    
    def list_diagram_types(self) -> str:
        """List all available diagram types."""
        types_info = []
        for type_id, info in self.diagram_types.items():
            types_info.append(f"**{info['name']}** ({type_id}): {info['description']}")
        
        return "Available Diagram Types:\n" + "\n".join(types_info)
    
    def get_template(self, diagram_type: str) -> str:
        """Get template for specific diagram type."""
        if diagram_type not in self.diagram_types:
            return f"Unknown diagram type: {diagram_type}"
        
        info = self.diagram_types[diagram_type]
        
        result = f"# {info['name']} Template\n\n"
        result += f"**Description**: {info['description']}\n"
        result += f"**Syntax**: `{info['syntax']}`\n\n"
        result += "## Basic Example:\n```mermaid\n"
        result += info['example']
        result += "\n```\n\n"
        
        if info['templates']:
            result += "## Templates:\n\n"
            for template in info['templates']:
                result += f"### {template['name']}\n"
                result += f"{template['description']}\n\n"
                result += "```mermaid\n"
                result += template['code']
                result += "\n```\n\n"
        
        return result
    
    def get_examples(self, diagram_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get examples for diagram type(s)."""
        examples = []
        
        if diagram_type:
            if diagram_type in self.diagram_types:
                info = self.diagram_types[diagram_type]
                examples.append({
                    'type': diagram_type,
                    'name': f"Basic {info['name']}",
                    'description': info['description'],
                    'code': info['example']
                })
                
                for template in info['templates']:
                    examples.append({
                        'type': diagram_type,
                        'name': template['name'],
                        'description': template['description'],
                        'code': template['code']
                    })
        else:
            # Return examples for all types
            for type_id, info in self.diagram_types.items():
                examples.append({
                    'type': type_id,
                    'name': f"Basic {info['name']}",
                    'description': info['description'],
                    'code': info['example']
                })
        
        return examples
    
    def get_diagram_info(self, diagram_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a diagram type."""
        return self.diagram_types.get(diagram_type)
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by query."""
        results = []
        query_lower = query.lower()
        
        for type_id, info in self.diagram_types.items():
            # Search in diagram type name and description
            if query_lower in info['name'].lower() or query_lower in info['description'].lower():
                results.append({
                    'type': type_id,
                    'name': info['name'],
                    'description': info['description'],
                    'code': info['example'],
                    'match': 'diagram_type'
                })
            
            # Search in templates
            for template in info['templates']:
                if (query_lower in template['name'].lower() or 
                    query_lower in template['description'].lower()):
                    results.append({
                        'type': type_id,
                        'name': template['name'],
                        'description': template['description'],
                        'code': template['code'],
                        'match': 'template'
                    })
        
        return results
    
    def get_syntax_help(self, diagram_type: str) -> str:
        """Get syntax help for a diagram type."""
        if diagram_type not in self.diagram_types:
            return f"Unknown diagram type: {diagram_type}"
        
        info = self.diagram_types[diagram_type]
        
        help_text = f"# {info['name']} Syntax Help\n\n"
        help_text += f"**Start with**: `{info['syntax']}`\n\n"
        
        # Add type-specific syntax help
        if diagram_type == 'flowchart':
            help_text += """## Common Elements:
- Nodes: `A[Rectangle]`, `B(Round)`, `C{Diamond}`, `D((Circle))`
- Connections: `A --> B`, `A --- B`, `A -.-> B`
- Labels: `A -->|label| B`
- Subgraphs: `subgraph title ... end`
"""
        elif diagram_type == 'sequence':
            help_text += """## Common Elements:
- Participants: `participant A as Alice`
- Messages: `A->>B: Message`, `A-->>B: Async`
- Notes: `note over A,B: Note text`
- Loops: `loop condition ... end`
"""
        elif diagram_type == 'class':
            help_text += """## Common Elements:
- Classes: `class ClassName { +method() }`
- Relationships: `A <|-- B` (inheritance), `A --> B` (association)
- Visibility: `+` public, `-` private, `#` protected
"""
        
        return help_text