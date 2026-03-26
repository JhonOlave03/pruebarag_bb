from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
load_dotenv()

def create_shunks(data):
    chunks_service = {}
    chunks_size = 250
    chunk_overlap = 50
    step = chunks_size - chunk_overlap
    for service, content in data.items():
        chunks_service[service] = []

        for item in content:
            source = item["source"]
            #print(item["content"])
            words = item["content"].split()
            
            for i in range(0, len(words), step):
                chunk_text = " ".join(words[i:i+chunks_size])
                
                chunks_service[service].append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            "service": service,
                            "source": source,
                        }
                    )
                )
                

    return chunks_service
                     
def db_build_vectorial(chunks_service):
    embeddings = HuggingFaceEmbeddings(
        model_name = "sentence-transformers/all-mpnet-base-v2"
    )
    vector_dbs = {}
    for service, docs in chunks_service.items():
        if os.path.exists(f"data_vectors/{service}"):
            vector_dbs[service] = FAISS.load_local(f"data_vectors/{service}", embeddings, allow_dangerous_deserialization=True)
        else:
            vector_dbs[service] = FAISS.from_documents(docs, embeddings)
            vector_dbs[service].save_local(f"data_vectors/{service}")
            
        
    return vector_dbs
     

def create_db_vectorial(data):
    chunks = create_shunks(data)
    db_vector = db_build_vectorial(chunks)
    return db_vector