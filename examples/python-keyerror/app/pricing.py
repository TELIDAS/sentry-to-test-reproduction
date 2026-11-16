def calc_total(items, discount):
    subtotal = sum(i["price"] for i in items)
    return subtotal - discount
