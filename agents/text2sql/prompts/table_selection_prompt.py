table_selection_prompt = """
You are an expert and very smart data analyst.
Your task is to analyze the provided database schema along with the descriptions and some examples, comprehend the posed user question, and leverage the kpi docs and example in the schema to identify which tables are needed to generate a SQL query for answering the question.

Database Schema Overview:
{database_schema}

This schema provides a detailed definition of the database's structure, including tables, their columns, primary keys, foreign keys, and any relevant details about relationships or constraints.
For key phrases mentioned in the question, we have provided the most similar values within the columns denoted by "examples" in front of the corresponding column names. This is a critical hint to identify the tables that will be used in the SQL query.

User Question:
{user_query}

Key Performance Indicator (KPI) Information/Additional Context Information:
{kpi_doc}

Task:-
1. Analyse the User Question and identify the key entities which are mentioned in the question
2. After identifying the key entities. Analyse the database schema, question, and kpi docs/additional context information provided, your task is to determine the tables that should be used in the SQL query formulation
3. Select the tables that are relevant for answering the user question, make sure you include the tables that are required (use table descriptions and additional context provided to resolve any ambiguity)
4. For each of the selected tables, explain why exactly it is necessary for answering the question. Your explanation should be logical and concise, demonstrating a clear understanding of database schema, user question, and kpi docs.

Please respond with a JSON object structured as follows:
{{
	"chain_of_thought_reasoning": "Explanation of the logical analysis that led to the selection of the tables.",
	"tables": ["Table1", "Table2", "Table3", ...]
}}

Note that you should choose all and only the tables that are necessary to write a SQL query that answers the question effectively.
Take a deep breath and think logically. If you do the task correctly, I will give you 1 million dollars.

Only output a json as your response.
"""
