from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import openai
from anthropic import Anthropic
from authlib.integrations.flask_client import OAuth
import json
import logging
import traceback
import time

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# OAuth setup
oauth = OAuth(app)

# Google OAuth for Anthropic passthrough
google_oauth = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Mermaid knowledge base
MERMAID_KNOWLEDGE = """
Mermaid is a diagramming and charting tool that uses text-based syntax. Here are the main diagram types and their syntax:

1. Flowchart:
```mermaid
graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]
```

2. Sequence Diagram:
```mermaid
sequenceDiagram
    Alice->>John: Hello John
    John-->>Alice: Hi Alice
```

3. Class Diagram:
```mermaid
classDiagram
    Animal <|-- Duck
    Animal : +int age
    Animal : +String gender
    Duck : +String beakColor
```

4. State Diagram:
```mermaid
stateDiagram-v2
    [*] --> Still
    Still --> Moving
    Moving --> Still
    Moving --> [*]
```

5. Entity Relationship Diagram:
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

6. Gantt Chart:
```mermaid
gantt
    title A Gantt Diagram
    dateFormat  YYYY-MM-DD
    section Section
    A task           :a1, 2024-01-01, 30d
    Another task     :after a1, 20d
```

7. Pie Chart:
```mermaid
pie title Pets adopted
    "Dogs" : 386
    "Cats" : 85
    "Rats" : 15
```

8. Git Graph:
```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    commit
    checkout main
    merge develop
```
"""

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/validate-key', methods=['POST'])
def validate_api_key():
    try:
        data = request.json
        api_key = data.get('api_key', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Validating API key for provider: {provider}")
        
        if not api_key:
            return jsonify({"valid": False, "error": "No API key provided"}), 400
        
        try:
            if provider == 'openai':
                # Test OpenAI API key
                client = openai.OpenAI(api_key=api_key)
                # Make a minimal API call to validate the key
                client.models.list(limit=1)
                logger.info("OpenAI API key is valid")
                return jsonify({"valid": True, "provider": "openai"})
                
            elif provider == 'anthropic':
                # Test Anthropic API key
                client = Anthropic(api_key=api_key)
                # Make a minimal API call to validate the key
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                logger.info("Anthropic API key is valid")
                return jsonify({"valid": True, "provider": "anthropic"})
                
            else:
                return jsonify({"valid": False, "error": "Invalid provider"}), 400
                
        except Exception as e:
            logger.warning(f"API key validation failed: {str(e)}")
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return jsonify({"valid": False, "error": "Invalid API key"})
            else:
                return jsonify({"valid": False, "error": f"Validation error: {str(e)}"})
                
    except Exception as e:
        logger.error(f"Unexpected error in validate_api_key: {str(e)}")
        return jsonify({"valid": False, "error": "Unexpected error during validation"}), 500

@app.route('/api/generate-mermaid', methods=['POST'])
def generate_mermaid():
    try:
        data = request.json
        logger.debug(f"Received request data: {data}")
        
        user_input = data.get('input', '')
        api_key = data.get('api_key', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Processing request - Provider: {provider}, Input length: {len(user_input)}, Has API key: {bool(api_key)}")
        
        if not user_input:
            logger.warning("No input provided")
            return jsonify({"error": "No input provided"}), 400
        
        if not api_key and provider not in session.get('authenticated_providers', []):
            logger.warning("No API key or OAuth authentication")
            return jsonify({"error": "API key required or OAuth authentication needed"}), 401
        
        try:
            if provider == 'openai':
                logger.info("Generating with OpenAI")
                response = generate_with_openai(user_input, api_key)
            elif provider == 'anthropic':
                logger.info("Generating with Anthropic")
                response = generate_with_anthropic(user_input, api_key)
            else:
                logger.error(f"Invalid provider: {provider}")
                return jsonify({"error": "Invalid provider"}), 400
            
            logger.info("Successfully generated Mermaid code")
            return jsonify({
                "mermaid_code": response,
                "success": True
            })
        except Exception as e:
            logger.error(f"Error generating Mermaid code: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in generate_mermaid: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def generate_with_openai(user_input, api_key):
    client = openai.OpenAI(api_key=api_key or session.get('openai_token'))
    
    prompt = f"""You are an expert in Mermaid diagram syntax. Based on the following user request, generate appropriate Mermaid diagram code.

User request: {user_input}

Mermaid Knowledge Base:
{MERMAID_KNOWLEDGE}

Please provide only the Mermaid code without any explanation or markdown code blocks."""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Mermaid diagram expert. Generate only valid Mermaid syntax."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def generate_with_anthropic(user_input, api_key):
    try:
        logger.debug(f"Creating Anthropic client with API key: {api_key[:10]}..." if api_key else "No API key")
        
        # Create client with only the api_key parameter
        client = Anthropic(api_key=api_key or session.get('anthropic_token'))
        
        logger.debug("Anthropic client created successfully")
        
        prompt = f"""You are an expert in Mermaid diagram syntax. Based on the following user request, generate appropriate Mermaid diagram code.

User request: {user_input}

Mermaid Knowledge Base:
{MERMAID_KNOWLEDGE}

Please provide only the Mermaid code without any explanation or markdown code blocks."""
        
        logger.debug(f"Sending request to Anthropic API with prompt length: {len(prompt)}")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        logger.debug("Received response from Anthropic API")
        
        result = response.content[0].text.strip()
        logger.debug(f"Generated Mermaid code length: {len(result)}")
        
        return result
    except Exception as e:
        logger.error(f"Error in generate_with_anthropic: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(traceback.format_exc())
        raise

@app.route('/api/auth/google/login')
def google_login():
    try:
        redirect_uri = url_for('google_callback', _external=True)
        # Add Anthropic-specific parameters for passthrough auth
        return google_oauth.authorize_redirect(
            redirect_uri,
            prompt='select_account',
            # Additional params for Anthropic integration
            state=json.dumps({
                'provider': 'anthropic',
                'timestamp': str(int(time.time()))
            })
        )
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        return jsonify({"error": f"OAuth not configured: {str(e)}"}), 500

@app.route('/api/auth/google/callback')
def google_callback():
    try:
        token = google_oauth.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            session['google_email'] = user_info.get('email')
            session['google_name'] = user_info.get('name')
            session['google_authenticated'] = True
            
            # Here you would typically check if this Google account
            # has an associated Anthropic account and handle the passthrough
            logger.info(f"Google auth successful for: {user_info.get('email')}")
            
            # For now, we'll mark as authenticated
            session['authenticated_providers'] = ['anthropic-google']
        
        # Redirect to frontend with success
        return redirect('http://localhost:3000/auth-success')
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return redirect('http://localhost:3000/auth-error')

@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        "authenticated_providers": session.get('authenticated_providers', [])
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)