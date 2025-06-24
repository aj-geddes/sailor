"""Comprehensive Mermaid.js resources, examples, and templates"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class MermaidExample:
    """A complete Mermaid diagram example"""
    name: str
    description: str
    code: str
    category: str
    complexity: str  # "basic", "intermediate", "advanced"
    features: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)


@dataclass
class MermaidTemplate:
    """A template for generating diagrams"""
    name: str
    template: str
    variables: List[str]
    description: str
    example_vars: Dict[str, str] = field(default_factory=dict)


class MermaidResources:
    """Complete library of Mermaid.js resources"""
    
    def __init__(self):
        self.examples = self._load_examples()
        self.templates = self._load_templates()
        self.syntax_guide = self._load_syntax_guide()
        self.best_practices = self._load_best_practices()
        
    def _load_examples(self) -> Dict[str, List[MermaidExample]]:
        """Load comprehensive diagram examples"""
        return {
            "flowchart": [
                MermaidExample(
                    name="Simple Process Flow",
                    description="Basic process with decision points",
                    code="""flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Perfect!]
    B -->|No| D[Debug]
    D --> E[Fix Issue]
    E --> B
    C --> F[End]""",
                    category="flowchart",
                    complexity="basic",
                    features=["decision", "loop", "end_points"],
                    use_cases=["troubleshooting", "basic_workflow"]
                ),
                MermaidExample(
                    name="User Authentication Flow",
                    description="Complete login process with error handling",
                    code="""flowchart TD
    A[User visits site] --> B[Login required?]
    B -->|No| C[Access granted]
    B -->|Yes| D[Show login form]
    D --> E[User enters credentials]
    E --> F{Valid credentials?}
    F -->|Yes| G[Generate session]
    F -->|No| H[Show error]
    H --> I{Attempts < 3?}
    I -->|Yes| D
    I -->|No| J[Account locked]
    G --> K[Redirect to dashboard]
    K --> C
    J --> L[Send unlock email]""",
                    category="flowchart",
                    complexity="intermediate",
                    features=["authentication", "error_handling", "loops", "conditions"],
                    use_cases=["web_development", "security", "user_experience"]
                ),
                MermaidExample(
                    name="CI/CD Pipeline",
                    description="DevOps deployment pipeline with parallel steps",
                    code="""flowchart LR
    A[Code Commit] --> B[Trigger Build]
    B --> C[Run Tests]
    C --> D{Tests Pass?}
    D -->|No| E[Notify Developer]
    D -->|Yes| F[Build Docker Image]
    F --> G[Security Scan]
    G --> H[Push to Registry]
    H --> I{Deploy to Staging}
    I --> J[Integration Tests]
    J --> K{Tests Pass?}
    K -->|No| L[Rollback]
    K -->|Yes| M[Deploy to Production]
    M --> N[Health Checks]
    N --> O[Monitor Metrics]
    
    subgraph "Parallel Testing"
        C1[Unit Tests]
        C2[Lint Check]
        C3[Security Scan]
    end
    
    C --> C1
    C --> C2
    C --> C3""",
                    category="flowchart",
                    complexity="advanced",
                    features=["subgraphs", "parallel_flows", "devops"],
                    use_cases=["software_development", "automation", "deployment"]
                )
            ],
            "sequence": [
                MermaidExample(
                    name="API Request Flow",
                    description="Simple REST API interaction",
                    code="""sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database
    
    User->>Frontend: Submit form
    Frontend->>Backend: POST /api/users
    Backend->>Database: INSERT user
    Database-->>Backend: Success
    Backend-->>Frontend: 201 Created
    Frontend-->>User: Show success message""",
                    category="sequence",
                    complexity="basic",
                    features=["participants", "sync_messages", "responses"],
                    use_cases=["api_design", "web_development"]
                ),
                MermaidExample(
                    name="Microservices Communication",
                    description="Complex microservices interaction with async patterns",
                    code="""sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant Order as Order Service
    participant Payment as Payment Service
    participant Inventory as Inventory Service
    participant Queue as Message Queue
    participant Email as Email Service
    
    Client->>Gateway: POST /orders
    Gateway->>Auth: Validate token
    Auth-->>Gateway: Token valid
    
    Gateway->>Order: Create order
    Order->>Inventory: Check availability
    Inventory-->>Order: Items available
    
    par Parallel Processing
        Order->>Payment: Process payment
        Payment-->>Order: Payment confirmed
    and
        Order->>Queue: Publish order event
        Queue->>Email: Send confirmation
        Email-->>Queue: Email sent
    end
    
    Order-->>Gateway: Order created (ID: 12345)
    Gateway-->>Client: 201 Created
    
    Note over Queue,Email: Async email processing""",
                    category="sequence",
                    complexity="advanced",
                    features=["microservices", "parallel", "async", "notes"],
                    use_cases=["system_design", "distributed_systems", "e-commerce"]
                )
            ],
            "class": [
                MermaidExample(
                    name="E-commerce Domain Model",
                    description="Complete class diagram for online store",
                    code="""classDiagram
    class User {
        +int id
        +string email
        +string name
        +DateTime createdAt
        +login(password) bool
        +logout() void
        +updateProfile(data) void
    }
    
    class Customer {
        +string address
        +string phone
        +List~Order~ orders
        +placeOrder(items) Order
        +viewOrderHistory() List~Order~
    }
    
    class Admin {
        +string role
        +List~string~ permissions
        +manageProducts() void
        +viewAnalytics() Report
    }
    
    class Product {
        +int id
        +string name
        +decimal price
        +int stockQuantity
        +string description
        +updateStock(quantity) void
        +isAvailable() bool
    }
    
    class Order {
        +int id
        +DateTime orderDate
        +OrderStatus status
        +decimal totalAmount
        +List~OrderItem~ items
        +calculateTotal() decimal
        +addItem(product, quantity) void
        +removeItem(productId) void
    }
    
    class OrderItem {
        +int quantity
        +decimal unitPrice
        +Product product
        +getSubtotal() decimal
    }
    
    class Payment {
        +int id
        +decimal amount
        +PaymentMethod method
        +PaymentStatus status
        +DateTime processedAt
        +process() bool
        +refund() bool
    }
    
    User <|-- Customer
    User <|-- Admin
    Customer ||--o{ Order : places
    Order ||--o{ OrderItem : contains
    OrderItem }o--|| Product : references
    Order ||--|| Payment : has
    
    <<enumeration>> OrderStatus
    OrderStatus : PENDING
    OrderStatus : CONFIRMED
    OrderStatus : SHIPPED
    OrderStatus : DELIVERED
    OrderStatus : CANCELLED
    
    <<enumeration>> PaymentStatus
    PaymentStatus : PENDING
    PaymentStatus : SUCCESS
    PaymentStatus : FAILED
    PaymentStatus : REFUNDED""",
                    category="class",
                    complexity="advanced",
                    features=["inheritance", "composition", "enumerations", "relationships"],
                    use_cases=["domain_modeling", "system_design", "documentation"]
                )
            ],
            "er": [
                MermaidExample(
                    name="Blog Database Schema",
                    description="Complete database design for blogging platform",
                    code="""erDiagram
    User {
        int id PK
        string email UK
        string username UK
        string password_hash
        string first_name
        string last_name
        datetime created_at
        datetime updated_at
        boolean is_active
        string role
    }
    
    Post {
        int id PK
        int author_id FK
        string title
        text content
        text excerpt
        string slug UK
        string status
        datetime published_at
        datetime created_at
        datetime updated_at
        int view_count
        boolean allow_comments
    }
    
    Category {
        int id PK
        string name UK
        string slug UK
        text description
        string color
        int parent_id FK
        int sort_order
    }
    
    Tag {
        int id PK
        string name UK
        string slug UK
        string color
        int usage_count
    }
    
    Comment {
        int id PK
        int post_id FK
        int user_id FK
        int parent_id FK
        text content
        string status
        datetime created_at
        string author_email
        string author_name
        string author_ip
    }
    
    PostCategory {
        int post_id FK
        int category_id FK
    }
    
    PostTag {
        int post_id FK
        int tag_id FK
    }
    
    Media {
        int id PK
        int user_id FK
        string filename
        string original_name
        string mime_type
        int file_size
        string file_path
        text alt_text
        datetime created_at
    }
    
    PostMedia {
        int post_id FK
        int media_id FK
        string usage_type
    }
    
    User ||--o{ Post : writes
    User ||--o{ Comment : makes
    User ||--o{ Media : uploads
    Post ||--o{ Comment : has
    Post }o--o{ Category : belongs_to
    Post }o--o{ Tag : tagged_with
    Post }o--o{ Media : uses
    Category ||--o{ Category : parent_of
    Comment ||--o{ Comment : replies_to""",
                    category="er",
                    complexity="advanced",
                    features=["foreign_keys", "many_to_many", "self_referencing", "detailed_attributes"],
                    use_cases=["database_design", "cms", "documentation"]
                )
            ],
            "state": [
                MermaidExample(
                    name="Order State Machine",
                    description="E-commerce order lifecycle management",
                    code="""stateDiagram-v2
    [*] --> Created
    Created --> Confirmed : payment_received
    Created --> Cancelled : customer_cancels / refund_payment
    
    Confirmed --> Processing : start_fulfillment
    Confirmed --> Cancelled : inventory_unavailable / refund_payment
    
    Processing --> Shipped : items_dispatched / send_tracking
    Processing --> PartiallyShipped : some_items_dispatched
    Processing --> Cancelled : fulfillment_failed / refund_payment
    
    PartiallyShipped --> Shipped : remaining_items_dispatched
    PartiallyShipped --> Cancelled : cancel_remaining / partial_refund
    
    Shipped --> InTransit : tracking_updated
    Shipped --> Delivered : delivery_confirmed
    Shipped --> Lost : tracking_shows_lost / investigate
    
    InTransit --> Delivered : delivery_confirmed / update_customer
    InTransit --> Lost : tracking_timeout / investigate
    InTransit --> Returned : delivery_failed / process_return
    
    Delivered --> Completed : customer_satisfied
    Delivered --> ReturnRequested : customer_requests_return
    
    ReturnRequested --> Returned : return_approved / send_return_label
    ReturnRequested --> Completed : return_denied
    
    Returned --> Refunded : return_processed / issue_refund
    Returned --> Exchanged : exchange_processed / ship_replacement
    
    Lost --> Refunded : investigation_complete / issue_refund
    
    Refunded --> [*]
    Completed --> [*]
    Exchanged --> [*]
    Cancelled --> [*]
    
    state Processing {
        [*] --> PickingItems
        PickingItems --> PackingItems : items_picked
        PackingItems --> ReadyToShip : items_packed
        ReadyToShip --> [*]
    }""",
                    category="state",
                    complexity="advanced",
                    features=["nested_states", "actions", "guards", "complex_transitions"],
                    use_cases=["business_process", "workflow", "system_design"]
                )
            ],
            "gantt": [
                MermaidExample(
                    name="Software Development Project",
                    description="Complete project timeline with dependencies",
                    code="""gantt
    title Software Development Project Timeline
    dateFormat YYYY-MM-DD
    section Planning
        Requirements Gathering    :done, req, 2024-01-01, 2024-01-14
        Technical Design         :done, design, after req, 10d
        Architecture Review      :done, arch, after design, 3d
        Project Setup           :done, setup, after arch, 2d
        
    section Development Phase 1
        Backend API Development  :active, backend1, after setup, 20d
        Database Schema         :done, db, after setup, 5d
        Authentication System   :auth, after db, 8d
        User Management         :users, after auth, 10d
        
    section Frontend Development
        UI Framework Setup      :ui-setup, after setup, 3d
        Component Library       :components, after ui-setup, 15d
        User Interface         :ui, after components, 20d
        Integration Testing    :integration, after backend1, 10d
        
    section Development Phase 2
        Advanced Features      :features, after users, 15d
        Performance Optimization :perf, after integration, 8d
        Security Hardening     :security, after features, 10d
        
    section Testing & Deployment
        System Testing         :testing, after security, 10d
        User Acceptance Testing :uat, after testing, 7d
        Production Deployment  :deploy, after uat, 3d
        Monitoring Setup       :monitor, after deploy, 2d
        
    section Documentation
        API Documentation      :api-docs, after backend1, 5d
        User Manual           :user-docs, after ui, 8d
        Technical Documentation :tech-docs, after security, 5d""",
                    category="gantt",
                    complexity="intermediate",
                    features=["sections", "dependencies", "status", "milestones"],
                    use_cases=["project_management", "software_development", "planning"]
                )
            ],
            "pie": [
                MermaidExample(
                    name="Technology Stack Distribution",
                    description="Programming language usage in projects",
                    code="""pie title Technology Stack Distribution
    "JavaScript" : 35
    "Python" : 25
    "Java" : 20
    "TypeScript" : 12
    "Go" : 5
    "Other" : 3""",
                    category="pie",
                    complexity="basic",
                    features=["labels", "percentages"],
                    use_cases=["reporting", "analytics", "presentations"]
                )
            ],
            "mindmap": [
                MermaidExample(
                    name="Software Architecture Concepts",
                    description="Key concepts in software architecture",
                    code="""mindmap
  root((Software Architecture))
    Design Patterns
      Creational
        Singleton
        Factory
        Builder
      Structural
        Adapter
        Decorator
        Facade
      Behavioral
        Observer
        Strategy
        Command
    Architecture Patterns
      Layered
        Presentation
        Business
        Data
      Microservices
        Service Discovery
        API Gateway
        Event Sourcing
      Event Driven
        Publishers
        Subscribers
        Message Queues
    Quality Attributes
      Performance
        Latency
        Throughput
        Scalability
      Security
        Authentication
        Authorization
        Encryption
      Maintainability
        Modularity
        Testability
        Documentation""",
                    category="mindmap",
                    complexity="intermediate",
                    features=["multi_level", "concepts", "organization"],
                    use_cases=["brainstorming", "knowledge_mapping", "education"]
                )
            ],
            "journey": [
                MermaidExample(
                    name="Customer Onboarding Journey",
                    description="User experience journey for new customers",
                    code="""journey
    title Customer Onboarding Journey
    section Discovery
      Visit website          : 3: Customer
      Browse features        : 4: Customer
      Read testimonials      : 4: Customer
      Compare pricing        : 3: Customer
    section Registration
      Click sign up          : 5: Customer
      Fill registration form : 2: Customer
      Verify email          : 3: Customer
      Complete profile      : 3: Customer
    section First Use
      Watch tutorial        : 4: Customer
      Try basic features    : 5: Customer
      Get stuck on feature  : 1: Customer
      Contact support       : 2: Customer, Support
      Problem resolved      : 5: Customer, Support
    section Engagement
      Explore advanced features : 4: Customer
      Invite team members      : 5: Customer
      Set up integrations     : 3: Customer, Admin
      Provide feedback        : 4: Customer
    section Retention
      Regular usage          : 5: Customer
      Upgrade plan          : 4: Customer
      Refer friends         : 5: Customer
      Become advocate       : 5: Customer""",
                    category="journey",
                    complexity="intermediate",
                    features=["sections", "actors", "emotions", "touchpoints"],
                    use_cases=["user_experience", "customer_success", "service_design"]
                )
            ],
            "timeline": [
                MermaidExample(
                    name="Product Development Timeline",
                    description="Major milestones in product evolution",
                    code="""timeline
    title Product Development Timeline
    
    section 2022
        Q1 : Market Research
           : Competitor Analysis
           : User Interviews
        Q2 : MVP Development
           : Core Features
           : Initial Testing
        Q3 : Beta Launch
           : User Feedback
           : Iterative Improvements
        Q4 : Public Launch
           : Marketing Campaign
           : Customer Acquisition
           
    section 2023
        Q1 : Feature Expansion
           : Mobile App
           : API Integration
        Q2 : Enterprise Features
           : SSO Implementation
           : Advanced Analytics
        Q3 : International Expansion
           : Multi-language Support
           : Regional Compliance
        Q4 : AI Integration
           : Machine Learning
           : Automated Insights
           
    section 2024
        Q1 : Platform Optimization
           : Performance Improvements
           : Scalability Enhancements
        Q2 : Advanced Analytics
           : Real-time Dashboards
           : Predictive Features""",
                    category="timeline",
                    complexity="intermediate",
                    features=["sections", "quarters", "multiple_events"],
                    use_cases=["project_planning", "roadmap", "history"]
                )
            ]
        }
    
    def _load_templates(self) -> Dict[str, List[MermaidTemplate]]:
        """Load diagram templates for quick generation"""
        return {
            "flowchart": [
                MermaidTemplate(
                    name="Process Flow",
                    template="""flowchart {direction}
    A[{start}] --> B{{{decision}}}
    B -->|{yes_label}| C[{yes_action}]
    B -->|{no_label}| D[{no_action}]
    C --> E[{end}]
    D --> E""",
                    variables=["direction", "start", "decision", "yes_label", "yes_action", "no_label", "no_action", "end"],
                    description="Basic process with decision point",
                    example_vars={
                        "direction": "TD",
                        "start": "Start Process",
                        "decision": "Is data valid?",
                        "yes_label": "Yes",
                        "yes_action": "Process Data",
                        "no_label": "No",
                        "no_action": "Show Error",
                        "end": "Complete"
                    }
                ),
                MermaidTemplate(
                    name="Approval Workflow",
                    template="""flowchart TD
    A[{request_start}] --> B[{review_step}]
    B --> C{{{approval_decision}}}
    C -->|Approved| D[{approved_action}]
    C -->|Rejected| E[{rejected_action}]
    C -->|Needs Changes| F[{changes_action}]
    F --> A
    D --> G[{completion}]
    E --> H[{notification}]""",
                    variables=["request_start", "review_step", "approval_decision", "approved_action", "rejected_action", "changes_action", "completion", "notification"],
                    description="Approval workflow with feedback loop",
                    example_vars={
                        "request_start": "Submit Request",
                        "review_step": "Manager Review",
                        "approval_decision": "Decision?",
                        "approved_action": "Execute Request",
                        "rejected_action": "Archive Request",
                        "changes_action": "Request Changes",
                        "completion": "Mark Complete",
                        "notification": "Notify Requester"
                    }
                )
            ],
            "sequence": [
                MermaidTemplate(
                    name="API Interaction",
                    template="""sequenceDiagram
    participant {client} as {client_label}
    participant {server} as {server_label}
    participant {database} as {database_label}
    
    {client}->>+{server}: {request_message}
    {server}->>+{database}: {db_query}
    {database}-->>-{server}: {db_response}
    {server}-->>-{client}: {response_message}""",
                    variables=["client", "client_label", "server", "server_label", "database", "database_label", "request_message", "db_query", "db_response", "response_message"],
                    description="Basic API request-response pattern",
                    example_vars={
                        "client": "Client",
                        "client_label": "Web Browser",
                        "server": "API",
                        "server_label": "REST API",
                        "database": "DB",
                        "database_label": "PostgreSQL",
                        "request_message": "GET /users/123",
                        "db_query": "SELECT * FROM users WHERE id=123",
                        "db_response": "User data",
                        "response_message": "200 OK + User JSON"
                    }
                )
            ],
            "class": [
                MermaidTemplate(
                    name="Basic Class Structure",
                    template="""classDiagram
    class {class_name} {{
        +{attribute1_type} {attribute1_name}
        +{attribute2_type} {attribute2_name}
        -{private_attribute_type} {private_attribute_name}
        +{method1_name}({method1_params}) {method1_return}
        +{method2_name}({method2_params}) {method2_return}
        -{private_method_name}() void
    }}""",
                    variables=["class_name", "attribute1_type", "attribute1_name", "attribute2_type", "attribute2_name", "private_attribute_type", "private_attribute_name", "method1_name", "method1_params", "method1_return", "method2_name", "method2_params", "method2_return", "private_method_name"],
                    description="Single class with attributes and methods",
                    example_vars={
                        "class_name": "User",
                        "attribute1_type": "string",
                        "attribute1_name": "name",
                        "attribute2_type": "string",
                        "attribute2_name": "email",
                        "private_attribute_type": "string",
                        "private_attribute_name": "password",
                        "method1_name": "login",
                        "method1_params": "password: string",
                        "method1_return": "boolean",
                        "method2_name": "updateEmail",
                        "method2_params": "newEmail: string",
                        "method2_return": "void",
                        "private_method_name": "hashPassword"
                    }
                )
            ]
        }
    
    def _load_syntax_guide(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive syntax reference"""
        return {
            "flowchart": {
                "directions": {
                    "TD": "Top Down",
                    "TB": "Top to Bottom (same as TD)",
                    "BT": "Bottom to Top",
                    "RL": "Right to Left",
                    "LR": "Left to Right"
                },
                "node_shapes": {
                    "A[Rectangle]": "Rectangle",
                    "B(Round edges)": "Round edges",
                    "C([Stadium])": "Stadium-shaped",
                    "D[[Subroutine]]": "Subroutine",
                    "E[(Database)]": "Cylindrical",
                    "F((Circle))": "Circle",
                    "G>Asymmetric]": "Asymmetric",
                    "H{Rhombus}": "Rhombus/Decision",
                    "I{{Hexagon}}": "Hexagon",
                    "J[/Parallelogram/]": "Parallelogram",
                    "K[\\Parallelogram\\]": "Alt Parallelogram",
                    "L[/Trapezoid\\]": "Trapezoid",
                    "M[\\Trapezoid/]": "Alt Trapezoid"
                },
                "links": {
                    "A --> B": "Arrow link",
                    "A --- B": "Open link",
                    "A -.-> B": "Dotted arrow",
                    "A -.- B": "Dotted open",
                    "A ==> B": "Thick arrow",
                    "A === B": "Thick open",
                    "A -->|text| B": "Arrow with text",
                    "A -.->|text| B": "Dotted with text"
                },
                "subgraphs": {
                    "syntax": "subgraph title\n    direction TB\n    A --> B\nend",
                    "description": "Group related nodes together"
                },
                "styling": {
                    "class_definition": "classDef className fill:#f9f,stroke:#333,stroke-width:4px",
                    "apply_class": "class nodeId className",
                    "direct_styling": "A:::className"
                }
            },
            "sequence": {
                "participants": {
                    "participant A": "Define participant",
                    "participant B as Label": "With custom label",
                    "actor A": "Human actor",
                    "box rgba(0,0,255,0.1) Title": "Group participants"
                },
                "messages": {
                    "A->>B": "Solid arrow",
                    "A-->>B": "Dashed arrow", 
                    "A-xB": "Cross on arrow",
                    "A--xB": "Cross on dashed arrow",
                    "A-)B": "Open arrow",
                    "A--)B": "Dashed open arrow"
                },
                "activations": {
                    "A->>+B": "Activate B",
                    "B-->>-A": "Deactivate B",
                    "activate A": "Manual activate",
                    "deactivate A": "Manual deactivate"
                },
                "notes": {
                    "Note right of A: Text": "Note on right",
                    "Note left of A: Text": "Note on left",
                    "Note over A,B: Text": "Note spanning A to B"
                },
                "loops": {
                    "loop Every minute": "Loop with condition",
                    "alt happy path": "Alternative path",
                    "else error": "Else in alternative",
                    "opt optional": "Optional section",
                    "par parallel": "Parallel execution",
                    "and": "Parallel and",
                    "critical": "Critical section",
                    "break": "Break section"
                }
            },
            "class": {
                "visibility": {
                    "+": "Public",
                    "-": "Private", 
                    "#": "Protected",
                    "~": "Package/Internal"
                },
                "relationships": {
                    "A --|> B": "Inheritance",
                    "A --* B": "Composition",
                    "A --o B": "Aggregation",
                    "A --> B": "Association",
                    "A -- B": "Link (solid)",
                    "A ..> B": "Dependency",
                    "A ..|> B": "Realization",
                    "A ..* B": "Composition with dotted line"
                },
                "cardinality": {
                    "A \"1\" --> \"*\" B": "One to many",
                    "A \"1\" --> \"1\" B": "One to one",
                    "A \"*\" --> \"*\" B": "Many to many",
                    "A \"1..1\" --> \"0..*\" B": "Range notation"
                },
                "annotations": {
                    "<<interface>>": "Interface stereotype",
                    "<<abstract>>": "Abstract class",
                    "<<enumeration>>": "Enumeration",
                    "<<service>>": "Service class"
                }
            }
        }
    
    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load best practices for each diagram type"""
        return {
            "general": [
                "Keep diagrams focused on a single purpose or process",
                "Use consistent naming conventions throughout",
                "Limit the number of elements per diagram (7±2 rule)",
                "Add descriptive titles and labels",
                "Use colors and styling purposefully, not decoratively",
                "Test your diagram with someone unfamiliar with the process",
                "Version control your diagrams alongside code",
                "Include a legend when using custom symbols or colors"
            ],
            "flowchart": [
                "Start with a clear beginning and end point",
                "Use diamond shapes for decision points",
                "Keep decision questions simple (yes/no when possible)",
                "Avoid crossing lines by reorganizing layout",
                "Group related steps in subgraphs",
                "Use consistent verb tenses (imperative: 'Submit', 'Validate')",
                "Show error paths and exception handling",
                "Consider the happy path vs edge cases balance"
            ],
            "sequence": [
                "Order participants logically (user to system, left to right)",
                "Use activation boxes to show when objects are active",
                "Keep messages concise but descriptive",
                "Show return values when they affect the flow",
                "Use notes to explain complex interactions",
                "Consider using references for complex sub-flows",
                "Show error scenarios and timeouts",
                "Group related interactions with fragments"
            ],
            "class": [
                "Show only relevant attributes and methods",
                "Use proper visibility modifiers (+, -, #, ~)",
                "Include return types and parameter types",
                "Show relationships with appropriate cardinality",
                "Use interfaces and abstract classes when applicable",
                "Group related classes visually",
                "Consider using packages for large systems",
                "Balance detail level with readability"
            ],
            "er": [
                "Use consistent naming for tables and columns",
                "Show primary keys (PK) and foreign keys (FK)",
                "Include important constraints and indexes",
                "Use meaningful relationship names",
                "Show cardinality clearly (1:1, 1:N, M:N)",
                "Group related entities visually",
                "Include lookup tables and junction tables",
                "Consider showing data types for key fields"
            ],
            "state": [
                "Define a clear initial state",
                "Show all possible transitions",
                "Use meaningful state names (verbs or adjectives)",
                "Include guard conditions when needed",
                "Show actions/effects on transitions",
                "Consider using nested states for complex behavior",
                "Define final states when applicable",
                "Document error states and recovery paths"
            ],
            "styling": [
                "Choose themes that match your presentation context",
                "Use hand-drawn style for brainstorming/informal docs",
                "Maintain contrast for accessibility",
                "Use transparent backgrounds for documents",
                "Consistent color coding within a diagram set",
                "Test diagrams in both light and dark modes",
                "Consider printing in grayscale",
                "Use semantic colors (red for errors, green for success)"
            ]
        }
    
    def get_examples_by_category(self, category: str) -> List[MermaidExample]:
        """Get all examples for a specific category"""
        return self.examples.get(category, [])
    
    def get_examples_by_complexity(self, complexity: str) -> List[MermaidExample]:
        """Get examples by complexity level"""
        examples = []
        for category_examples in self.examples.values():
            examples.extend([ex for ex in category_examples if ex.complexity == complexity])
        return examples
    
    def search_examples(self, query: str, categories: Optional[List[str]] = None) -> List[MermaidExample]:
        """Search examples by keywords"""
        results = []
        search_categories = categories or list(self.examples.keys())
        
        query_lower = query.lower()
        
        for category in search_categories:
            if category in self.examples:
                for example in self.examples[category]:
                    # Search in name, description, features, and use_cases
                    searchable_text = f"{example.name} {example.description} {' '.join(example.features)} {' '.join(example.use_cases)}".lower()
                    if query_lower in searchable_text:
                        results.append(example)
        
        return results
    
    def get_template(self, template_name: str, category: str = None) -> Optional[MermaidTemplate]:
        """Get a specific template"""
        search_categories = [category] if category else list(self.templates.keys())
        
        for cat in search_categories:
            if cat in self.templates:
                for template in self.templates[cat]:
                    if template.name.lower() == template_name.lower():
                        return template
        return None
    
    def fill_template(self, template: MermaidTemplate, variables: Dict[str, str]) -> str:
        """Fill a template with provided variables"""
        result = template.template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, var_value)
        return result
    
    def get_syntax_help(self, category: str, topic: str = None) -> Dict[str, Any]:
        """Get syntax help for a specific category and topic"""
        if category not in self.syntax_guide:
            return {}
        
        if topic:
            return self.syntax_guide[category].get(topic, {})
        return self.syntax_guide[category]
    
    def get_best_practices(self, category: str = None) -> List[str]:
        """Get best practices for a category or general practices"""
        if category and category in self.best_practices:
            return self.best_practices[category]
        return self.best_practices.get("general", [])
    
    def generate_quick_reference(self, category: str) -> str:
        """Generate a quick reference guide for a diagram type"""
        if category not in self.syntax_guide:
            return f"No reference available for {category}"
        
        ref = f"# {category.title()} Quick Reference\n\n"
        
        # Add syntax information
        syntax_info = self.syntax_guide[category]
        for section, content in syntax_info.items():
            ref += f"## {section.replace('_', ' ').title()}\n"
            if isinstance(content, dict):
                for key, value in content.items():
                    ref += f"- `{key}`: {value}\n"
            else:
                ref += f"{content}\n"
            ref += "\n"
        
        # Add best practices
        practices = self.get_best_practices(category)
        if practices:
            ref += "## Best Practices\n"
            for practice in practices:
                ref += f"- {practice}\n"
            ref += "\n"
        
        # Add examples
        examples = self.get_examples_by_category(category)
        if examples:
            ref += "## Examples\n"
            for example in examples[:2]:  # Show first 2 examples
                ref += f"### {example.name} ({example.complexity})\n"
                ref += f"{example.description}\n\n"
                ref += f"```mermaid\n{example.code}\n```\n\n"
        
        return ref