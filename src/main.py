import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
#import funtions to specific work
from .preproccesing import preprocess_file as pref
from .data_vector import base_vectorice as bv
from .agentes import model
from .tools import retrieve as rt
import logging
import time

llm=None
retriever_breb=None
retriever_sedes=None
retriever_productos=None

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="app.log",
    filemode="a",  #agregar
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, retriever_breb, retriever_sedes, retriever_productos
    logger.info("Procesando recursos...")
    logger.info("Loading docs...")
    #build resources path
    path_base = os.path.dirname(os.path.abspath(__name__))
    path_resources = os.path.join(path_base, "resources\\")
    #Calling preprocessing function
    files_preprocessed = pref.files_preprocessing(path_resources)    
    logger.info("Creando base vectorial...")
    dbvector = bv.create_db_vectorial(files_preprocessed)
    logger.info("Cargando LLM...")
    llm = model.created_model()
    retriever_breb = rt.create_retriever_tool(dbvector["bre-b"], "breb_tool", "Información sobre BRE-B")
    retriever_sedes = rt.create_retriever_tool(dbvector["sedes_review"], "sedes_review_tool", "Reviews de sedes")
    retriever_productos = rt.create_retriever_tool(dbvector["productos"], "productos_tool", "Productos bancarios")
    logger.info("Base de datos vectoriales...")
    yield  
    

#creación del servidor
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionUser(BaseModel):
    question: str
    
@app.post("/")
def post_question(question: QuestionUser):
    start = time.time()
    logger.info(f"Pregunta recibida: {question.question}")
    answer = model.created_agente(
        llm,
        [retriever_breb, retriever_sedes, retriever_productos],
        question.question
    )
    logger.info(f"Respuesta generada: {answer}")
    end = time.time()
    duration = round(end - start, 2)
    logger.info(f"Respuesta generada en {duration}s")
    return {"answer": answer}