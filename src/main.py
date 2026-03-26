import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
#import funtions to specific work
from .preproccesing import preprocess_file as pref
from .data_vector import base_vectorice as bv
from .agentes import model
from .tools import retrieve as rt

# Variables globales
llm=None
retriever_breb=None
retriever_sedes=None
retriever_productos=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, retriever_breb, retriever_sedes, retriever_productos
    print("Procesando recursos...")
    print("Loading docs...")
    #build resources path
    path_base = os.path.dirname(os.path.abspath(__name__))
    path_resources = os.path.join(path_base, "resources\\")
    #Calling preprocessing function
    files_preprocessed = pref.files_preprocessing(path_resources)    
    print("Haciendo Embeddings y creando Base de datos")
    dbvector = bv.create_db_vectorial(files_preprocessed)
    print("cargando LLM...")
    llm = model.created_model()
    retriever_breb = rt.create_retriever_tool(dbvector["bre-b"], "breb_tool", "Información sobre BRE-B")
    retriever_sedes = rt.create_retriever_tool(dbvector["sedes_review"], "sedes_review_tool", "Reviews de sedes")
    retriever_productos = rt.create_retriever_tool(dbvector["productos"], "productos_tool", "Productos bancarios")
    yield  
    print("Base de datos vectoriales, Herramientas y Agentes creados...")

#creación del servidor
app = FastAPI(lifespan=lifespan)
class QuestionUser(BaseModel):
    question: str
    
@app.post("/")
def post_question(question: QuestionUser):
    answer = model.created_agente(
        llm,
        [retriever_breb, retriever_sedes, retriever_productos],
        question.question
    )
    return {"answer": answer}