ITEMS_PER_PAGE = 10

def paginate_items(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    formatted_items = [item.format() for item in selection]
    current_items = formatted_items[start:end]

    return current_items