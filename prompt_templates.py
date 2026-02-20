"""
NFR Assistant - Prompt Templates
=================================
Structured prompts for different menu actions
"""

MENU_PROMPTS = {
    "define_entity": """
What is {user_input}?

Given this NFR type information:
{context}

Provide a brief, clear, and concise explanation of what {user_input} is. Try to make it so that even people who have no expert knowledge in the requirements engineering
field can understand what's going on. Keep it simple and direct, and about the entity itself. Provide easy to understand examples if it fits.
""",


    "browse_entity": """
Explain {user_input} based on this given this information about its decomposition methods and correlation rules:

{context}

Be concise but cover all information given to you. Do not change or add any offsprings in decomposition methods.
""",

   

    "decompose": """
A softgoal can be decomposed into sub-softgoals. A decomposition helps define a softgoal, since it provides the components that makes up of the main softgoal.
Decompose the (nonfunctional requirement/operationalization) {user_input} softgoal given the decomposition information:{context}""",

    
    "show_examples": """
Try to explain in detail about what {user_input} is, given the information:

{context}

Provide a concise explanation covering all the information given but not in a way that is too verbose; provide an example. Be brief but helpful.
""",

    "show_operationalizations": """
Operationalizations, or operationalizing softgoals are possible design alternatives for meeting or satisficing non-functional requirements in the system. 
Demonstrate and explain the operationalizations for the {user_input} softgoal given the information: {context}.

""",


    "analyze_contributions": """
Analyze and explain the following contribution relationships for {user_input}:

{context}

Every operationalization, or function in the system can simultaneously have negative and positive effects on different non-functional requirements. 
Therefore, using one operationalization can help satisfice one NFR while hindering another. Explain each NFR the {user_input} operationalization affects, whether negatively or positively; analyze the {user_input}'s trade-offs.
Provide examples where you can and help understand the implications for using each technique.
""",

    "default": """
User query: {user_input}

Metamodel data:
{context}

Provide a helpful response based on this metamodel information. Be clear, practical, and grounded in the provided context.
""",

    
}