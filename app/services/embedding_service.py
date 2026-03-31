import ollama

def get_embedding(text: str) -> list[float]:
    response = ollama.embeddings(model="nomic-embed-text", prompt=text)
    vector = response["embedding"]  # list of 768 floats
    return vector