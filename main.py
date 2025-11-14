from enum import Enum

from fastapi import FastAPI, Query, Path, Body, Cookie, Header

from typing import Annotated, Literal, Any

from pydantic import BaseModel, AfterValidator, Field, HttpUrl

from datetime import datetime, time, timedelta

from uuid import UUID

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                },
                {
                    "name": "Bar",
                    "price": "35.4"
                }
            ]
        }
    }

# Si el parametro esta en la ruta sera un path parameter
# Si el parametro esta basado en una clase con BaseModel sera un body
# Si el parametro es de un tipo primitivo sera un query param

@app.post("/items/{item_id}")
async def create_item(
        item_id: int, 
        item: Item, 
        #Validar que q sea maximo de 50 caracteres
        #El tener un valor por defecto hace que el parametro sea opcional
        q: Annotated[str | None, Query(min_length=3, max_length=50, pattern="^fixedquery$")] = "fixedquery"
    ):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    item_dict.update({"item_id": item_id})
    if q:
        item_dict.update({"q": q})
    return item_dict

#Crear validadores (funciones) personalizados que seran usados despues o antes 
# de las validaciones comunes (BeforeValidator y AfterValidator) dentro de 
# Annotated

def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start withc "isbn-" or "imdb-"')
    return id

#Multiples valores de q en la ruta, se debe declarar con Query() para que no
#sea considerado un body
@app.get("/items4/")
async def read_items4(
        q: Annotated[list[str] | None, 
            Query(
                alias="item-query",
                title="Query string",
                description="Query string que recibe una lista",
                min_length=2,
                #Mostrar que un endpoint esta deprecado
                deprecated=True,
                #Ocultara este parametro en la documentacion
                include_in_schema=False,
                )
        ] = ["foo", "bar"],
        id: Annotated[str | None, AfterValidator(check_valid_id)] = None
    ):
    query_items = {"q": q, "id": id}
    return query_items

@app.get("/items5/{item_id}")
async def read_item5(item_id: Annotated[int, Path(
    title="The Id of the item to get",
    ge=1,
    le=1000
    )],
                    size: Annotated[float, Query(gt=0, lt=10.5)],
                    q: Annotated[str | None, Query(alias="item-query")] = None,
    ):
    results = {"item_id": item_id}
    results.update({"size": size})
    if q:
        results.update({"q": q})
    return results

class FilterParams(BaseModel):
    #Reestringir parametros extra de consulta que manden
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items6/")
async def read_items6(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    item: Item,
    user: User,
    importance: Annotated[int, Body()],
    q: str | None = None
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        results.update({"q": q})
    return results

class Image(BaseModel):
    url: HttpUrl
    name: str

class Item2(BaseModel):
    name: str = Field(examples=["Foo"])
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300,
        examples=[3.2]
    )
    price: float = Field(
        gt=0, description="The price must be greater than zero", examples=[3.2]
    )
    tax: float | None = Field(default=None, examples=[3, 2])
    tags: set[str] = set()
    images: list[Image] | None = None

class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item2]

@app.put("/items2/{item_id}")
async def update_item2(
    item_id: int,
    item: Annotated[Item2, Body(embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results

@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer

@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images

@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights

@app.put("/items3/{item_id}")
async def update_item3(
    item_id: int,
    item: Annotated[Item, Body(
        examples=[
            {
                "name": "Fooo",
                "description": "New description",
                "price": 20.04,
                "tax": 5.5,
            },
            {
                "name": "Bar",
                "price": "38.4"
                
            }
        ]
    )]
):
    results = {"item_id": item_id, "item": item}
    return results

@app.put("/items4/{item_id}")
async def update_item4(
    item_id: int,
    item: Annotated[Item, Body(
        openapi_examples={
            "normal": {
                "summary": "A normal example",
                "description": "A **normal** item works correctly",
                "value": {
                    "name": "Fooo",
                    "description": "A very nice item",
                    "price": "35.4",
                    "tax": 3.2,
                },
            },
            "coverted": {
                "summary": "An example with coverted data",
                "description": "FastApi can convert price `strings` to actual numbers",
                "value": {
                    "name": "Bar",
                    "price": "35.4",
                },
            },
            "invalid": {
                "summary": "Invalid data is rejected with an error",
                "value": {
                    "name": "Baz",
                    "price": "Thirty five point four"
                },
            },
        },
    )],
):
    results = {"item_id": item_id, "item": item}
    return results

"""
Tipos de datos extras

UUID -> Universal Unique Identifier o los ID de las BD, representados
        como cadenas

datetime.datetime -> Un datetime.datetime de python, en las solicitudos
        y respuestas sera representado como un str con la ISO 8601

datetime.date -> Un datetime.date de Python, representado como str
        con la ISO 8601

datetime.time -> Un datetime.time de Python, representado como str con
        la ISO 8601

datetime.timedelta -> Un datetime.timedelta de Python, representado como
        float del total de segundos respetando la ISO 8601

frozenset -> Tratado como un set, 
        En la solicitud se leera como una lista eliminando duplicados y
        convirtiendolos en set

        En la respuesta sera convertido de set a una lista

        El esquema generado especificara que los valores son unicos usando
        uniqueItems de JSON Schemas's

bytes -> bytes de Python, tratados como str, el esquema generado especifica
        que es un str con formato binario

Decimal -> Decimal estandar de python, tratado como float
"""

@app.put("/items5/{item_id}")
async def read_items5(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }

@app.get("/items7/")
async def read_items7(
    ads_id: Annotated[str | None, Cookie()] = None
):
    return {"ads_id": ads_id}

# Header ofrece pequeñas extras funcionalidades aparte de las base de Path,
# Query y Cookie, por estandar estan separadas por un " - "
@app.get("/items8/")
async def read_items8(
    user_agent: Annotated[str | None, Header()] = None,
    x_token: Annotated[list[str] | None, Header()] = None
):
    return {"User-Agent": user_agent, "X-Token values": x_token}

class Cookies(BaseModel):
    model_config = {"extra": "forbid"}

    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

@app.get("/items9/")
async def read_items9(
    cookies: Annotated[Cookies, Cookie()]
):
    return cookies

class CommonHeaders(BaseModel):
    model_config = {"extra": "forbid"}

    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items10/")
async def read_items10(
    headers: Annotated[CommonHeaders, Header()]
):
    return headers

class Item4(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []

@app.post("/items2/")
async def create_item2(
    item: Item4
) -> Item4:
    return item

@app.get("/items11/")
async def read_items11() -> list[Item4]:
    return [
        Item4(name="Porta Gun", price=42.0),
        Item4(name="Plumbus", price=32.0)
    ]

@app.post("/items3/", response_model=Item4)
async def create_item3(
    item: Item4
) -> Any:
    return item

@app.get("/items12/", response_model=list[Item4])
async def read_items12() -> Any:
    return [
        {"name": "Portal Gun", "price": 42.0},
        Item4(name="Plumbus", price=32.0)
    ]