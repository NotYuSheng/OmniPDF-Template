from fastapi import FastAPI
from openai import OpenAI
<<<<<<< HEAD
<<<<<<< HEAD

=======
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict
import uuid
>>>>>>> 04e9342 (feat: basic chat service by running  /c/<query> or /c)
=======

>>>>>>> 579b4f7 (fix: clean main.py)

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


<<<<<<< HEAD
<<<<<<< HEAD
=======
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


app = FastAPI()


>>>>>>> 04e9342 (feat: basic chat service by running  /c/<query> or /c)
=======
>>>>>>> 579b4f7 (fix: clean main.py)
@app.get("/c")
def chat():
    client = OpenAI(
        base_url="http://localhost:1234/v1",  # Make sure `/v1` is included
        api_key="lm-studio"  # any dummy string
    )

    response = client.chat.completions.create(
        model="qwen2.5-0.5b-instruct",
        messages=[
            {"role": "user", "content": "List 3 niche things/items in IT Technical Skills or facts that is useful to a software engineer."}]
    )

    return {"response": response.choices[0].message.content}


@app.get("/c/{chat_item}")
def chat(chat_item):
    client = OpenAI(
        base_url="http://localhost:1234/v1",  # Make sure `/v1` is included
        api_key="lm-studio"  # any dummy string
    )

    response = client.chat.completions.create(
        model="qwen2.5-0.5b-instruct",
        messages=[{"role": "user", "content": chat_item}]
    )

    return {"response": response.choices[0].message.content}
