from fastapi import FastAPI

app = FastAPI(title="CareMinder Backend")

@app.get("/health")
def health_check():
    return {"status": "ok"}
