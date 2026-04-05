import os
import json
from google import genai
from pageindex import PageIndexClient

# load env variables
from dotenv import load_dotenv
load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Initialize clients if keys exist
pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY) if PAGEINDEX_API_KEY else None
ai_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

def call_llm(prompt, model="gemini-2.5-flash", temperature=0):
    if not ai_client:
        return "GOOGLE_API_KEY not set. Cannot call LLM."
        
    response = ai_client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=temperature
        )
    )
    return response.text.strip()

def remove_fields(tree, fields):
    if isinstance(tree, dict):
        return {k: remove_fields(v, fields) for k, v in tree.items() if k not in fields}
    elif isinstance(tree, list):
        return [remove_fields(item, fields) for item in tree]
    return tree

def create_node_mapping(tree):
    mapping = {}
    if isinstance(tree, dict):
        if 'node_id' in tree:
            mapping[tree['node_id']] = tree
        for k, v in tree.items():
            mapping.update(create_node_mapping(v))
    elif isinstance(tree, list):
        for item in tree:
            mapping.update(create_node_mapping(item))
    return mapping

class VectorlessRAG:
    def submit_document(self, file_path):
        if not pi_client:
            raise ValueError("PAGEINDEX_API_KEY not configured")
        res = pi_client.submit_document(file_path)
        return res["doc_id"]

    def is_ready(self, doc_id):
        if not pi_client:
            return False
        return pi_client.is_retrieval_ready(doc_id)
        
    def ask_question(self, doc_id, query, current_chat_history_str=""):
        if not self.is_ready(doc_id):
            return "Document is still processing in PageIndex. Please wait."

        tree_res = pi_client.get_tree(doc_id, node_summary=True)
        if 'result' not in tree_res:
            return "Error retrieving document tree from PageIndex."
        tree = tree_res['result']
        
        tree_without_text = remove_fields(tree.copy(), fields=['text'])
        
        search_prompt = f"""
        You are given a question and a tree structure of a document.
        Each node contains a node id, node title, and a corresponding summary.
        Your task is to find all nodes that are likely to contain the answer to the question.
        
        Recent chat history:
        {current_chat_history_str}
        
        Question: {query}
        
        Document tree structure:
        {json.dumps(tree_without_text, indent=2)}
        
        Please reply in the following JSON format:
        {{
            "thinking": "<Your thinking process on which nodes are relevant to the question>",
            "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
        }}
        Directly return the final JSON structure. Do not output anything else.
        """
        
        tree_search_result = call_llm(search_prompt)
        
        # Clean formatting
        if tree_search_result.startswith("```json"):
            tree_search_result = tree_search_result[7:-3].strip()
        elif tree_search_result.startswith("```"):
            tree_search_result = tree_search_result[3:-3].strip()
            
        try:
            tree_search_result_json = json.loads(tree_search_result)
        except Exception as e:
            return f"Error parsing reasoning response: {str(e)} \n\n {tree_search_result}"
            
        node_map = create_node_mapping(tree)
        node_list = tree_search_result_json.get("node_list", [])
        
        if not node_list:
            relevant_content = "No relevant context found in document based on reasoning."
        else:
            relevant_content = "\n\n".join(node_map[node_id].get("text", "") for node_id in node_list if node_id in node_map)
        
        answer_prompt = f"""
        Answer the question based on the context:
        
        Recent Chat Context:
        {current_chat_history_str}
        
        Question: {query}
        Context extracted from document:
        {relevant_content}
        
        Provide a clear, concise answer based only on the context provided.
        """
        
        answer = call_llm(answer_prompt, temperature=0.7)
        return answer
