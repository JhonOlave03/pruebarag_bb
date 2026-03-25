from fastapi import FastAPI


#creación del servidor
app = FastAPI()
@app.get("/")
def home():
    return {"status":"OIk"}
