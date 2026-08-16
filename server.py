from mcp.server.mcpserver import MCPServer
from dotenv import load_dotenv
import os
from openai import OpenAI
import tempfile

load_dotenv()

client = OpenAI()
VECTOR_STORE_NAME = "MEMORIES"

mcp = MCPServer("MemoriesTwo")


def get_or_create_vector_store():
    stores = client.vector_stores.list()
    for store in stores:
        if store.name == VECTOR_STORE_NAME:
            return store
    return client.vector_stores.create(name=VECTOR_STORE_NAME)


@mcp.tool()
def save_memory(memory: str):
    vector_store = get_or_create_vector_store()
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as f:
        f.write(memory)
        f.flush()
        client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=open(f.name, "rb")
        )

    return {"status": "saved", "vector store id": vector_store.id}


@mcp.tool()
def search_memory(query: str):
    """Search memories in the vector store and return relevant chunks"""
    vector_store = get_or_create_vector_store()
    results = client.vector_stores.search(
        vector_store_id=vector_store.id,
        query=query,
    )
    content_texts = [
        content.text
        for item in results.data
        for content in item.content
        if content.type == "text"
    ]


    return {"results": content_texts}











if __name__ == "__main__":
    mcp.run()