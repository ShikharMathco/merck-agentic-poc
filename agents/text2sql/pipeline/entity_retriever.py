# entity_retriever.py
import glob
from pathlib import Path
import pickle
import numpy as np
import difflib
import concurrent.futures
import logging
from typing import List, Dict, Tuple, Optional, Any
from datasketch import MinHash, MinHashLSH
import os
import warnings

warnings.filterwarnings(action="ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

# If you have an embeddings wrapper (GPTEL/Grokk), pass it as `embeddings`.
# It must implement:
#   - embed_query(text) -> vector (1D array-like)
#   - embed_documents(list_of_texts) -> list of vectors
EMBEDDING_FUNCTION: Any = None


# ---------------------------
# Simple context loader (for small folder of docs)
# ---------------------------
def get_context_documents(folder_path: str) -> Dict[str, str]:
    """
    Read all files in folder_path and return a mapping filename -> content.
    Only reads files (skips subfolders). Handles common text files.
    Use this when you have a handful (e.g. 4) context docs and want to pass them
    straight to the LLM prompt (no embeddings required).
    """
    folder = Path(folder_path)
    results: Dict[str, str] = {}
    if not folder.exists():
        logging.warning("Context folder does not exist: %s", folder_path)
        return results

    for file_path in sorted(folder.glob("*")):
        if file_path.is_file():
            try:
                # attempt text; if binary, skip
                content = file_path.read_text(encoding="utf-8")
                results[file_path.name] = content
            except Exception as e:
                logging.warning("Failed to read %s: %s", file_path, e)
    return results


# ---------------------------
# Backwards-compatible entity_retrieval
# ---------------------------
def entity_retrieval(
    dir_path: str,
    user_query: str,
    kpi_docs: str,
    tentative_schema: dict,
    extracted_keywords: List[str],
    embeddings: Optional[Any] = None,
    use_fuzzy: bool = False
) -> Dict[str, Dict[str, List[str]]]:
    """
    Top-level function used by pipeline.

    Behavior:
    - If use_fuzzy is False (default) -> load all files from dir_path/context_input (if exist)
      and return them as a special context mapping under key "_context_files".
      This is the lightweight option for small static docs (your 4 files).
    - If use_fuzzy is True -> run the original heavy fuzzy pipeline that uses preprocessed
      MinHash/LSH files under dir_path/preprocessed/*.pkl and optional embeddings.

    Args:
        dir_path: project root or base folder (used to find preprocessed chunks or context_input)
        user_query: natural language question (unused in simple mode)
        kpi_docs: auxiliary hints (unused in simple mode)
        tentative_schema: schema dict (used by fuzzy pipeline)
        extracted_keywords: keywords list used for fuzzy search
        embeddings: optional embedding wrapper (must provide embed_query/embed_documents)
        use_fuzzy: toggle fuzzy/LSH pipeline

    Returns:
        dict: either {"_context_files": {filename: content, ...}} OR fuzzy result mapping
              {table: {column: [values...]}}
    """
    global EMBEDDING_FUNCTION
    EMBEDDING_FUNCTION = embeddings

    # SIMPLE MODE: return context documents
    if not use_fuzzy:
        context_folder = os.path.join(dir_path, "context_input")
        docs = get_context_documents(context_folder)
        # The pipeline expects a mapping; we package it under a reserved key
        return {"_context_files": docs}

    # FUZZY MODE: run the old LSH / MinHash / semantic pipeline
    # (keeps original behavior for large DBs)
    similar_values = get_similar_entities(
        keywords=extracted_keywords,
        db_id=tentative_schema.get("db_id", ""),
        dir_path=dir_path
    )
    return similar_values


# ---------------------------
# --- The original fuzzy pipeline (unchanged logic, refactored)
# ---------------------------
def _column_value(string: str) -> Tuple[Optional[str], Optional[str]]:
    if "=" in string:
        left_equal = string.find("=")
        first_part = string[:left_equal].strip()
        second_part = string[left_equal + 1:].strip() if len(string) > left_equal + 1 else None
        return first_part, second_part
    return None, None


def _extract_paranthesis(string: str) -> List[str]:
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
    keyword = keyword.lower().replace(" ", "").replace("_", "").rstrip("s")
    column_name = column_name.lower().replace(" ", "").replace("_", "").rstrip("s")
    similarity = difflib.SequenceMatcher(None, column_name, keyword).ratio()
    return similarity >= threshold


def _get_similar_column_names(keyword: str, question: str, hint: str, tentative_schema: dict) -> List[Tuple[str, str]]:
    keyword = keyword.strip()
    potential_column_names = [keyword]
    column, value = _column_value(keyword)
    if column:
        potential_column_names.append(column)
    potential_column_names.extend(_extract_paranthesis(keyword))
    if " " in keyword:
        potential_column_names.extend(part.strip() for part in keyword.split())

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
    return [(table, column) for table, column, _ in similar_column_names]


def get_similar_entities(keywords: List[str], db_id: str, dir_path: str) -> Dict[str, Dict[str, List[str]]]:
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
                    second_part = keyword[i + 1:]
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
    return {
        table_name: {
            column_name: _get_similar_values(keyword, values)
            for column_name, values in column_values.items()
        }
        for table_name, column_values in unique_values.items()
    }


def _get_similar_values(target_string: str, values: List[str]) -> List[Tuple[str, str, float, float]]:
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
    target_string_embedding = EMBEDDING_FUNCTION.embed_query(target_string)
    all_embeddings = EMBEDDING_FUNCTION.embed_documents(list_of_similar_words)
    similarities = [
        np.dot(target_string_embedding, embedding) / (np.linalg.norm(embedding) * np.linalg.norm(target_string_embedding))
        for embedding in all_embeddings
    ]
    return similarities


def query_lsh(lsh: MinHashLSH, minhashes: Dict[str, Tuple[MinHash, str, str, str]], keyword: str,
              signature_size: int = 20, n_gram: int = 3, top_n: int = 10) -> Dict[str, Dict[str, List[str]]]:
    query_minhash = _create_minhash(signature_size, keyword, n_gram)
    results = lsh.query(query_minhash)
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
    m = MinHash(num_perm=signature_size)
    for d in [string[i:i + n_gram] for i in range(len(string) - n_gram + 1)]:
        m.update(d.encode('utf8'))
    return m


def _jaccard_similarity(m1: MinHash, m2: MinHash) -> float:
    return m1.jaccard(m2)
