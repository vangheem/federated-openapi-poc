from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI()


class User(BaseModel):
    id: str
    name: str


USER_DATA = {
    "1": User(id="1", name="Isaac Newton"),
    "2": User(id="2", name="Albert Einstein"),
    "3": User(id="3", name="Galileo Galilei"),
}


@app.get("/users/{id}", response_model=User)
async def get_user(id: str) -> User:
    return USER_DATA[id]


class UserResult(BaseModel):
    items: List[User]


@app.get("/users", response_model=UserResult)
async def get_users() -> UserResult:
    return UserResult(
        items=list(USER_DATA.values()),
    )
