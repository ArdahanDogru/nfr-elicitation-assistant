"""
NFR Elicitation Assistant - Utility Functions
=============================================
Shared utility functions used across modules
"""

import re
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def format_entity_name(name: str) -> str:
    """
    Format entity names for display:
    - Remove 'Type' suffix
    - Add spaces to camelCase
    """
    # Remove Type suffix
    if name.endswith('Type'):
        name = name[:-4]
    
    # Add spaces to camelCase (TimePerformance -> Time Performance)
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    return result


def validate_requirement(text: str) -> bool:
    """
    Check if input looks like a requirement.
    Returns False for obvious non-sense.
    """
    text = text.strip()
    
    # Too short
    if len(text) < 10:
        return False
    
    # Check for requirement keywords
    req_keywords = [
        'shall', 'should', 'must', 'will', 'can', 'may',
        'system', 'user', 'data', 'application', 'software',
        'within', 'response', 'time', 'provide', 'allow',
        'enable', 'display', 'process', 'store', 'access'
    ]
    
    text_lower = text.lower()
    has_keyword = any(keyword in text_lower for keyword in req_keywords)
    
    # Check if it's mostly alphabetic (not random characters)
    alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
    
    return has_keyword or alpha_ratio > 0.7


def get_nfr_and_children(nfr_name: str):
    """Get NFR type and all its children for searching contributions"""
    from nfr_queries import getEntity, getChildren, getEntityName
    
    entity = getEntity(nfr_name)
    if not entity:
        return [nfr_name]
    
    result = [getEntityName(entity)]
    
    # Get children
    try:
        children = getChildren(entity)
        for child in children:
            result.append(getEntityName(child))
    except:
        pass
    
    return result


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def fuzzy_match_entity(user_input: str) -> tuple:
    """
    Fuzzy match user input to metamodel entities.
    Returns (matched_entity_name, suggestion_message) or (None, error_message)
    """
    try:
        from nfr_queries import getEntity, getEntityName
        import metamodel
        import inspect
        
        user_input = user_input.strip()
        if not user_input:
            return None, "Please enter an entity name"
        
        # First try exact match via getEntity (which has built-in fuzzy matching)
        entity = getEntity(user_input)
        if entity:
            entity_name = getEntityName(entity)
            # Check if the input was different from the matched name
            if user_input.lower() != entity_name.lower().replace('type', '').replace('softgoal', ''):
                formatted = format_entity_name(entity_name)
                return entity_name, f"💡 Matched '{user_input}' → {formatted}\n\n"
            return entity_name, ""
        
        # If getEntity failed, try manual fuzzy matching
        # Collect all entity names
        all_entities = []
        for name, obj in inspect.getmembers(metamodel):
            if inspect.isclass(obj) and not name.startswith('_'):
                all_entities.append(name)
        
        # Find closest matches
        user_lower = user_input.lower()
        matches = []
        for entity_name in all_entities:
            entity_lower = entity_name.lower()
            # Calculate distance
            dist = levenshtein_distance(user_lower, entity_lower)
            # Also check without common suffixes
            entity_clean = entity_lower.replace('type', '').replace('softgoal', '')
            dist_clean = levenshtein_distance(user_lower, entity_clean)
            min_dist = min(dist, dist_clean)
            
            # Accept if distance is reasonable (within 40% of input length)
            threshold = max(3, len(user_input) * 0.4)
            if min_dist <= threshold:
                matches.append((entity_name, min_dist))
        
        # Sort by distance, but prefer "Type" suffix over "Softgoal" suffix
        def sort_key(match):
            name, dist = match
            # Prefer Type > Softgoal > Others
            suffix_priority = 0
            if name.endswith('Type'):
                suffix_priority = 0  # Highest priority
            elif name.endswith('Softgoal'):
                suffix_priority = 1  # Lower priority
            else:
                suffix_priority = 2  # Lowest priority
            return (suffix_priority, dist)  # Sort by suffix first, then distance
        
        matches.sort(key=sort_key)
        
        if matches:
            best_match = matches[0][0]
            formatted = format_entity_name(best_match)
            # Show only Type versions in suggestions (filter out Softgoals)
            type_matches = [m for m in matches if m[0].endswith('Type')]
            if type_matches:
                suggestions = [format_entity_name(m[0]) for m in type_matches[:3]]
            else:
                suggestions = [format_entity_name(m[0]) for m in matches[:3]]
            suggestion_msg = f"💡 Did you mean: {', '.join(suggestions)}?\n\n"
            return best_match, suggestion_msg
        
        return None, f"âŒ Could not find entity: {user_input}\n\nTry: Performance, Security, Usability, Indexing, Encryption, etc."
        
    except Exception as e:
        return None, f"âŒ Error during matching: {str(e)}"