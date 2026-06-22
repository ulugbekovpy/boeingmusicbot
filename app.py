from fastapi import FastAPI

import uvicorn

from script import search

app = FastAPI()

@app.get("/search/{query}")
def search_tracks(query: str):
    result = search(query)
    return result

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)