from app.pricing import calc_total


def create_order(order):
    items = order["items"]
    total = calc_total(items, order["discount"])  # KeyError when "discount" is absent
    return {"items": items, "total": total}
