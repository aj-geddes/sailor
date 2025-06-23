"""Guided prompts for Mermaid diagram creation"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DiagramPrompt:
    """Structured prompt for diagram creation"""
    name: str
    description: str
    questions: List[Dict[str, str]]
    examples: Optional[Dict[str, str]] = None


class PromptGenerator:
    """Generates guided prompts for different diagram types"""
    
    @staticmethod
    def get_flowchart_prompt(process_name: str, complexity: str = "medium") -> str:
        """Generate flowchart creation prompt"""
        return f"""Let's create a flowchart for "{process_name}". I'll guide you through the process:

1. **Starting Point**: What triggers or starts the {process_name}?
   Example: "User clicks submit button", "Customer places order", "System receives request"

2. **Main Steps**: List the main steps in order (3-7 steps for {complexity} complexity).
   Example: "Validate input → Process data → Save to database → Send notification"

3. **Decision Points**: Are there any decisions or conditions? (if/then scenarios)
   Example: "Is data valid? Yes → Continue, No → Show error"

4. **End Points**: How does the process complete? (Success/Failure/Multiple endings)
   Example: "Success: Show confirmation", "Failure: Display error message"

5. **Style Preferences**:
   - Theme: Default, Dark, Forest, or Neutral?
   - Look: Classic or Hand-drawn?
   - Direction: Top-to-bottom (TB), Left-to-right (LR)?

Please provide your answers, and I'll create a professional flowchart diagram."""
    
    @staticmethod
    def get_sequence_prompt(scenario: str, participants: str = "3") -> str:
        """Generate sequence diagram creation prompt"""
        return f"""Let's create a sequence diagram for "{scenario}". Here's what I need:

1. **Participants**: Who or what are the {participants} main actors?
   Example: "User, Frontend, Backend, Database" or "Customer, Sales System, Payment Gateway"

2. **Initial Action**: What starts the {scenario}?
   Example: "User submits login form", "Customer initiates payment"

3. **Message Flow**: Describe the sequence of messages/actions between participants.
   Format: "A → B: Action/Message"
   Example: 
   - User → Frontend: Submit form
   - Frontend → Backend: Validate credentials
   - Backend → Database: Query user
   - Database → Backend: Return user data

4. **Response Types**: Are there any async operations or return messages?
   Example: "Backend -->> Frontend: Return token (dashed line for response)"

5. **Special Elements**: Any loops, alternatives, or parallel processes?
   Example: "Loop: Retry 3 times", "Alt: If authenticated / else show error"

6. **Visual Style**:
   - Theme preference?
   - Background: Transparent or white?

Share these details and I'll create your sequence diagram."""
    
    @staticmethod
    def get_architecture_prompt(system_name: str, components: List[str]) -> str:
        """Generate architecture diagram creation prompt"""
        components_str = ', '.join(components) if components else 'your components'
        
        return f"""Let's design the architecture for "{system_name}". Please provide:

1. **Component Details** for each of: {components_str}
   - Type: (Service, Database, External API, User Interface, etc.)
   - Purpose: Brief description
   - Technology: (Optional - e.g., Python, PostgreSQL, React)

2. **Connections**: How do components communicate?
   Example: "Frontend → API Gateway → Microservices → Database"
   Include: Protocol (HTTP, gRPC, Message Queue, etc.)

3. **External Dependencies**: Any third-party services?
   Example: "Payment Gateway, Email Service, Cloud Storage"

4. **Architecture Pattern**: 
   - Monolithic, Microservices, Serverless, or Hybrid?
   - Any specific patterns? (MVC, Event-driven, etc.)

5. **Deployment Context**: 
   - Cloud provider? (AWS, Azure, GCP, On-premise)
   - Containerized? (Docker, Kubernetes)

6. **Diagram Preferences**:
   - Grouping: By layer, by domain, or by deployment?
   - Include icons/logos?
   - Style: Technical or presentation-friendly?

Provide these details for a comprehensive architecture diagram."""
    
    @staticmethod
    def get_data_viz_prompt(data_type: str, title: str) -> str:
        """Generate data visualization prompt"""
        if 'percentage' in data_type.lower() or 'pie' in data_type.lower():
            return f"""Creating a pie chart for "{title}". Please provide:

1. **Categories and Values**:
   Format: "Category: Value or Percentage"
   Example:
   - Desktop: 45%
   - Mobile: 35%
   - Tablet: 20%

2. **Color Preferences**: Any specific color scheme?

3. **Labels**: Show percentages, values, or both?

4. **Style**: Classic or hand-drawn look?"""
        
        elif 'timeline' in data_type.lower():
            return f"""Creating a timeline for "{title}". Please provide:

1. **Events with Dates**:
   Format: "YYYY-MM-DD: Event description"
   Example:
   - 2024-01: Project kickoff
   - 2024-03: Phase 1 complete
   - 2024-06: Launch

2. **Grouping**: Any categories or phases?

3. **Style**: Horizontal or vertical timeline?"""
        
        elif 'comparison' in data_type.lower() or 'bar' in data_type.lower():
            return f"""Creating a comparison chart for "{title}". Please provide:

1. **Data Points**:
   Format: "Label: Value"
   Example:
   - Q1 2024: 1.2M
   - Q2 2024: 1.5M
   - Q3 2024: 1.8M

2. **Units**: What are you measuring? (revenue, users, percentage, etc.)

3. **Comparison Type**: Side-by-side bars, stacked bars, or grouped?

4. **Visual Preferences**: Colors, labels, grid lines?"""
        
        else:
            return f"""For your {data_type} visualization "{title}", please provide:

1. **Data Points**: List your data with labels and values

2. **Comparison Type**: What are you comparing?

3. **Visual Preference**: Bar chart, line graph, or other?"""
    
    @staticmethod
    def get_gantt_prompt(project_name: str, duration: str) -> str:
        """Generate Gantt chart creation prompt"""
        return f"""Let's create a Gantt chart for "{project_name}" ({duration} duration):

1. **Project Phases**: List main phases or milestones
   Example: "Planning, Development, Testing, Deployment"

2. **Tasks per Phase**: Break down each phase into tasks
   Format: "Task name: Duration"
   Example:
   Planning:
   - Requirements gathering: 1 week
   - Design mockups: 2 weeks
   
3. **Dependencies**: Which tasks depend on others?
   Example: "Testing starts after Development"

4. **Resources**: Who's responsible? (Optional)
   Example: "Frontend: Team A, Backend: Team B"

5. **Critical Path**: Which tasks are critical for timeline?

6. **Visual Preferences**:
   - Show weekends?
   - Highlight critical tasks?
   - Color scheme?

Provide these details for your project timeline."""
    
    @staticmethod
    def get_state_diagram_prompt(system_name: str) -> str:
        """Generate state diagram creation prompt"""
        return f"""Let's create a state diagram for "{system_name}". Please provide:

1. **Initial State**: What's the starting state?
   Example: "Idle", "Disconnected", "New"

2. **States**: List all possible states
   Example: "Idle, Processing, Complete, Error, Cancelled"

3. **Transitions**: What triggers state changes?
   Format: "From State → To State: Trigger/Event"
   Example:
   - Idle → Processing: Start button clicked
   - Processing → Complete: Task finished
   - Processing → Error: Exception occurred

4. **Final States**: Which states are terminal? (if any)
   Example: "Complete", "Cancelled"

5. **Special Behaviors**:
   - Any parallel states?
   - Nested states?
   - History states?

6. **Visual Preferences**:
   - Include state actions? (entry/exit)
   - Show transition guards?
   - Style preferences?

Describe your state machine for a complete diagram."""
    
    @staticmethod
    def get_er_diagram_prompt(domain: str) -> str:
        """Generate ER diagram creation prompt"""
        return f"""Let's create an Entity-Relationship diagram for "{domain}". Please provide:

1. **Entities**: List the main entities/tables
   Example: "Customer, Order, Product, Invoice"

2. **Attributes**: For each entity, list key attributes
   Format: "Entity: attribute1 (type), attribute2 (type)"
   Example:
   Customer: id (PK), name (string), email (string)
   Order: id (PK), customer_id (FK), date (datetime)

3. **Relationships**: How are entities related?
   Format: "Entity1 [relationship] Entity2"
   Example:
   - Customer [1 to many] Order
   - Order [many to many] Product
   - Order [1 to 1] Invoice

4. **Cardinality**: Specify relationship details
   - One-to-One (1:1)
   - One-to-Many (1:N)
   - Many-to-Many (M:N)

5. **Business Rules**: Any special constraints?
   Example: "Each order must have at least one product"

6. **Visual Preferences**:
   - Show all attributes or just keys?
   - Include data types?
   - Color coding for entity types?

Provide these details for your database design."""
    
    @staticmethod
    def get_class_diagram_prompt(system_name: str) -> str:
        """Generate class diagram creation prompt"""
        return f"""Let's create a class diagram for "{system_name}". Please provide:

1. **Classes**: List the main classes
   Example: "User, Account, Transaction, PaymentMethod"

2. **Class Details**: For each class, provide:
   - Attributes: name: type
   - Methods: methodName(params): returnType
   Example:
   User:
   - Attributes: id: int, name: string, email: string
   - Methods: login(password): boolean, logout(): void

3. **Relationships**:
   - Inheritance: "Child extends Parent"
   - Composition: "Whole contains Part"
   - Association: "ClassA uses ClassB"
   Example:
   - AdminUser extends User
   - Account contains Transaction
   - User has PaymentMethod

4. **Visibility**: Specify access modifiers
   - + public
   - - private
   - # protected
   - ~ package

5. **Interfaces/Abstract Classes**: Any?
   Example: "IPaymentProcessor interface", "AbstractUser abstract class"

6. **Design Patterns**: Using any patterns?
   Example: "Factory, Observer, Singleton"

Share your object-oriented design details."""
    
    @staticmethod
    def get_mindmap_prompt(topic: str) -> str:
        """Generate mindmap creation prompt"""
        return f"""Let's create a mindmap for "{topic}". Please provide:

1. **Central Theme**: Confirm or refine the main topic
   Example: "{topic}" or a more specific version

2. **Main Branches**: 3-6 primary categories/themes
   Example: "Features, Benefits, Challenges, Applications"

3. **Sub-branches**: For each main branch, provide 2-4 sub-topics
   Example:
   Features:
   - Speed
   - Security
   - Scalability

4. **Depth**: How many levels deep? (2-4 recommended)

5. **Special Elements**:
   - Any icons or emojis to include?
   - Cross-connections between branches?
   - Priority or importance indicators?

6. **Style Preferences**:
   - Colorful or monochrome?
   - Classic or hand-drawn?
   - Compact or spacious layout?

Outline your ideas for a comprehensive mindmap."""
    
    @staticmethod
    def parse_user_response(prompt_type: str, user_input: str) -> Dict[str, any]:
        """
        Parse user responses to extract structured data
        
        Args:
            prompt_type: Type of diagram prompt
            user_input: User's response text
            
        Returns:
            Structured data extracted from response
        """
        # This is a simplified parser - in production, use NLP or structured forms
        data = {
            'raw_input': user_input,
            'prompt_type': prompt_type
        }
        
        # Extract common patterns
        lines = user_input.strip().split('\n')
        
        # Look for numbered responses
        numbered_responses = {}
        current_number = None
        current_content = []
        
        for line in lines:
            # Check if line starts with a number
            if line.strip() and line.strip()[0].isdigit() and '.' in line:
                if current_number:
                    numbered_responses[current_number] = '\n'.join(current_content)
                current_number = line.split('.')[0].strip()
                current_content = [line.split('.', 1)[1].strip() if '.' in line else '']
            elif current_number:
                current_content.append(line.strip())
        
        if current_number:
            numbered_responses[current_number] = '\n'.join(current_content)
        
        data['numbered_responses'] = numbered_responses
        
        # Extract style preferences
        style_keywords = {
            'theme': ['default', 'dark', 'forest', 'neutral'],
            'look': ['classic', 'hand-drawn', 'handdrawn', 'hand drawn'],
            'background': ['transparent', 'white']
        }
        
        lower_input = user_input.lower()
        for style_type, keywords in style_keywords.items():
            for keyword in keywords:
                if keyword in lower_input:
                    data[style_type] = keyword
                    break
        
        # Handle direction separately with more specific patterns
        direction_patterns = [
            ('top to bottom', 'top'),
            ('bottom to top', 'bottom'),
            ('left to right', 'left'),
            ('right to left', 'right'),
            ('tb direction', 'tb'),
            ('bt direction', 'bt'),
            ('lr layout', 'lr'),
            ('rl layout', 'rl'),
            ('tb', 'tb'),
            ('bt', 'bt'),
            ('lr', 'lr'),
            ('rl', 'rl'),
            ('top', 'top'),
            ('bottom', 'bottom'),
            ('left', 'left'),
            ('right', 'right')
        ]
        
        for pattern, direction in direction_patterns:
            if pattern in lower_input:
                data['direction'] = direction
                break
        
        return data