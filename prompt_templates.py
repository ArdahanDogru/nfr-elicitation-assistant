"""
NFR Assistant - Prompt Templates
=================================
Structured prompts for different menu actions
"""

MENU_PROMPTS = {
    "define_entity": """
The user asked: "What is {user_input}?"

Here is the basic information from the NFR Framework metamodel:
{context}

Provide a brief, factual response (2-3 sentences) that:
1. States whether this is a Functional Requirement (FR) or Non-Functional Requirement (NFR) type
2. Briefly explains what category it belongs to and its general purpose

Keep it simple and direct - just classification and brief context. DO NOT mention decomposition or sub-types.
""",


    "browse_entity": """
Explain {user_input} based on this information from the NFR Framework metamodel:

{context}

Provide a clear, direct explanation (3-4 sentences):
1. Start with: "{user_input} is a [type] that [purpose]"
2. If there are multiple decomposition methods, explain each one
3. For each method, list what it decomposes into using the EXACT offspring names

DO NOT use phrases like "the user is exploring" or "the user is browsing". Write as if explaining directly.
Be concise but cover all decomposition methods shown.
""",

    "define_nfr": """
The user asked: "What is {user_input}?"

Here is the NFR type information from the metamodel:
{context}

Provide a clear, practical explanation of this NFR type. Include:
1. A concise definition
2. Why this quality attribute matters to stakeholders
3. A concrete example from real software systems (e.g., e-commerce, healthcare, mobile apps)
4. Related NFR types if relevant

Keep it conversational but technically accurate, 2-3 paragraphs.
""",

    "decompose": """
The user wants to decompose: {user_input}

Metamodel decomposition information:
{context}

Explain the decomposition strategy naturally:
1. Describe the decomposition approach and why it makes sense
2. Present the child NFR types and their purposes
3. Provide a practical example scenario showing the decomposition in action
4. Mention any important trade-offs or considerations

Write in natural prose, not bullet points. Make it educational and practical.
""",

    "show_sources": """
The user wants to know the sources and justifications for decomposing: {user_input}

Metamodel information on sources and attribution:
{context}

Explain the scholarly basis for these decompositions:
1. Who proposed these decompositions? (academic sources)
2. What is the justification or reasoning?
3. How widely accepted are these approaches?
4. Are there alternative perspectives?

Be scholarly but accessible. Cite sources naturally.
""",

    "show_examples": """
The user wants details about: {user_input}

Metamodel information:
{context}

Provide a CONCISE explanation (2-3 sentences max):
1. What is this entity?
2. One practical example
3. Key takeaway or usage tip

Be brief but helpful.
""",

    "list_all_types": """
The user wants to see all available NFR types.

Complete list from metamodel:
{context}

Organize and present this information helpfully:
1. Group related types if it aids understanding
2. Provide brief context about the framework structure
3. Suggest where users might start based on common needs
4. Make it navigable, not overwhelming

Present in natural prose with clear organization.
""",

    "show_operationalizations": """
The user asked about operationalizations (techniques) for: {user_input}

Metamodel information:
{context}

Explain the available techniques:
1. What operationalizations can achieve this NFR?
2. How does each technique work?
3. What are the trade-offs or considerations?
4. Provide practical examples

Be concrete and actionable. Focus on helping users choose appropriate techniques.
""",

    "list_claims": """
The user wants to see all claim-based decompositions.

Claims from the metamodel:
{context}

Present the claims and their scholarly basis:
1. Organize claims by topic or NFR area
2. Show the academic justification for each
3. Highlight areas of consensus vs. debate
4. Explain the significance

Make the scholarly foundation accessible and clear.
""",

    "analyze_contributions": """
Analyzing contribution relationships for: {user_input}

Metamodel context:
{context}

Analyze these contribution relationships:
1. What techniques help or hurt which NFRs?
2. What are the contribution types (MAKE, HELP, HURT, BREAK) and why?
3. What are potential side effects on other quality attributes?
4. What trade-offs should designers consider?

Be explicit about both positive and negative impacts. Help users understand the full implications.
""",

    "show_claims": """
The user wants to see claims and justifications for: {user_input}

Metamodel claims information:
{context}

Explain the argumentation:
1. What scholarly sources support these decompositions?
2. What is the reasoning or justification?
3. What evidence or logic backs these claims?
4. Are there competing perspectives?

Present the academic foundation clearly and accessibly.
""",

    "explain_classification": """
A requirement was classified by the system.

Requirement: {user_input}

Classification result:
{context}

Explain this classification to the user:
1. Why does this classification make sense?
2. What key phrases indicate the category (FR vs NFR)?
3. How could the requirement be written more clearly?
4. Could this be a composite requirement? (both FR and NFR aspects)

Be educational - help them understand the reasoning process.
""",

    "explain_specific_classification": """
A requirement was classified into a specific type.

Requirement: {user_input}

Classification details:
{context}

Explain the specific type classification:
1. Why this particular NFR/FR type?
2. What phrases or characteristics indicate this type?
3. How to refine the requirement statement?
4. Are there related types to consider?

Help the user validate and improve their requirement.
""",

    "default": """
User query: {user_input}

Metamodel data:
{context}

Provide a helpful response based on this metamodel information. Be clear, practical, and grounded in the provided context.
"""
}