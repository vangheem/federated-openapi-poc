from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI()


class Product(BaseModel):
    id: str


class Review(BaseModel):
    body: str
    product: Product


class User(BaseModel):
    reviews: List[Review]


USER_DATA = {
    "1": User(reviews=[Review(body="Great!", product=Product(id="1"))]),
    "2": User(reviews=[Review(body="Great!", product=Product(id="2"))]),
    "3": User(reviews=[Review(body="Great!", product=Product(id="3"))]),
}


@app.get("/users/{id}", response_model=User)
async def get_user_review(id: str) -> User:
    return USER_DATA[id]
