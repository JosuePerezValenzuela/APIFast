def get_full_name(first_name: str, last_name: str):
    full_name = first_name.title() + last_name.title()
    print(full_name)

def get_name_with_age(name: str, age: int):
    name_with_age = name + " is this old: " + str(age)
    return name_with_age

def process_items(items: list[str]):
    for item in items:
        print (item.capitalize)

def process_items2(items_t: tuple[int, int, str], items_s: set[bytes]):
    return items_t, items_s

def process_items3(prices: dict[str, float]):
    for item_name, item_price in prices.items():
        print(item_name)
        print(item_price)

def process_item(item: int | str):
    print(item)

def say_hi(name: str | None = None):
    if name is not None:
        print(f"hey {name}!")
    else:
        print("Hello world")
