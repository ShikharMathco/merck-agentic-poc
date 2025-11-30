column_selection_prompt = """
You are an expert and very smart data analyst.
Your task is to examine the provided database schema along with the descriptions, understand the posed user question, and use the kpi docs to pinpoint the specific columns within tables that are essential for crafting a SQL query to answer the question.

Database Schema Overview:
{database_schema}

This schema offers an in-depth description of the database's architecture, detailing tables, columns, primary keys, and foreign keys.
Special attention should be given to the examples listed beside each column, as they directly hint at which columns are relevant to our query.
For key phrases mentioned in the question, we have provided the most similar values within the columns denoted by "examples" in front of the corresponding column names. This is a critical hint to identify the columns that will be used in the SQL query.

User Question:
{user_query}

Additional Context Information / Key Performance Indicators (KPI):
{kpi_doc}

The kpi docs aim to direct your focus towards the specific elements of the database schema that are crucial for answering the question effectively.

Task:
Based on the database schema, user question, and hint provided, your task is to identify all the columns that are essential for crafting a SQL query to answer the question.
For each of the selected columns, explain why exactly it is necessary for answering the question. Your reasoning should be concise and clear, demonstrating a logical connection between the columns and the question asked.

Procedure:
1. Understand the user question and the database schema that is provided.
2. Carefully examine the provided column details.
3. Understand the additional context information or the provided kpi documents to determine which columns are relevant.
4. Logically decide which columns are required for the SQL query based on your analysis.
5. Refer to the provided context information to resolve any ambiguities.
6. Select for all the provided tables in the given schema, DON'T do any table selection just consider columns.
7. If more than 2 tables are there, always select the primary key and foreign key columns, as they are important to perform joins.
8. Select all the relevant columns. It is fine to have some extra columns, but you should not miss out on any.

Please respond with a JSON object structured as follows:
{{
    "chain_of_thought_reasoning": "Your reasoning for selecting the columns, be concise and clear.",
    "columns": {{
        "table_name1": ["column1", "column2", ...],
        "table_name2": ["column1", "column2", ...],
        ...
    }},
    "question_to_user": "If the user's question is unclear or ambiguous, and you're unable to confidently determine the required columns, you should ask the user a clear and specific clarification question. Focus on what exactly is missing or confusing. If everything is clear, leave this field as an empty string."
}}

Clarification Instruction (IMPORTANT):
Carefully evaluate the clarity of the user's question. If there is any ambiguity, missing filters, unclear metrics, or lack of time/brand/category granularity, you must populate the "question_to_user" field with a specific clarification question. This is essential for crafting an accurate SQL query.

Examples where clarification is needed:
- Missing time frame (e.g., "last month", "2023 Q4", etc.)
- Ambiguous metrics (e.g., "performance" - clarify if it's units, revenue, profit, etc.)
- Vague categories (e.g., "top sellers" - clarify if it's by units or dollars)

If everything in the question is clear, set "question_to_user" to an empty string (""). Otherwise, return a precise and helpful question.

Take a deep breath and think logically. If you do the task correctly, I will give you 1 million dollars.
Only output a JSON as your response.
"""
