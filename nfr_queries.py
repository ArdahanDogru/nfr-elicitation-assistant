"""
Query API for 3-Level NFR Framework Metamodel
=============================================

Provides functions to query the 3-level metamodel:
- Level 1: Metaclasses (ontology)
- Level 2: Classes (model)
- Level 3: Ground instances (tokens)
"""

import inspect
from utils import format_entity_name
from typing import List, Dict, Any, Optional, Union
import metamodel


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_level(entity) -> int:
    """
    Determine which level an entity belongs to.
    Returns: 1 (metaclass), 2 (class), or 3 (instance)
    """
    if inspect.isclass(entity):
        # Check if it's a metaclass (its bases include 'type')
        if issubclass(type(entity), type) and entity != type:
            # It's a class, so check if it's a metaclass
            if any(isinstance(base, type) and base.__name__.endswith('MetaClass') 
                   for base in entity.__mro__):
                return 2  # It's a regular class
            # Check if the class name suggests it's a metaclass
            if entity.__name__.endswith('MetaClass'):
                return 1  # It's a metaclass
            else:
                return 2  # It's a regular class
        return 2  # It's a class
    else:
        return 3  # It's an instance


def get_metaclass_attributes(cls) -> List[str]:
    """
    Get attributes defined by the metaclass of a class.
    These are the attributes from Level 1 that apply to Level 2 classes.
    """
    if hasattr(cls, '_metaclass_attributes'):
        return list(cls._metaclass_attributes)
    return []


# ============================================================================
# ENTITY RESOLUTION
# ============================================================================

def getEntity(name: str):
    """
    Get entity by name from any level with intelligent fuzzy matching.
    Returns metaclass, class, or instance as appropriate.
    
    Handles variations like:
    - "Performance" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ tries PerformanceType, PerformanceSoftgoal
    - "Security" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ tries SecurityType, SecuritySoftgoal
    - "Indexing" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ tries IndexingType, IndexingSoftgoal
    
    Examples:
        >>> getEntity("softgoal")
        <class 'Softgoal'>
        
        >>> getEntity("performance")  # matches PerformanceType
        <class 'PerformanceType'>
        
        >>> getEntity("PerformanceType")  # exact match
        <class 'PerformanceType'>
    """
    name_lower = name.lower().strip()
    
    # Term mappings for common queries
    term_map = {
        # Base types
        'proposition': 'Proposition',
        'softgoal': 'Softgoal',
        'nfr softgoal': 'NFRSoftgoal',
        'nfrsoftgoal': 'NFRSoftgoal',
        'operationalizing softgoal': 'OperationalizingSoftgoal',
        'operationalizingsoftgoal': 'OperationalizingSoftgoal',
        'claim softgoal': 'ClaimSoftgoal',
        'claimsoftgoal': 'ClaimSoftgoal',
        'softgoal type': 'SoftgoalType',
        'softgoaltype': 'SoftgoalType',
        
        # Common terminology variations
        'functional requirement': 'OperationalizingSoftgoal',
        'functional requirements': 'OperationalizingSoftgoal',
        'non-functional requirement': 'NFRSoftgoal',
        'non-functional requirements': 'NFRSoftgoal',
        'nonfunctional requirement': 'NFRSoftgoal',
        'nonfunctional requirements': 'NFRSoftgoal',
        'nfr': 'NFRSoftgoal',
        'nfrs': 'NFRSoftgoal',
        'quality attribute': 'NFRSoftgoal',
        'quality attributes': 'NFRSoftgoal',
        'solution': 'OperationalizingSoftgoal',
        'solutions': 'OperationalizingSoftgoal',
        'technique': 'OperationalizingSoftgoal',
        'techniques': 'OperationalizingSoftgoal',
        'implementation': 'OperationalizingSoftgoal',
        'implementations': 'OperationalizingSoftgoal',
    }
    
    # Check mappings first
    if name_lower in term_map:
        name_lower = term_map[name_lower].lower()
    
    # Try exact match first
    for member_name, obj in inspect.getmembers(metamodel):
        if member_name.lower() == name_lower:
            if not inspect.isfunction(obj) and not inspect.ismodule(obj):
                return obj
    
    # If no exact match, try fuzzy matching with Type/Softgoal suffixes
    # This handles queries like "Performance" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "PerformanceType"
    fuzzy_variants = [
        name_lower + 'type',           # "performance" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "performancetype"
        name_lower + 'softgoal',       # "performance" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "performancesoftgoal"
        name_lower.replace(' ', ''),   # "time performance" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "timeperformance"
    ]
    
    for variant in fuzzy_variants:
        for member_name, obj in inspect.getmembers(metamodel):
            if member_name.lower() == variant:
                if not inspect.isfunction(obj) and not inspect.ismodule(obj):
                    return obj
    
    # Still not found? Try partial/prefix matching
    # This handles queries like "Softgoa" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "Softgoal", "Performanc" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "PerformanceType"
    # Find all entities that start with the search term (minimum 3 characters)
    if len(name_lower) >= 3:
        matches = []
        for member_name, obj in inspect.getmembers(metamodel):
            if not inspect.isfunction(obj) and not inspect.ismodule(obj):
                # Check if member starts with the search term
                if member_name.lower().startswith(name_lower):
                    matches.append((member_name, obj))
        
        # If we found exactly one match, return it
        if len(matches) == 1:
            return matches[0][1]
        
        # If multiple matches, prefer Type suffix over Softgoal
        if len(matches) > 1:
            # Prioritize: Type > Softgoal > other
            for suffix_priority in ['type', 'softgoal', '']:
                for member_name, obj in matches:
                    if member_name.lower().endswith(suffix_priority):
                        return obj
            # If no priority match, return first
            return matches[0][1]
    
    # Still not found? Return None
    return None


def getEntityName(entity) -> str:
    """
    Get the name of an entity (works for classes and instances).
    
    For classes: Returns entity.__name__
    For instances: Searches metamodel module to find variable name
    
    Examples:
        >>> getEntityName(Performance)
        'Performance'
        
        >>> getEntityName(Indexing)  # instance
        'Indexing'
    """
    # If it's a class, use __name__
    if inspect.isclass(entity):
        return entity.__name__
    
    # If it's a string already, return it
    if isinstance(entity, str):
        return entity
    
    # For instances, search metamodel module to find variable name
    for member_name, obj in inspect.getmembers(metamodel):
        if obj is entity:
            return member_name
    
    # Fallback: return class name (not ideal but better than crashing)
    return type(entity).__name__


# ============================================================================
# ATTRIBUTE QUERIES
# ============================================================================

def getAttributes(entity) -> List[str]:
    """
    Get all attributes of an entity, including inherited ones.
    
    For Level 2 classes: Gets attributes from metaclass + class level
    For Level 3 instances: Gets attributes from their class
    
    Examples:
        >>> getAttributes(Softgoal)
        ['priority', 'type', 'topic', 'label', 'assumption']
        
        >>> getAttributes(Performance)
        []  # SoftgoalType doesn't have aggregateOf attributes
        
        >>> getAttributes(Indexing)
        ['priority', 'type', 'topic', 'label', 'assumption']
    """
    attributes = set()
    
    # Determine if entity is a class or instance
    if inspect.isclass(entity):
        cls = entity
    else:
        cls = type(entity)
    
    # Special case: ClaimSoftgoal explicitly ONLY has type and topic
    # Don't walk up the MRO to inherit attributes
    if cls.__name__ == 'ClaimSoftgoal' or (hasattr(cls, '__mro__') and 
        any(parent.__name__ == 'ClaimSoftgoal' for parent in cls.__mro__[:-1])):
        # Only use ClaimSoftgoal's own _metaclass_attributes
        if hasattr(cls, '_metaclass_attributes'):
            return sorted(list(cls._metaclass_attributes))
        return []
    
    # Walk up the class hierarchy to collect all attributes
    for parent_cls in cls.__mro__:
        if parent_cls == object:
            continue
            
        # Get attributes from metaclass (Level 1)
        metaclass_attrs = get_metaclass_attributes(parent_cls)
        attributes.update(metaclass_attrs)
        
        # Get attributes from __init__
        if hasattr(parent_cls, '__init__'):
            try:
                init_source = inspect.getsource(parent_cls.__init__)
                # Find self.attribute assignments
                import re
                class_attrs = re.findall(r'self\.(\w+)\s*[:=]', init_source)
                attributes.update(class_attrs)
            except:
                pass
    
    # Return as sorted list
    return sorted(list(attributes))


# ============================================================================
# HIERARCHY QUERIES
# ============================================================================

def getChildren(cls) -> List:
    """
    Get direct subclasses of a class.
    
    Examples:
        >>> getChildren(Softgoal)
        [<class 'NFRSoftgoal'>, <class 'OperationalizingSoftgoal'>, <class 'ClaimSoftgoal'>]
        
        >>> getChildren(SoftgoalType)
        [<class 'Performance'>, <class 'Security'>, ...]
    """
    if inspect.isclass(cls):
        return cls.__subclasses__()
    return []


def getParent(cls):
    """
    Get parent class.
    
    Examples:
        >>> getParent(NFRSoftgoal)
        <class 'Softgoal'>
        
        >>> getParent(Performance)
        <class 'SoftgoalType'>
    """
    if inspect.isclass(cls):
        bases = cls.__bases__
        # Filter out 'object' and metaclasses
        parents = [b for b in bases if b != object and not b.__name__.endswith('MetaClass')]
        if parents:
            return parents[0]
    return None


def getMetaclass(cls):
    """
    Get the metaclass of a class.
    
    Examples:
        >>> getMetaclass(Softgoal)
        <class 'SoftgoalMetaClass'>
        
        >>> getMetaclass(Performance)
        <class 'SoftgoalTypeMetaClass'>
    """
    if inspect.isclass(cls):
        return type(cls)
    return None


def isNFR(entity) -> bool:
    """
    Check if an entity is a non-functional requirement or NFR-related type.
    
    Returns True if:
    - Entity is NFRSoftgoal class or its subclass
    - Entity is an NFRType (NFR quality attribute) or its subclass
    
    Returns False if:
    - Entity is an OperationalizingType (technique type) or its subclass
    
    Examples:
        >>> isNFR(Performance)
        True  # It's an NFRType (quality attribute)
        
        >>> isNFR(Indexing)
        False  # It's an OperationalizingType (technique), not an NFR
        
        >>> isNFR(NFRSoftgoal)
        True  # It's the NFRSoftgoal class
    """
    if inspect.isclass(entity):
        cls = entity
    else:
        cls = type(entity)
    
    # Check if it's NFRSoftgoal or its subclass
    try:
        if issubclass(cls, metamodel.NFRSoftgoal):
            return True
    except (TypeError, AttributeError):
        pass
    
    # Check if it's an NFRType (quality attribute, not technique)
    # Note: We check NFRType specifically, not SoftgoalType,
    # because OperationalizingType also inherits from SoftgoalType
    try:
        if issubclass(cls, metamodel.NFRType):
            return True
    except (TypeError, AttributeError):
        pass
    
    return False


# ============================================================================
# CONTRIBUTION QUERIES
# ============================================================================

def getContributions(source_name: str) -> List[Dict]:
    """
    Get all contributions from a source.
    Finds all Contribution instances in the metamodel.
    
    Examples:
        >>> getContributions("Indexing")
        [{'target': 'Performance', 'type': 'HELP'}, ...]
    """
    contributions = []
    
    # Find all Contribution instances in metamodel
    for name, obj in inspect.getmembers(metamodel):
        if isinstance(obj, metamodel.Contribution):
            if obj.source.lower() == source_name.lower():
                contributions.append({
                    'target': obj.target,
                    'type': obj.type.value
                })
    
    return contributions


def checkContribution(source: str, target: str) -> Dict:
    """
    Check if source contributes to target.
    
    Returns:
        {'contributes': bool, 'type': str or None}
    """
    # Find all Contribution instances
    for name, obj in inspect.getmembers(metamodel):
        if isinstance(obj, metamodel.Contribution):
            if (obj.source.lower() == source.lower() and 
                obj.target.lower() == target.lower()):
                return {
                    'contributes': True,
                    'type': obj.type.value
                }
    
    return {'contributes': False, 'type': None}


def checkContributionToAnyNFR(source: str) -> Dict:
    """
    Check if source contributes to any NFR.
    
    Returns:
        {'contributes': bool, 'targets': list, 'details': list}
    """
    nfr_types = [
        'Performance', 'TimePerformance', 'SpacePerformance',
        'Security', 'Confidentiality', 'Integrity', 'Availability',
        'Usability', 'Maintainability', 'Reliability', 'Accuracy',
        'Portability', 'Scalability'
    ]
    
    targets = []
    details = []
    
    # Find all Contribution instances
    for name, obj in inspect.getmembers(metamodel):
        if isinstance(obj, metamodel.Contribution):
            if obj.source.lower() == source.lower():
                if obj.target in nfr_types:
                    targets.append(obj.target)
                    details.append((obj.target, obj.type.value))
    
    return {
        'contributes': len(targets) > 0,
        'targets': targets,
        'details': details
    }


# ============================================================================
# INSTANCE QUERIES
# ============================================================================

def getInstances(cls) -> List:
    """
    Get all ground instances of a class.
    
    For Level 2 classes, returns Level 3 instances.
    
    Examples:
        >>> getInstances(OperationalizingSoftgoal)
        [Indexing, Caching, Encryption, ...]
        
        >>> getInstances(Contribution)
        [IndexingToPerformance, CachingToPerformance, ...]
    """
    instances = []
    
    # Search through metamodel for instances
    for name, obj in inspect.getmembers(metamodel):
        if not inspect.isclass(obj) and not inspect.isfunction(obj):
            if not name.startswith('_'):
                # Check if it's an instance of the class
                try:
                    if isinstance(obj, cls):
                        instances.append(obj)
                except:
                    pass
    
    return instances


def getAllGroundInstances() -> Dict[str, List]:
    """
    Get all ground instances organized by class.
    
    Returns:
        Dictionary mapping class names to lists of instances
    """
    result = {}
    
    # Get all operationalizing softgoals
    result['OperationalizingSoftgoal'] = getInstances(metamodel.OperationalizingSoftgoal)
    result['NFRSoftgoal'] = getInstances(metamodel.NFRSoftgoal)
    result['ClaimSoftgoal'] = getInstances(metamodel.ClaimSoftgoal)
    
    return result


# ============================================================================
# INFORMATION QUERIES
# ============================================================================

def getDecompositionsFor(softgoal_type) -> List:
    """
    Get all decomposition methods for a given softgoal type.
    
    Args:
        softgoal_type: A SoftgoalType class to find decompositions for
    
    Returns:
        List of DecompositionMethod instances that decompose this type
    
    Examples:
        >>> getDecompositionsFor(PerformanceType)
        [PerformanceDecomp1, PerformanceDecomp2]
    """
    decompositions = []
    
    # Search through metamodel for DecompositionMethod instances
    for name, obj in inspect.getmembers(metamodel):
        # Check if it's a DecompositionMethod instance
        if hasattr(metamodel, 'DecompositionMethod') and isinstance(obj, metamodel.DecompositionMethod):
            # Check if this method decomposes our type
            if hasattr(obj, 'parent') and obj.parent == softgoal_type:
                decompositions.append(obj)
    
    return decompositions


def whatIs(entity_or_name, verbose: bool = True) -> str:
    """
    Get comprehensive information about an entity.
    
    Includes:
    - Description
    - Parent class
    - Children (subclasses)
    - Attributes
    - Decompositions (if it's a SoftgoalType)
    
    Args:
        entity_or_name: Either a string name or an entity object
        verbose: If True, return comprehensive info; if False, just description
    
    Examples:
        >>> whatIs("Performance")
        Returns comprehensive info about Performance type
        
        >>> whatIs(Performance, verbose=False)
        'System response time, throughput, and efficiency'
    """
    # If it's a string, resolve it
    if isinstance(entity_or_name, str):
        entity = getEntity(entity_or_name)
        entity_name = entity_or_name
    else:
        # It's already an entity
        entity = entity_or_name
        entity_name = getEntityName(entity)
    
    if not entity:
        return f"Entity '{entity_name}' not found"
    
    # Get classification and structure info
    import inspect
    import metamodel
    
    classification = "Unknown"
    if inspect.isclass(entity):
        try:
            if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(entity, metamodel.NFRSoftgoalType):
                classification = "NFR (Non-Functional Requirement)"
            elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(entity, metamodel.FunctionalRequirementType):
                classification = "Functional Requirement"
            elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(entity, metamodel.OperationalizingSoftgoalType):
                classification = "Operationalizing Softgoal"
            elif hasattr(metamodel, 'OperationalizingType') and issubclass(entity, metamodel.OperationalizingType):
                classification = "Operationalizing Softgoal"
        except (TypeError, AttributeError):
            pass
    
    # If not verbose, return minimal structural info
    if not verbose:
        result = f"**Type:** {classification}\n\n"
        
        # Add decomposition info if available (ONLY direct children)
        if inspect.isclass(entity):
            children = getChildren(entity)
            if children:
                child_names = [format_entity_name(getEntityName(c)) for c in children]
                result += f"**Decomposes into ({len(children)} direct children):**\n"
                for child_name in child_names:
                    result += f"• {child_name}\n"
        
        return result
    
    # Build comprehensive information
    result = []
    
    # Classification (NFR/FR/Operationalization)
    classification = "Unknown"
    if inspect.isclass(entity):
        try:
            # Check most specific types first, then more generic
            if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(entity, metamodel.NFRSoftgoalType):
                classification = "NFR (Non-Functional Requirement)"
            elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(entity, metamodel.FunctionalRequirementType):
                classification = "Functional Requirement"
            elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(entity, metamodel.OperationalizingSoftgoalType):
                classification = "Operationalizing Softgoal"
            elif hasattr(metamodel, 'OperationalizingType') and issubclass(entity, metamodel.OperationalizingType):
                classification = "Operationalizing Softgoal"
            elif hasattr(metamodel, 'ClaimSoftgoalType') and issubclass(entity, metamodel.ClaimSoftgoalType):
                classification = "Claim Softgoal"
            elif hasattr(metamodel, 'SoftgoalType') and issubclass(entity, metamodel.SoftgoalType):
                classification = "Softgoal"
        except (TypeError, AttributeError):
            pass
    
    # Format entity name (remove Type/Softgoal suffix for display)
    display_name = entity_name.replace('Type', '').replace('Softgoal', '')
    
    
    # Don't show redundant header - user already knows what they searched for
    result.append(f"ðŸ” {classification}")
    
    
    # Decomposition info not included - used by "What is X?" which shouldnt mention it
    
    # Attributes
    if inspect.isclass(entity):
        attributes = getAttributes(entity)
    else:
        # For instances, get attributes from their class
        attributes = getAttributes(type(entity))
    
    if attributes:
        result.append(f"\nAttributes: {len(attributes)}")
        for attr in attributes:
            # Try to get the value if it's an instance
            if not inspect.isclass(entity) and hasattr(entity, attr):
                value = getattr(entity, attr)
                # Format the value
                if inspect.isclass(value):
                    value_str = value.__name__
                elif hasattr(value, 'name'):  # Enum
                    value_str = value.name
                elif hasattr(value, '__name__'):
                    value_str = value.__name__
                else:
                    value_str = str(value)
                result.append(f"  â€¢ {attr} = {value_str}")
            else:
                # For classes, just show attribute name
                result.append(f"  â€¢ {attr}")
    
    result.append("=" * 70)
    
    return "\n".join(result)




def printHierarchy(cls, level: int = 0, max_depth: int = 3):
    """
    Print class hierarchy tree.
    
    Example:
        >>> printHierarchy(Proposition)
        Proposition: A statement or assertion in the NFR Framework
          Softgoal: A softgoal without clear-cut satisfaction criteria
            NFRSoftgoal: A softgoal representing a non-functional requirement
            OperationalizingSoftgoal: A softgoal representing a concrete operationalization
            ClaimSoftgoal: A softgoal representing a claim about the domain
    """
    if level > max_depth:
        return
    
    indent = "  " * level
    desc = getattr(cls, 'description', 'No description')
    print(f"{indent}{cls.__name__}: {desc}")
    
    for subclass in cls.__subclasses__():
        printHierarchy(subclass, level + 1, max_depth)


# ============================================================================
# MISSING FUNCTIONS - ADDED BACK
# ============================================================================

def getAllClasses() -> List[str]:
    """
    Get all class names in the metamodel.
    
    Returns:
        List of class names
    """
    classes = []
    for name, obj in inspect.getmembers(metamodel):
        if inspect.isclass(obj) and not name.startswith('_'):
            # Exclude built-in types and metaclasses
            if obj.__module__ == 'metamodel':
                classes.append(name)
    return sorted(classes)


def getAllMetaclasses() -> List[str]:
    """
    Get all metaclass names in the metamodel.
    
    Returns:
        List of metaclass names (classes ending with 'MetaClass')
    """
    metaclasses = []
    for name, obj in inspect.getmembers(metamodel):
        if inspect.isclass(obj) and name.endswith('MetaClass'):
            metaclasses.append(name)
    return sorted(metaclasses)


def getAllNFRTypes() -> List[str]:
    """
    Get all NFR (Non-Functional Requirement) types from the metamodel.
    
    These are all subclasses of NFRSoftgoalType.
    
    Returns:
        List of NFR type names (without 'Type' suffix for readability)
    
    Examples:
        >>> getAllNFRTypes()
        ['Performance', 'Security', 'Usability', 'Reliability', ...]
    """
    nfr_types = []
    
    # Get NFRSoftgoalType class
    if not hasattr(metamodel, 'NFRSoftgoalType'):
        return []
    
    base_class = metamodel.NFRSoftgoalType
    
    for name, obj in inspect.getmembers(metamodel):
        if inspect.isclass(obj) and obj != base_class:
            # Check if it's a subclass of NFRSoftgoalType
            try:
                if issubclass(obj, base_class):
                    # Remove 'Type' suffix for readability
                    clean_name = name[:-4] if name.endswith('Type') else name
                    nfr_types.append(clean_name)
            except TypeError:
                continue
    
    return sorted(nfr_types)


def getAllOperationalizingTypes() -> List[str]:
    """
    Get all Operationalizing (Functional Requirement operation) types from the metamodel.
    
    These are all subclasses of OperationalizingSoftgoalType.
    
    Returns:
        List of operationalizing type names (without 'Type' suffix for readability)
    
    Examples:
        >>> getAllOperationalizingTypes()
        ['Authentication', 'Backup', 'Caching', 'Display', 'Encryption', ...]
    """
    op_types = []
    
    # Get OperationalizingSoftgoalType class
    if not hasattr(metamodel, 'OperationalizingSoftgoalType'):
        return []
    
    base_class = metamodel.OperationalizingSoftgoalType
    
    for name, obj in inspect.getmembers(metamodel):
        if inspect.isclass(obj) and obj != base_class:
            # Check if it's a subclass of OperationalizingSoftgoalType
            try:
                if issubclass(obj, base_class):
                    # Remove 'Type' suffix for readability
                    clean_name = name[:-4] if name.endswith('Type') else name
                    op_types.append(clean_name)
            except TypeError:
                continue
    
    return sorted(op_types)


def getAllSoftgoalTypes() -> Dict[str, List[str]]:
    """
    Get all softgoal types organized by category.
    
    Returns:
        Dictionary with 'NFR' and 'Operationalizing' keys containing lists of types
    
    Examples:
        >>> getAllSoftgoalTypes()
        {
            'NFR': ['Performance', 'Security', ...],
            'Operationalizing': ['Authentication', 'Caching', ...]
        }
    """
    return {
        'NFR': getAllNFRTypes(),
        'Operationalizing': getAllOperationalizingTypes()
    }


def getAncestors(cls) -> List:
    """
    Get all ancestor classes (parent, grandparent, etc.) of a class.
    
    Examples:
        >>> getAncestors(NFRSoftgoal)
        [Softgoal, Proposition, object]
    """
    if not inspect.isclass(cls):
        return []
    
    # Use MRO (Method Resolution Order) but exclude the class itself
    ancestors = []
    for ancestor in cls.__mro__[1:]:  # Skip first element (the class itself)
        if ancestor != object:  # Optionally exclude 'object'
            ancestors.append(ancestor)
    
    return ancestors


def instanceOf(entity, class_or_name) -> bool:
    """
    Check if entity is an instance of a class.
    
    Examples:
        >>> instanceOf(Indexing, OperationalizingSoftgoal)
        True
        
        >>> instanceOf(Performance, SoftgoalType)
        True
    """
    # Resolve class if name provided
    if isinstance(class_or_name, str):
        class_or_name = getEntity(class_or_name)
    
    if class_or_name is None:
        return False
    
    # Check if entity is instance of class
    if inspect.isclass(entity):
        # Entity is a class, check if it's a subclass
        try:
            return issubclass(entity, class_or_name)
        except TypeError:
            return False
    else:
        # Entity is an instance
        return isinstance(entity, class_or_name)


def getEntityInfo(entity) -> Dict[str, Any]:
    """
    Get comprehensive information about an entity.
    
    Returns:
        Dictionary with name, type, description, metaclass, parent, children, attributes, instances
    """
    if entity is None:
        return {}
    
    info = {
        'name': entity.__name__ if hasattr(entity, '__name__') else str(entity),
        'type': 'class' if inspect.isclass(entity) else 'instance',
        'description': getattr(entity, 'description', 'No description'),
        'metaclass': None,
        'parent': None,
        'children': [],
        'attributes': [],
        'instances': []
    }
    
    if inspect.isclass(entity):
        # Get metaclass
        try:
            mc = getMetaclass(entity)
            if mc:
                info['metaclass'] = mc.__name__
        except:
            pass
        
        # Get parent
        try:
            parent = getParent(entity)
            if parent:
                info['parent'] = parent.__name__
        except:
            pass
        
        # Get children
        try:
            children = getChildren(entity)
            info['children'] = [c.__name__ for c in children]
        except:
            pass
        
        # Get attributes
        try:
            attrs = getAttributes(entity)
            info['attributes'] = attrs
        except:
            pass
        
        # Get instances (if it's a class)
        try:
            instances = getInstances(entity)
            if instances and len(instances) < 20:  # Don't include if too many
                info['instances'] = [str(i) if not hasattr(i, '__name__') else i.__name__ for i in instances]
        except:
            pass
    
    return info


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TESTING 3-LEVEL METAMODEL QUERIES")
    print("="*70)
    
    # Test 1: Entity resolution
    print("\n1. Entity Resolution:")
    softgoal = getEntity("softgoal")
    print(f"   getEntity('softgoal') = {softgoal}")
    print(f"   Level: {get_level(softgoal)}")
    
    indexing = getEntity("indexing")
    print(f"   getEntity('indexing') = {indexing}")
    print(f"   Level: {get_level(indexing)}")
    
    # Test 2: Attributes
    print("\n2. Attributes:")
    attrs = getAttributes(metamodel.Softgoal)
    print(f"   Softgoal attributes: {attrs}")
    
    attrs_inst = getAttributes(indexing)
    print(f"   Indexing attributes: {attrs_inst}")
    
    # Test 3: Hierarchy
    print("\n3. Hierarchy:")
    children = getChildren(metamodel.Softgoal)
    print(f"   Softgoal children: {[c.__name__ for c in children]}")
    
    parent = getParent(metamodel.NFRSoftgoal)
    print(f"   NFRSoftgoal parent: {parent.__name__}")
    
    # Test 4: Metaclass
    print("\n4. Metaclass:")
    mc = getMetaclass(metamodel.Softgoal)
    print(f"   Softgoal metaclass: {mc.__name__}")
    
    # Test 5: Contributions
    print("\n5. Contributions:")
    contribs = getContributions("Indexing")
    print(f"   Indexing contributions: {contribs}")
    
    check = checkContribution("Indexing", "Performance")
    print(f"   Indexing ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Performance: {check}")
    
    # Test 6: NFR check
    print("\n6. NFR Check:")
    print(f"   isNFR(Performance): {isNFR(metamodel.Performance)}")
    print(f"   isNFR(Indexing): {isNFR(indexing)}")
    
    # Test 7: Ground instances
    print("\n7. Ground Instances:")
    ops = getInstances(metamodel.OperationalizingSoftgoal)
    print(f"   OperationalizingSoftgoal instances: {len(ops)}")
    
    print("\n" + "="*70)
    print("ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ All queries working!")
    print("="*70)