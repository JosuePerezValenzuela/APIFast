from enum import Enum

from fastapi import FastAPI

from pydantic import BaseModel

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/")
async def root():
    return { "message": "Hello World"}

# ** PARAMETROS EN LAS RUTAS

# Parametro item_id de tipo int, lo convierte si es posible
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

#Misma ruta con el de abajo, pero el orden importa parao no tener errores
@app.get("/users/me")
async def read_user_me():
    return {"used_id": "the current user"}

@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}

#El parametro de ruta esta definido por un enum
@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    
    if model_name is ModelName.lenet:
        return {"model_name": model_name, "message": "LeCNN all the images"}
    
    return {"model_name": model_name, "message": "Have some residuals"}

#Ruta como parametro de una ruta con el tipo :path en la ruta
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}

# ** Query parameters
# Cuando no esta declarado en la ruta, son automaticamente interpretadas como
# query parameters

@app.get("/items2/")
async def read_item2(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]

# ** Parametros opcionales

@app.get("/items3/{item_id}")
async def read_item3(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

# ** Multiples parametros de ruta y query

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
        user_id: int, item_id: str, needy: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

class Item (BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    item_dict.update({"item_id": item_id})
    return item_dict