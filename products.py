from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Product(BaseModel):
    name: str


PRODUCT_DATA = {
    "1": Product(name="Principia Mathematica"),
    "2": Product(name="Relativity the Special General Theory"),
    "3": Product(name="Dialogue Concerning the Two Chief World Systems"),
}


@app.get("/products/{id}", response_model=Product)
async def get_product(id: str) -> Product:
    return PRODUCT_DATA[id]
