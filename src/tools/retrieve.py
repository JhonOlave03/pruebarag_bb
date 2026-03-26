from langchain.tools import tool

def create_retriever_tool(datavec, name, description):

    @tool(name)
    def retrieved_splits(query: str) -> str:
        """Retrieve relevant chunks based on a query."""
        chunks_search = datavec.similarity_search(query, k=3)

        format_chunks_search = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}"
            for doc in chunks_search
        )
        return format_chunks_search
    
    retrieved_splits.description = description
    return retrieved_splits


