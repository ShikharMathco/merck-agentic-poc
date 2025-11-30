import ast
import re

def extract_list(text) -> list:
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        match = re.search(r"(\[.+?\])", text)
        if match:
            try:
                return ast.literal_eval(match.group(1))
            except (SyntaxError, ValueError):
                return []
            except Exception as e:
                return []
        return []
    except Exception as e:
        return []
    
def extract_json(text):
    try:
        logging.info(f"Extracting JSON: {text}")
        codeblock_pattern = r'```json\s*(\{[\s\S]*\})\s*```'
        text = text.replace("\n", " ").strip()
        m = re.search(codeblock_pattern, text, flags=re.DOTALL)
        if m:
            data = m.group(1)
            try:
                return json.loads(data)
            except Exception as e:
                logging.warning(f"Error with json loads in regex: {str(e)}")
                try:
                    return ast.literal(data)
                except Exception as e2:
                    logging.warning(f"Error with literal eval in regex: {str(e2)}")
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end+1])
        return {}
    except Exception as e1:
        try:
            if "```json" in text:
                text = text.replace("```json", "").replace("```", "")
            text = text.strip()
            try:
                return json.loads(text)
            except Exception as json_e:
                logging.warning(f"Error with json loads: {str(json_e)}")
                try:
                    return ast.literal_eval(text)
                except Exception as ast_e:
                    logging.warning(f"Error with literal eval: {str(ast_e)}")
                    return {}
        except Exception as e2:
            logging.error(f"Error while handling the exception of extract_json: {str(e2)}", exc_info=True)
            return {}

