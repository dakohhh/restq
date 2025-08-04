from fastapi import FastAPI
from rest_app import rest_q


app = FastAPI()


def some():
    pass


@app.get("/")
def test_task():
    return


