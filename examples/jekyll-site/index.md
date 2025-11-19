---
layout: home
title: Sailor Jekyll Example
---

# Welcome to Sailor Documentation Example

This site demonstrates how to integrate Sailor with Jekyll for automatic Mermaid diagram generation.

## System Architecture

Our example system uses a microservices architecture:

```mermaid
flowchart TB
    subgraph "Frontend Layer"
        Web[Web Application]
        Mobile[Mobile App]
        Admin[Admin Dashboard]
    end
    
    subgraph "API Gateway"
        Gateway[Kong API Gateway]
        RateLimit[Rate Limiter]
        Auth[Authentication]
    end
    
    subgraph "Microservices"
        UserSvc[User Service]
        OrderSvc[Order Service]
        PaymentSvc[Payment Service]
        NotificationSvc[Notification Service]
    end
    
    subgraph "Data Layer"
        UserDB[(User Database)]
        OrderDB[(Order Database)]
        Cache[(Redis Cache)]
        Queue[Message Queue]
    end
    
    Web --> Gateway
    Mobile --> Gateway
    Admin --> Gateway
    
    Gateway --> RateLimit
    RateLimit --> Auth
    Auth --> UserSvc
    Auth --> OrderSvc
    Auth --> PaymentSvc
    
    UserSvc --> UserDB
    UserSvc --> Cache
    OrderSvc --> OrderDB
    OrderSvc --> Queue
    PaymentSvc --> Queue
    Queue --> NotificationSvc
    
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef gateway fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    
    class Web,Mobile,Admin frontend
    class Gateway,RateLimit,Auth gateway
    class UserSvc,OrderSvc,PaymentSvc,NotificationSvc service
    class UserDB,OrderDB,Cache,Queue data
```

## Authentication Flow

Here's how authentication works in our system:

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant Gateway
    participant AuthService
    participant UserDB
    participant Cache
    
    User->>WebApp: Enter credentials
    WebApp->>Gateway: POST /auth/login
    Gateway->>AuthService: Validate credentials
    AuthService->>UserDB: Query user
    UserDB-->>AuthService: User data
    AuthService->>AuthService: Validate password
    AuthService->>Cache: Store session
    AuthService-->>Gateway: JWT token
    Gateway-->>WebApp: Auth response
    WebApp->>WebApp: Store token
    WebApp-->>User: Login success
    
    Note over User,WebApp: Subsequent requests
    User->>WebApp: Access protected resource
    WebApp->>Gateway: Request + JWT
    Gateway->>Cache: Validate token
    Cache-->>Gateway: Token valid
    Gateway->>AuthService: Get user context
    AuthService-->>Gateway: User data
    Gateway-->>WebApp: Protected resource
```

## Database Schema

Our user service database schema:

```mermaid
erDiagram
    User ||--o{ Order : places
    User ||--o{ Address : has
    User ||--o{ PaymentMethod : has
    User {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }
    
    Order ||--|{ OrderItem : contains
    Order ||--|| Payment : has
    Order {
        uuid id PK
        uuid user_id FK
        string status
        decimal total_amount
        timestamp created_at
        timestamp updated_at
    }
    
    OrderItem {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        integer quantity
        decimal unit_price
        decimal total_price
    }
    
    Address {
        uuid id PK
        uuid user_id FK
        string type
        string street
        string city
        string state
        string zip_code
        string country
        boolean is_default
    }
    
    PaymentMethod {
        uuid id PK
        uuid user_id FK
        string type
        string last_four
        string token
        boolean is_default
    }
    
    Payment {
        uuid id PK
        uuid order_id FK
        uuid payment_method_id FK
        string status
        decimal amount
        string transaction_id
        timestamp processed_at
    }
```

## State Machine Example

Order processing state machine:

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Validated: validate
    Validated --> PaymentPending: process payment
    Validated --> Cancelled: cancel
    
    PaymentPending --> PaymentFailed: payment fails
    PaymentPending --> Paid: payment success
    
    PaymentFailed --> PaymentPending: retry
    PaymentFailed --> Cancelled: max retries
    
    Paid --> Processing: start fulfillment
    Processing --> Shipped: ship order
    Processing --> Cancelled: cancel
    
    Shipped --> Delivered: confirm delivery
    Shipped --> Lost: report lost
    
    Delivered --> [*]
    Cancelled --> [*]
    Lost --> [*]
    
    note right of PaymentPending
        Payment gateway
        processes transaction
    end note
    
    note left of Processing
        Warehouse picks
        and packs order
    end note
```

## Generated Diagrams

After processing with Sailor, these diagrams are converted to images and available at:

- [System Architecture](./diagrams/index_diagram_1.png)
- [Authentication Flow](./diagrams/index_diagram_2.png)
- [Database Schema](./diagrams/index_diagram_3.png)
- [State Machine](./diagrams/index_diagram_4.png)

## Learn More

- [Sailor Documentation](https://github.com/aj-geddes/sailor)
- [Mermaid Documentation](https://mermaid.js.org)
- [Jekyll Documentation](https://jekyllrb.com)