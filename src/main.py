import os
from fastapi import FastAPI
#import funtions to specific work
from .preproccesing import preprocess_file as pref
from .data_vector import base_vectorice as bv

#creación del servidor
app = FastAPI()
@app.get("/")
def home():
    #resources
    path_base = os.path.dirname(os.path.abspath(__name__))
    path_resources = os.path.join(path_base, "resources\\")
    #Calling preprocessing function
    files_preprocessed = pref.files_preprocessing(path_resources)
    dbvector = bv.create_db_vectorial(files_preprocessed)
    return {"status":"Ok",
            "paths": dbvector}
