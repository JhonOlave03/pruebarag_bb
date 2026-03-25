import os
from fastapi import FastAPI
#import funtions to specific work
from .preproccesing import preprocess_file as pref

def preprocesing(path_resources):
    path_preprocessed = pref.identify_files(path_resources)
    return path_preprocessed
     

#creación del servidor
app = FastAPI()
@app.get("/")
def home():
    #resources
    path_base = os.path.dirname(os.path.abspath(__name__))
    path_resources = os.path.join(path_base, "resources\\")
    #Calling preprocessing function
    answer = preprocesing(path_resources)
    return {"status":"Ok",
            "paths": answer}
