import glob
from pathlib import Path
import pickle
import numpy as np
import difflib
import concurrent.futures
import logging
from typing import List, Dict, Tuple, Optional, Any
from langchain_openai import AzureOpenAIEmbeddings
from datasketch import MinHash, MinHashLSH
import os
import warnings
warnings.filterwarnings(action="ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force = True)


EMBEDDING_FUNCTION = ""


def entity_retrieval(dir_path: str, user_query: str, kpi_docs: str, tentative_schema: dict, extracted_keywords: List[str], embeddings: Optional[AzureOpenAIEmbeddings]=None) -> Dict[str, Dict[str, List[str]]]:
    """
    Retrieves entities and columns similar to given keywords.

    Args:
        user_query (str): _description_
        kpi_docs (str): _description_
        tentative_schema (str): The current tentative schema
        extracted_keywords (List[str]): _description_

    Returns:
        Dict[str, Any]: A dictionary containing similar columns and values.
    """
    global EMBEDDING_FUNCTION
    EMBEDDING_FUNCTION = embeddings
    # keywords = extracted_keywords
    # similar_columns = get_similar_columns(keywords=keywords, question=user_query, hint=kpi_docs, tentative_schema=tentative_schema)
    # result = {"similar_columns": similar_columns}
    # result = {}
    similar_values = get_similar_entities(keywords=extracted_keywords, db_id=tentative_schema.get("db_id", ""), dir_path=dir_path)
    # result["similar_values"] = similar_values
    # return result
    return similar_values

### Column name similarity ###
def get_similar_columns(keywords: List[str], question: str, hint: str, tentative_schema: dict) -> Dict[str, List[str]]:
    """
    Finds columns similar to given keywords based on question and hint.

    Args:
        keywords (List[str]): The list of keywords.
        question (str): The question string.
        hint (str): The hint string.

    Returns:
        Dict[str, List[str]]: A dictionary mapping table names to lists of similar column names.
    """
    selected_columns = {}
    for keyword in keywords:
        similar_columns = _get_similar_column_names(keyword=keyword, question=question, hint=hint, tentative_schema=tentative_schema)
        for table_name, column_name in similar_columns:
            selected_columns.setdefault(table_name, []).append(column_name)
    return selected_columns

def _column_value(string: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Splits a string into column and value parts if it contains '='.

    Args:
        string (str): The string to split.

    Returns:
        Tuple[Optional[str], Optional[str]]: The column and value parts.
    """
    if "=" in string:
        left_equal = string.find("=")
        first_part = string[:left_equal].strip()
        second_part = string[left_equal + 1:].strip() if len(string) > left_equal + 1 else None
        return first_part, second_part
    return None, None

def _extract_paranthesis(string: str) -> List[str]:
    """
    Extracts strings within parentheses from a given string.

    Args:
        string (str): The string to extract from.

    Returns:
        List[str]: A list of strings within parentheses.
    """
    paranthesis_matches = []
    open_paranthesis = []
    for i, char in enumerate(string):
        if char == "(":
            open_paranthesis.append(i)
        elif char == ")" and open_paranthesis:
            start = open_paranthesis.pop()
            found_string = string[start:i + 1]
            if found_string:
                paranthesis_matches.append(found_string)
    return paranthesis_matches

def _does_keyword_match_column(keyword: str, column_name: str, threshold: float = 0.9) -> bool:
    """
    Checks if a keyword matches a column name based on similarity.

    Args:
        keyword (str): The keyword to match.
        column_name (str): The column name to match against.
        threshold (float, optional): The similarity threshold. Defaults to 0.9.

    Returns:
        bool: True if the keyword matches the column name, False otherwise.
    """
    keyword = keyword.lower().replace(" ", "").replace("_", "").rstrip("s")
    column_name = column_name.lower().replace(" ", "").replace("_", "").rstrip("s")
    similarity = difflib.SequenceMatcher(None, column_name, keyword).ratio()
    return similarity >= threshold

def _get_similar_column_names(keyword: str, question: str, hint: str, tentative_schema: dict) -> List[Tuple[str, str]]:
    """
    Finds column names similar to a keyword.

    Args:
        keyword (str): The keyword to find similar columns for.
        question (str): The question string.
        hint (str): The hint string.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing table and column names.
    """
    keyword = keyword.strip()
    potential_column_names = [keyword]

    column, value = _column_value(keyword)
    if column:
        potential_column_names.append(column)

    potential_column_names.extend(_extract_paranthesis(keyword))

    if " " in keyword:
        potential_column_names.extend(part.strip() for part in keyword.split())

    # schema = DatabaseManager().get_db_schema()
    schema = {
                key: list(value["fields"].keys())
                for key, value in tentative_schema["tables"].items()
            }

    similar_column_names = []
    for table, columns in schema.items():
        for column in columns:
            for potential_column_name in potential_column_names:
                if _does_keyword_match_column(potential_column_name, column, 0.5):
                    similarity_score = _get_semantic_similarity_with_openai(f"`{table}`.`{column}`", [f"{question} {hint}"])[0]
                    similar_column_names.append((table, column, similarity_score))

    similar_column_names.sort(key=lambda x: x[2], reverse=True)
    # print(keyword, similar_column_names)
    # return [(table, column) for table, column, _ in similar_column_names[:1]]
    return [(table, column) for table, column, _ in similar_column_names]

### Entity similarity ###

def get_similar_entities(keywords: List[str], db_id: str, dir_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Retrieves similar entities from the database based on keywords.

    Args:
        keywords (List[str]): The list of keywords.

    Returns:
        Dict[str, Dict[str, List[str]]]: A dictionary mapping table and column names to similar entities.
    """
    selected_values = {}

    extract_chunk_num = lambda x: int(x.split("chunk_")[-1].split(".")[0])
    lsh_file_paths = sorted([file for file in glob.glob(f"{dir_path}/preprocessed/{db_id}_lsh_chunk_*.pkl")], key=extract_chunk_num)
    minhashes_file_paths = sorted([file for file in glob.glob(f"{dir_path}/preprocessed/{db_id}_minhashes_chunk_*.pkl")], key=extract_chunk_num)
    path_pairs = list(zip(lsh_file_paths, minhashes_file_paths))

    def get_similar_values_target_string(target_string: str, lsh, minhashes):
        unique_similar_values = query_lsh(
            lsh=lsh, 
            minhashes=minhashes, 
            keyword=target_string, 
            signature_size=100, 
            n_gram=3,
            top_n=10
        )
        del lsh, minhashes
        return target_string, _get_similar_entities_to_keyword(target_string, unique_similar_values)
    
    def get_selected_similar_values(keyword, lsh, minhashes):
        _selected_values = {}
        keyword = keyword.strip()
        to_search_values = [keyword, keyword.lower(), keyword.capitalize(), keyword.upper()]
        if (" " in keyword) and ("=" not in keyword):
            for i in range(len(keyword)):
                if keyword[i] == " ":
                    first_part = keyword[:i]
                    second_part = keyword[i+1:]
                    if first_part not in to_search_values:
                        to_search_values.append(first_part)
                    if second_part not in to_search_values:
                        to_search_values.append(second_part)

        to_search_values.sort(key=len, reverse=True)
        hint_column, hint_value = _column_value(keyword)
        if hint_value:
            to_search_values = [hint_value, *to_search_values]
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_similar_values_target_string, ts, lsh, minhashes): ts for ts in to_search_values}
            for future in concurrent.futures.as_completed(futures):
                target_string, similar_values = future.result()
                for table_name, column_values in similar_values.items():
                    for column_name, entities in column_values.items():
                        if entities:
                            _selected_values.setdefault(table_name, {}).setdefault(column_name, []).extend(
                                [(ts, value, edit_distance, embedding) for ts, value, edit_distance, embedding in entities]
                            )
        return _selected_values

    with concurrent.futures.ThreadPoolExecutor() as lsh_executor:
        futures = []
        for lsh_file_path, minhashes_file_path in path_pairs:
            with Path(lsh_file_path).open("rb") as file:
                lsh = pickle.load(file)
            with Path(minhashes_file_path).open("rb") as file:
                minhashes = pickle.load(file)
            futures.extend([lsh_executor.submit(get_selected_similar_values, keyword, lsh, minhashes) for keyword in keywords])
        for future in concurrent.futures.as_completed(futures):
            selected_similar_values = future.result()
            for table_name, column_values in selected_similar_values.items():
                for column_name, entities in column_values.items():
                    if entities:
                        selected_values.setdefault(table_name, {}).setdefault(column_name, []).extend(
                            [(ts, value, edit_distance, embedding) for ts, value, edit_distance, embedding in entities]
                        )

    for table_name, column_values in selected_values.items():
        for column_name, values in column_values.items():
            max_edit_distance = max(values, key=lambda x: x[2])[2]
            selected_values[table_name][column_name] = list(set(
                value for _, value, edit_distance, _ in values if edit_distance == max_edit_distance
            ))
    return selected_values

def _get_similar_entities_to_keyword(keyword: str, unique_values: Dict[str, Dict[str, List[str]]]) -> Dict[str, Dict[str, List[Tuple[str, str, float, float]]]]:
    """
    Finds entities similar to a keyword in the database.

    Args:
        keyword (str): The keyword to find similar entities for.
        unique_values (Dict[str, Dict[str, List[str]]]): The dictionary of unique values from the database.

    Returns:
        Dict[str, Dict[str, List[Tuple[str, str, float, float]]]]: A dictionary mapping table and column names to similar entities.
    """
    return {
        table_name: {
            column_name: _get_similar_values(keyword, values)
            for column_name, values in column_values.items()
        }
        for table_name, column_values in unique_values.items()
    }

def _get_similar_values(target_string: str, values: List[str]) -> List[Tuple[str, str, float, float]]:
    """
    Finds values similar to the target string based on edit distance and embedding similarity.

    Args:
        target_string (str): The target string to compare against.
        values (List[str]): The list of values to compare.

    Returns:
        List[Tuple[str, str, float, float]]: A list of tuples containing the target string, value, edit distance, and embedding similarity.
    """
    edit_distance_threshold = 0.3
    top_k_edit_distance = 5
    embedding_similarity_threshold = 0.6
    top_k_embedding = 1

    edit_distance_similar_values = [
        (value, difflib.SequenceMatcher(None, value.lower(), target_string.lower()).ratio())
        for value in values
        if difflib.SequenceMatcher(None, value.lower(), target_string.lower()).ratio() >= edit_distance_threshold
    ]
    edit_distance_similar_values.sort(key=lambda x: x[1], reverse=True)
    edit_distance_similar_values = edit_distance_similar_values[:top_k_edit_distance]
    similarities = _get_semantic_similarity_with_openai(target_string, [value for value, _ in edit_distance_similar_values])
    embedding_similar_values = [
        (target_string, edit_distance_similar_values[i][0], edit_distance_similar_values[i][1], similarities[i])
        for i in range(len(edit_distance_similar_values))
        if similarities[i] >= embedding_similarity_threshold
    ]

    embedding_similar_values.sort(key=lambda x: x[2], reverse=True)
    return embedding_similar_values[:top_k_embedding]

def _get_semantic_similarity_with_openai(target_string: str, list_of_similar_words: List[str]) -> List[float]:
    """
    Computes semantic similarity between a target string and a list of similar words using OpenAI embeddings.

    Args:
        target_string (str): The target string to compare.
        list_of_similar_words (List[str]): The list of similar words to compare against.

    Returns:
        List[float]: A list of similarity scores.
    """
    target_string_embedding = EMBEDDING_FUNCTION.embed_query(target_string)
    all_embeddings = EMBEDDING_FUNCTION.embed_documents(list_of_similar_words)
    # similarities = [np.dot(target_string_embedding, embedding) for embedding in all_embeddings]
    similarities = [
        np.dot(target_string_embedding, embedding)/(np.linalg.norm(embedding)*np.linalg.norm(target_string_embedding)) 
        for embedding in all_embeddings
    ]
    return similarities

def query_lsh(lsh: MinHashLSH, minhashes: Dict[str, Tuple[MinHash, str, str, str]], keyword: str, 
              signature_size: int = 20, n_gram: int = 3, top_n: int = 10) -> Dict[str, Dict[str, List[str]]]:
    """
    Queries the LSH for similar values to the given keyword and returns the top results.

    Args:
        lsh (MinHashLSH): The LSH object.
        minhashes (Dict[str, Tuple[MinHash, str, str, str]]): The dictionary of MinHashes.
        keyword (str): The keyword to search for.
        signature_size (int, optional): The size of the MinHash signature.
        n_gram (int, optional): The n-gram size for the MinHash.
        top_n (int, optional): The number of top results to return.

    Returns:
        Dict[str, Dict[str, List[str]]]: A dictionary containing the top similar values.
    """
    query_minhash = _create_minhash(signature_size, keyword, n_gram)
    results = lsh.query(query_minhash)
    # print(keyword, results)
    similarities = [(result, _jaccard_similarity(query_minhash, minhashes[result][0])) for result in results]
    similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_n]

    similar_values_trimmed: Dict[str, Dict[str, List[str]]] = {}
    for result, similarity in similarities:
        table_name, column_name, value = minhashes[result][1:]
        if table_name not in similar_values_trimmed:
            similar_values_trimmed[table_name] = {}
        if column_name not in similar_values_trimmed[table_name]:
            similar_values_trimmed[table_name][column_name] = []
        similar_values_trimmed[table_name][column_name].append(value)

    return similar_values_trimmed

def _create_minhash(signature_size: int, string: str, n_gram: int) -> MinHash:
    """
    Creates a MinHash object for a given string.

    Args:
        signature_size (int): The size of the MinHash signature.
        string (str): The input string to create the MinHash for.
        n_gram (int): The n-gram size for the MinHash.

    Returns:
        MinHash: The MinHash object for the input string.
    """
    m = MinHash(num_perm=signature_size)
    for d in [string[i:i + n_gram] for i in range(len(string) - n_gram + 1)]:
        m.update(d.encode('utf8'))
    return m

def _jaccard_similarity(m1: MinHash, m2: MinHash) -> float:
    """
    Computes the Jaccard similarity between two MinHash objects.

    Args:
        m1 (MinHash): The first MinHash object.
        m2 (MinHash): The second MinHash object.

    Returns:
        float: The Jaccard similarity between the two MinHash objects.
    """
    return m1.jaccard(m2)