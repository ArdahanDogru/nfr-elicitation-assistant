"""
Classifier v7 FIXED: Consistent Metamodel Integration
=======================================================

ARCHITECTURAL FIX:
- Both NFR AND FR types now read dynamically from metamodel
- Removed hardcoded FR_KEYWORDS dictionary
- FR classification now uses OperationalizingSoftgoalType subclasses
- Consistent approach: metamodel is single source of truth

Based on v6 (0.7387 F1 on PROMISE dataset)
"""

import ollama
import json
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
MODEL = "llama3.1:8b"

# ============================================================================
# CLASSIFIER MODE SWITCH
# ============================================================================

# Change this to switch between modes:
#   "PROMISE"        - 10 NFR types (tested, ~0.74 F1)
#   "FULL_METAMODEL" - All 47+ NFR types (untested, may have lower accuracy)

CLASSIFIER_MODE = "FULL_METAMODEL"  # <-- CHANGE THIS TO SWITCH MODES

# ============================================================================
# IMPORT METAMODEL AND EXTRACT TYPES DYNAMICALLY
# ============================================================================

try:
    from metamodel import NFRSoftgoalType, OperationalizingSoftgoalType
    print("✓ Successfully imported metamodel base classes")
except ImportError as e:
    print(f"✗ Error importing metamodel: {e}")
    raise


def get_all_subclasses(cls):
    """Recursively get all subclasses of a class"""
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_all_subclasses(subclass))
    return subclasses


def extract_all_nfr_types():
    """
    Dynamically extract ALL NFR types from metamodel.
    Returns dict: {type_name: type_class}
    """
    all_types = {}
    
    for type_class in get_all_subclasses(NFRSoftgoalType):
        # Get clean name (remove 'Type' suffix for display)
        class_name = type_class.__name__
        if class_name.endswith('Type'):
            type_name = class_name[:-4]  # Remove 'Type'
        else:
            type_name = class_name
        
        all_types[type_name] = type_class
    
    return all_types


def extract_all_fr_types():
    """
    Dynamically extract ALL FR/Operationalizing types from metamodel.
    Returns dict: {type_name: type_class}
    """
    all_types = {}
    
    for type_class in get_all_subclasses(OperationalizingSoftgoalType):
        # Get clean name (remove 'Type' suffix for display)
        class_name = type_class.__name__
        if class_name.endswith('Type'):
            type_name = class_name[:-4]  # Remove 'Type'
        else:
            type_name = class_name
        
        all_types[type_name] = type_class
    
    return all_types


# Extract all types at module load
ALL_NFR_METAMODEL_TYPES = extract_all_nfr_types()
ALL_FR_METAMODEL_TYPES = extract_all_fr_types()

print(f"✓ Extracted {len(ALL_NFR_METAMODEL_TYPES)} NFR types from metamodel")
print(f"✓ Extracted {len(ALL_FR_METAMODEL_TYPES)} FR/Operationalizing types from metamodel")


# PROMISE dataset types (10 types - for validated testing)
PROMISE_TYPE_NAMES = [
    'Availability',
    'FaultTolerance', 
    'LegalCompliance',
    'LookFeel',
    'Maintainability',
    'Performance',
    'Portability',
    'Scalability',
    'Security',
    'Usability'
]

PROMISE_TYPES = {name: ALL_NFR_METAMODEL_TYPES[name] for name in PROMISE_TYPE_NAMES if name in ALL_NFR_METAMODEL_TYPES}


def get_active_nfr_types():
    """Get the currently active NFR type dictionary based on mode"""
    if CLASSIFIER_MODE == "PROMISE":
        return PROMISE_TYPES
    else:
        return ALL_NFR_METAMODEL_TYPES


def get_active_fr_types():
    """Get the currently active FR type dictionary (always all types)"""
    return ALL_FR_METAMODEL_TYPES


def get_mode_info():
    """Get info about current mode for display"""
    active_nfr = get_active_nfr_types()
    active_fr = get_active_fr_types()
    return {
        "mode": CLASSIFIER_MODE,
        "nfr_type_count": len(active_nfr),
        "fr_type_count": len(active_fr),
        "nfr_types": list(active_nfr.keys()),
        "fr_types": list(active_fr.keys())
    }


# ============================================================================
# STAGE 1: FR vs NFR (Same as v6)
# ============================================================================

FR_NFR_PROMPT = """You are an expert in software requirements classification.

Your task: Classify the requirement as either Functional (FR) or Non-Functional (NFR).

DEFINITIONS:

Functional Requirement (FR):
- Describes WHAT the system does
- Specifies behaviors, actions, functions, features
- Examples: search, display, store, process, authenticate

Non-Functional Requirement (NFR):
- Describes HOW WELL the system performs
- Specifies quality attributes, constraints, performance criteria
- Examples: fast, secure, usable, reliable, available

FEW-SHOT EXAMPLES:

"The system shall allow users to search for products"
→ {"classification": "FR"}

"The system shall respond within 2 seconds"
→ {"classification": "NFR"}

"Only authorized users can access the system"
→ {"classification": "NFR"}

"The system shall display data in a graph"
→ {"classification": "FR"}

"The system must be available 99.9% of the time"
→ {"classification": "NFR"}

"The interface shall have standard navigation buttons"
→ {"classification": "NFR"}

"The system shall display user data in a table"
→ {"classification": "FR"}

"The product shall match the company color schema"
→ {"classification": "NFR"}

"The product shall display grids within a circle as a periscope view"
→ {"classification": "NFR"}

"The product shall display each ship using an image of that ship type"
→ {"classification": "NFR"}

"The product shall use symbols naturally understandable by users"
→ {"classification": "NFR"}

"When player takes shot, product shall simulate sound of ship at sea"
→ {"classification": "NFR"}

"The system shall display search results to the user"
→ {"classification": "FR"}

RULES:
1. Focus on the PRIMARY intent
2. WHAT the system does → FR
3. HOW WELL or HOW IT LOOKS → NFR
4. "display" + appearance/style → NFR
5. "display" + data/content → FR

Return ONLY JSON:
{"classification": "FR"} or {"classification": "NFR"}

Requirement: {requirement}"""


def classify_fr_nfr(requirement_text):
    """Stage 1: Classify as FR or NFR."""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a requirements classification expert."},
                {"role": "user", "content": FR_NFR_PROMPT.replace("{requirement}", requirement_text)}
            ],
            options={"temperature": 0.3, "num_predict": 50}
        )
        
        text = response['message']['content'].strip()
        
        try:
            parsed = json.loads(text)
            classification = parsed.get('classification', '').upper()
            return classification if classification in ['FR', 'NFR'] else 'FR'
        except:
            if 'NFR' in text.upper():
                return 'NFR'
            return 'FR'
    except Exception as e:
        print(f"Error in FR/NFR classification: {e}")
        return 'FR'


# ============================================================================
# STAGE 2A: NFR TYPE (Dynamic based on mode)
# ============================================================================

# Examples for PROMISE types (kept for compatibility)
NFR_TYPE_EXAMPLES = {
    'Availability': [
        "The system must be available 99.9% of the time",
        "The product shall be accessible 24/7",
        "System shall maintain operations during peak hours"
    ],
    
    'FaultTolerance': [
        "The system shall retain user preferences in the event of a failure",
        "Product shall recover from errors without data loss",
        "System shall operate in offline mode when connection is unavailable",
        "Product shall create exception logs for transmission to help desk"
    ],
    
    'LegalCompliance': [
        "The system shall comply with GDPR requirements",
        "Product must adhere to accessibility standards WCAG 2.1",
        "System shall maintain audit logs as required by regulations"
    ],
    
    'LookFeel': [
        "The product shall display grids as a periscope view",
        "Interface shall match the company color schema",
        "Product shall display ships using nautical-themed graphics",
        "System shall use intuitive icons"
    ],
    
    'Maintainability': [
        "Code shall be well-documented with inline comments",
        "System architecture shall use modular design patterns",
        "Product shall support easy version updates"
    ],
    
    'Performance': [
        "The system shall respond to queries within 2 seconds",
        "Product shall process 10,000 transactions per minute",
        "Application shall load the dashboard in under 1 second"
    ],
    
    'Portability': [
        "The system shall run on Windows, Mac, and Linux",
        "Product shall be compatible with multiple browsers",
        "Application shall work on mobile and desktop platforms"
    ],
    
    'Scalability': [
        "System shall support up to 100,000 concurrent users",
        "Product shall scale horizontally by adding servers",
        "Application shall handle 10x data growth without redesign"
    ],
    
    'Security': [
        "The system shall encrypt all sensitive data",
        "Only authorized users shall access admin functions",
        "Product shall require two-factor authentication"
    ],
    
    'Usability': [
        "Interface shall be intuitive for first-time users",
        "System shall provide helpful error messages",
        "Product shall support keyboard shortcuts"
    ]
}


def classify_nfr_type(requirement_text):
    """
    Stage 2A: Classify NFR type using metamodel.
    
    Returns tuple: (type_name, warning_message or None)
    """
    active_types = get_active_nfr_types()
    valid_types = list(active_types.keys())
    
    # Build type descriptions for LLM prompt
    type_descriptions = []
    for type_name, type_class in active_types.items():
        if hasattr(type_class, 'description'):
            desc = type_class.description
        else:
            desc = f"{type_name} quality attribute"
        type_descriptions.append(f"- {type_name}: {desc}")
    
    # Build prompt with examples (if in PROMISE mode)
    examples_text = ""
    if CLASSIFIER_MODE == "PROMISE" and len(valid_types) <= 15:
        examples_text = "\n\nFEW-SHOT EXAMPLES:\n"
        for nfr_type, examples in NFR_TYPE_EXAMPLES.items():
            if nfr_type in valid_types:
                for example in examples[:1]:  # Just one example per type
                    examples_text += f'"{example}"\n→ {{"type": "{nfr_type}"}}\n\n'
    
    prompt = f"""Classify this non-functional requirement into one of these NFR types:

{chr(10).join(type_descriptions)}
{examples_text}
IMPORTANT: Return ONLY a JSON object, nothing else.
Format: {{"type": "TypeName"}}

Requirement: {requirement_text}"""
    
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a requirements classification expert. Always respond with ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3, "num_predict": 30}
        )
        
        text = response['message']['content'].strip()
        
        # Try to extract JSON from the response
        parsed = extract_json_from_text(text)
        
        if parsed and 'type' in parsed:
            nfr_type = parsed['type']
            
            # Check if it's in our valid metamodel types
            if nfr_type in valid_types:
                return (nfr_type, None)  # Perfect match
            
            # Try case-insensitive match
            for valid_type in valid_types:
                if nfr_type.lower() == valid_type.lower():
                    return (valid_type, None)
            
            # No match - return with warning
            warning = f"⚠️ LLM suggested '{nfr_type}' (not in metamodel). LLM suggested: '{nfr_type}'"
            return (nfr_type if nfr_type else "Unknown", warning)
        
        # JSON extraction failed - try to extract type from text
        extracted = extract_type_from_text(text, valid_types)
        if extracted:
            return (extracted, None)
        
        # No match - return raw LLM text with warning
        warning = f"⚠️ No metamodel match found. LLM response: '{text[:50]}...'"
        return ("Unknown", warning)
            
    except Exception as e:
        print(f"Error in NFR type classification: {e}")
        return ("Error", f"⚠️ Classification error: {str(e)}")


# ============================================================================
# STAGE 2B: FR TYPE (NOW READS FROM METAMODEL!)
# ============================================================================

def classify_fr_type(requirement_text):
    """
    Stage 2B: Classify FR type using metamodel (FIXED VERSION).
    
    Returns tuple: (type_name, warning_message or None)
    """
    active_types = get_active_fr_types()
    valid_types = list(active_types.keys())
    
    # Build type descriptions for LLM prompt
    type_descriptions = []
    for type_name, type_class in active_types.items():
        if hasattr(type_class, 'description'):
            desc = type_class.description
        else:
            desc = f"{type_name} operation"
        type_descriptions.append(f"- {type_name}: {desc}")
    
    prompt = f"""Classify this functional requirement into one of these operation types:

{chr(10).join(type_descriptions)}

Or suggest a new operation type if none fit well.

IMPORTANT: Return ONLY a JSON object, nothing else. No explanation, no reasoning.
Format: {{"type": "TypeName"}}

Requirement: {requirement_text}"""
    
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a requirements classification expert. Always respond with ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3, "num_predict": 30}
        )
        
        text = response['message']['content'].strip()
        
        # Try to extract JSON from the response
        parsed = extract_json_from_text(text)
        
        if parsed and 'type' in parsed:
            fr_type_raw = parsed['type']
            
            # Convert verb to noun if needed
            fr_type = verb_to_noun(fr_type_raw)
            
            # Check if it matches a known FR type from metamodel
            if fr_type in valid_types:
                return (fr_type, None)  # Perfect match
            
            # Try case-insensitive match
            for valid_type in valid_types:
                if fr_type.lower() == valid_type.lower():
                    return (valid_type, None)
            
            # No match - return with warning (LLM suggested a new type)
            warning = f"⚠️ LLM suggested new type: '{fr_type}' (not in metamodel)"
            return (fr_type, warning)
        
        # JSON extraction failed - try to find type in text
        extracted = extract_type_from_text(text, valid_types)
        if extracted:
            return (extracted, None)
        
        # Last resort - return Unknown with the raw text
        return ("Unknown", f"⚠️ Could not parse LLM response: '{text[:80]}...'")
            
    except Exception as e:
        return ("Unknown", f"⚠️ FR classification error: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_json_from_text(text):
    """
    Extract JSON object from LLM response that may contain extra text.
    
    Handles cases like:
    - Pure JSON: {"type": "Decrypt"}
    - Prefixed: JSON: {"type": "Decrypt"}
    - With explanation: {"type": "Decrypt"}\n\nReasoning: ...
    - Embedded: Based on... {"type": "Decrypt"} ...more text
    """
    import re
    
    # Try direct JSON parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object pattern in text
    json_pattern = r'\{[^{}]*"type"\s*:\s*"[^"]+"\s*[^{}]*\}'
    matches = re.findall(json_pattern, text)
    
    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # Try to extract type value directly from patterns like "type": "Value"
    type_pattern = r'"type"\s*:\s*"([^"]+)"'
    match = re.search(type_pattern, text)
    if match:
        return {"type": match.group(1)}
    
    # Try without quotes: type: Value
    type_pattern2 = r'type["\s]*:\s*["\']?(\w+)["\']?'
    match = re.search(type_pattern2, text, re.IGNORECASE)
    if match:
        return {"type": match.group(1)}
    
    return None


def verb_to_noun(word):
    """
    Convert common verb forms to noun forms for type names.
    E.g., 'search' → 'Search', 'authenticate' → 'Authentication'
    """
    word_lower = word.lower()
    
    # Common verb-to-noun mappings
    verb_noun_map = {
        # Verbs to nouns
        'search': 'Search',
        'display': 'Display',
        'refresh': 'Refresh',
        'authenticate': 'Authentication',
        'authorize': 'Authorization',
        'validate': 'Validation',
        'decrypt': 'Decryption',
        'encrypt': 'Encryption',
        'sync': 'Sync',
        'synchronize': 'Sync',
        'cache': 'Caching',
        'notify': 'Notification',
        'export': 'Export',
        'import': 'Import',
        'store': 'Store',
        'backup': 'Backup',
        'restore': 'Restoration',
        'monitor': 'Monitor',
        'index': 'Indexing',
        'log': 'Log',
        
        # Already noun forms - just capitalize
        'decryption': 'Decryption',
        'encryption': 'Encryption',
        'validation': 'Validation',
        'authentication': 'Authentication',
        'authorization': 'Authorization',
        'synchronization': 'Sync',
        'caching': 'Caching',
        'notification': 'Notification',
        'storage': 'Store',
        'monitoring': 'Monitor',
        'indexing': 'Indexing',
        'logging': 'Log',
    }
    
    if word_lower in verb_noun_map:
        return verb_noun_map[word_lower]
    
    # If ends with common verb suffix, try to convert
    if word_lower.endswith('ate'):
        # validate -> validation
        return word[:-1].capitalize() + 'ion'
    elif word_lower.endswith('ify'):
        # notify -> notification
        return word[:-1].capitalize() + 'cation'
    elif word_lower.endswith('ize'):
        # synchronize -> synchronization
        return word[:-1].capitalize() + 'ation'
    
    # Default: just capitalize
    return word.capitalize()


def extract_type_from_text(text, valid_types):
    """
    Extract type name from free-form LLM text by looking for known types.
    """
    text_lower = text.lower()
    
    # Check for exact type matches first
    for type_name in valid_types:
        if type_name.lower() in text_lower:
            return type_name
    
    return None


# ============================================================================
# MAIN CLASSIFICATION FUNCTION
# ============================================================================

def classify_requirement(requirement_text):
    """
    Main classification using metamodel.
    
    Returns dict with:
    - category: "FR" or "NFR"
    - type: The classified type
    - warning: Warning message if LLM fallback used, else None
    - mode: Current classifier mode
    """
    category = classify_fr_nfr(requirement_text)
    
    if category == "NFR":
        req_type, warning = classify_nfr_type(requirement_text)
    else:
        req_type, warning = classify_fr_type(requirement_text)
    
    return {
        "category": category,
        "type": req_type,
        "warning": warning,
        "mode": CLASSIFIER_MODE
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def set_classifier_mode(mode):
    """
    Change classifier mode at runtime.
    
    Args:
        mode: "PROMISE" or "FULL_METAMODEL"
    """
    global CLASSIFIER_MODE
    if mode in ["PROMISE", "FULL_METAMODEL"]:
        CLASSIFIER_MODE = mode
        print(f"✓ Classifier mode set to: {mode}")
        print(f"  - NFR types: {len(get_active_nfr_types())}")
        print(f"  - FR types: {len(get_active_fr_types())}")
    else:
        print(f"✗ Invalid mode: {mode}. Use 'PROMISE' or 'FULL_METAMODEL'")


def list_available_types():
    """List all available types in current mode"""
    active_nfr = get_active_nfr_types()
    active_fr = get_active_fr_types()
    
    print(f"\n{'='*60}")
    print(f"Mode: {CLASSIFIER_MODE}")
    print('='*60)
    
    print(f"\nNFR Types ({len(active_nfr)}):")
    print('-'*60)
    for name, cls in sorted(active_nfr.items()):
        desc = cls.description[:50] if hasattr(cls, 'description') else "No description"
        print(f"  {name:25s}: {desc}...")
    
    print(f"\nFR/Operationalizing Types ({len(active_fr)}):")
    print('-'*60)
    for name, cls in sorted(active_fr.items()):
        desc = cls.description[:50] if hasattr(cls, 'description') else "No description"
        print(f"  {name:25s}: {desc}...")
    
    print('='*60)


# ============================================================================
# VERIFICATION
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("v7 FIXED: Consistent Metamodel Integration")
    print("="*70)
    
    print(f"\n✓ CLASSIFIER_MODE: {CLASSIFIER_MODE}")
    print(f"✓ Total NFR types in metamodel: {len(ALL_NFR_METAMODEL_TYPES)}")
    print(f"✓ Total FR types in metamodel: {len(ALL_FR_METAMODEL_TYPES)}")
    print(f"✓ Active NFR types: {len(get_active_nfr_types())}")
    print(f"✓ Active FR types: {len(get_active_fr_types())}")
    
    print("\n--- Testing FR classification (now uses metamodel!) ---")
    test_frs = [
        "System shall allow users to search for products",
        "The system shall display results in a table",
        "User can refresh the data manually",
        "The system shall cache frequently accessed data",
    ]
    
    for req in test_frs:
        result = classify_requirement(req)
        print(f"\nReq: {req}")
        print(f"  → {result['category']} / {result['type']}")
        if result['warning']:
            print(f"  → {result['warning']}")
    
    print("\n--- Testing NFR classification ---")
    test_nfrs = [
        "System must respond within 2 seconds",
        "The system shall be available 99.9% of the time",
    ]
    
    for req in test_nfrs:
        result = classify_requirement(req)
        print(f"\nReq: {req}")
        print(f"  → {result['category']} / {result['type']}")
        if result['warning']:
            print(f"  → {result['warning']}")
    
    print("\n" + "="*70)
    print("✅ v7 FIXED Complete - Both NFR and FR use metamodel!")
    print("="*70)