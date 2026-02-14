"""
NFR Assistant - Prompt Templates
=================================
Structured prompts for different menu actions
"""

MENU_PROMPTS = {
    "define_entity": """
"What is {user_input}?"

Provide a brief, clear, and concise explanation of what {user_input} is. Try to make it so that even people who have no expert knowledge in the requirements engineering
field can understand what's going on. Keep it simple and direct, and about the entity itself.
""",


    "browse_entity": """
Explain {user_input} based on this given this information about its decomposition methods and correlation rules:

{context}

Be concise but cover all information given to you. Do not change or add any offsprings in decomposition methods.
""",

    "define_nfr": """
What is {user_input}?

Given this NFR type information:
{context}

Provide a brief, clear, and concise explanation of what {user_input} is. Try to make it so that even people who have no expert knowledge in the requirements engineering
field can understand what's going on. Keep it simple and direct, and about the entity itself. Provide easy to understand examples if it fits.

""",

    "decompose": """
Decompose {user_input}

given the decomposition information:
{context}

Try to explain the logic for each decomposition in a clear and concise way, give examples where possible.
""",

    
    "show_examples": """
Try to explain in detail about what {user_input} is, given the information:

{context}

Provide a concise explanation covering all the information given but not in a way that is too verbose; provide an example. Be brief but helpful.
""",

    "show_operationalizations": """
Explain operationalizations (alternative design techniques) for achieving/satisficing the {user_input} NFR, given the information:

{context}

Explain the available techniques given, including how they work, how they help achieving/satisficing the {user_input}. Provide practical examples, and add a small part about the trade-offs/considerations for using each operationalization provided. 
""",


    "analyze_contributions": """
Analyze and explain the following contribution relationships for {user_input}:

{context}

Explain each trade-off, what techniques or operationalizations help or hurt which NFRs, what are the contribution types/side effects? Provide an example where you can.
Help me understand the implications for using each technique.
""",

    "default": """
User query: {user_input}

Metamodel data:
{context}

Provide a helpful response based on this metamodel information. Be clear, practical, and grounded in the provided context.
""",

    "verify": """You are verifying a statement about the NFR Framework metamodel.

User's statement: {user_input}

Your task is to check if this statement is TRUE or FALSE based on the metamodel.

Instructions:
1. Parse the statement to understand what is being claimed
2. Identify the entities and relationships mentioned
3. Query the metamodel to check if the claim is accurate
4. Respond with a clear verdict

Response format:

[✓ VERIFIED] or [✗ NOT VERIFIED]

Statement: [restate the user's claim]

Analysis:
[Explain how you interpreted the statement and what you checked in the metamodel]

Metamodel Evidence:
[Show what you found - actual entity names, relationships, offspring, etc.]

Verdict:
[Clear explanation of whether the statement is correct or incorrect, and why]

Be precise. Use actual metamodel entity names. If the statement is partially correct, explain what's right and what's wrong.

Statement types you can verify:
- "X is an NFR" - Check if X exists as an NFR type
- "X is an operationalization" - Check if X is an operationalization
- "X is decomposed into Y and Z" - Check if X has decomposition with Y and Z as offspring
- "X contributes to Y" - Check contribution relationships
"""
}