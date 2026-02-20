"""
NFR Assistant - MenuLLM Module
===============================
Lightweight LLM wrapper for menu-driven interactions
"""

import ollama
import json

# Import from same directory (flat structure)
from prompt_templates import MENU_PROMPTS
from system_prompt import MENU_LLM_SYSTEM_PROMPT


class MenuLLM:
    """
    Lightweight LLM wrapper for enhancing menu responses.
    Receives metamodel output → Returns natural language explanation.
    
    Key differences from NFRFrameworkAgent:
    - Single-turn responses (no multi-turn conversation)
    - No tool use (pure response generation)
    - Focused on presentation/explanation of metamodel data
    """
    
    # Token limits per action type (optimized for each use case)
    TOKEN_LIMITS = {
        # SHORT responses (150-200 tokens)
        "show_examples": 200,              # Browse Examples details - brief
        "browse_entity": 350,              # Browse Examples with multiple decompositions
        
        # MEDIUM responses (250-300 tokens)  
        "define_entity": 280,              # What is this? - moderate detail
        "define_nfr": 280,                 # What is NFR/FR? - moderate detail
        "explain_classification": 280,     # Classification explanation
        "explain_specific_classification": 280,  # Specific type classification
        "analyze_contributions": 700,      # Side effects analysis (increased)
        
        # LONG responses (350-400 tokens)
        "verify": 500,                     # Statement verification - detailed analysis
        "decompose": 600,                  # Decomposition - multiple children
        "show_sources": 400,               # Justifications - academic detail
        "show_operationalizations": 400,   # Operationalizations - multiple techniques
        "show_claims": 400,                # Argumentation - detailed claims
        "list_all_types": 350,             # List all types - comprehensive
        "list_claims": 350,                # List claims - detailed
        
        # Default fallback
        "default": 250,
    }
    
    def __init__(self, model_name="llama3.1:8b"):
        """
        Initialize MenuLLM.
        
        Args:
            model_name: Ollama model to use for responses
                       Default: llama3.1:8b (your current model)
                       For faster: "llama3.2:3b" (install with: ollama pull llama3.2:3b)
        """
        self.model = model_name
        self.system_prompt = MENU_LLM_SYSTEM_PROMPT
    
    def respond(self, action_type, user_input, metamodel_context):
        """
        Main method: Takes metamodel output, returns LLM-enhanced response.
        
        Args:
            action_type: str - "define_nfr", "decompose", "list_softgoals", etc.
            user_input: str - what user entered (e.g., "Performance")
            metamodel_context: dict or str - the raw metamodel output
        
        Returns:
            str - Natural language response from LLM
        """
        try:
            # DEBUG: Print inputs
            print()
            print("="*70)
            print("MenuLLM.respond() DEBUG")
            print("="*70)
            print("Action Type:", action_type)
            print("User Input:", user_input)
            print()
            print("Metamodel Context:")
            print("-"*70)
            print(metamodel_context)
            print("-"*70)
            
            # Build prompt
            prompt = self._build_prompt(action_type, user_input, metamodel_context)
            
            print()
            print("Prompt Template Name:", action_type)
            print("Full Prompt being sent to LLM:")
            print("-"*70)
            print(prompt)
            print("-"*70)
            
            # Call LLM with action-specific token limit
            response = self._call_llm(prompt, action_type)
            
            print()
            print("LLM Response:")
            print("-"*70)
            print(response)
            print("="*70)
            
            return response
            
        except Exception as e:
            # Fallback to raw metamodel context on error
            return f"⚠️ Error generating LLM response: {str(e)}\n\n---\n\nRaw metamodel data:\n{metamodel_context}"
    
    def _build_prompt(self, action_type, user_input, context):
        """Build prompt using template"""
        # Get appropriate template
        template = MENU_PROMPTS.get(action_type, MENU_PROMPTS["default"])
        
        # Convert context to string if needed
        if isinstance(context, dict):
            context_str = json.dumps(context, indent=2)
        else:
            context_str = str(context)
        
        # Format template with user input and context
        try:
            formatted_prompt = template.format(
                user_input=user_input,
                context=context_str
            )
        except KeyError as e:
            # Fallback if template expects other variables
            formatted_prompt = f"User query: {user_input}\n\nMetamodel context:\n{context_str}\n\nProvide a helpful response."
        
        return formatted_prompt
    
    def _call_llm(self, prompt, action_type="default"):
        """
        Simple Ollama call - optimized for speed with dynamic token limits.
        
        Args:
            prompt: The formatted prompt string
            action_type: The type of action (determines token limit)
            
        Returns:
            str - LLM response text
        """
        try:
            # Get token limit for this action type
            num_predict = self.TOKEN_LIMITS.get(action_type, self.TOKEN_LIMITS["default"])
            
            # Try ollama.chat() first (newer API)
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    options={
                        "temperature": 0.3,      # Lower = faster, more deterministic
                        "top_p": 0.8,            # Slightly lower for speed
                        "num_predict": num_predict,  # Dynamic based on action type!
                        "num_ctx": 2048,         # Limit context window for speed
                    }
                )
                return response['message']['content']
            except AttributeError:
                # Fallback to ollama.generate() for older API versions
                full_prompt = f"System: {self.system_prompt}\n\nUser: {prompt}"
                response = ollama.generate(
                    model=self.model,
                    prompt=full_prompt,
                    options={
                        "temperature": 0.3,
                        "top_p": 0.8,
                        "num_predict": num_predict,
                        "num_ctx": 2048,
                    }
                )
                return response['response']
            
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")


# Convenience function for quick testing
def test_menu_llm():
    """Test MenuLLM with sample data"""
    llm = MenuLLM()
    
    test_context = {
        "name": "PerformanceType",
        "description": "The degree to which a system accomplishes its designated functions within given constraints regarding processing time and throughput rate.",
        "parent": "Quality",
        "children": ["TimePerformance", "ResourceUtilization"]
    }
    
    response = llm.respond(
        action_type="define_nfr",
        user_input="Performance",
        metamodel_context=test_context
    )
    
    print("=" * 60)
    print("TEST: What is Performance?")
    print("=" * 60)
    print(response)
    print("=" * 60)


if __name__ == "__main__":
    test_menu_llm()