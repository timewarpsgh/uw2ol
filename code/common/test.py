from hashes.hash_items import hash_items


class Bag:
    """owned by role, contains a list of item_ids"""
    def __init__(self):
        self.container = {}

    def add_item(self, item_id):
        if self.get_all_items_count() < 20:
            if item_id in self.container:
                self.container[item_id] += 1
            else:
                self.container[item_id] = 1
        else:
            print('max 20 items!')

    def remove_item(self, item_id):
        self.container[item_id] -= 1
        if self.container[item_id] == 0:
            del self.container[item_id]


    def get_all_items_count(self):
        count = 0

        for k in self.container.keys():
            count += self.container[k]

        return count

    def get_all_items_dict(self):
        return self.container

class Item:
    def __init__(self, id):
        self.name = hash_items[id]['name']
        self.price = hash_items[id]['price']

if __name__ == '__main__':
    b = Bag()
    print(b.get_all_items_dict())
    print(b.get_all_items_count())
    b.add_item(0)

    b.add_item(1)
    b.add_item(2)
    b.add_item(1)
    for i in range(20):
        b.add_item(1)
    print(b.get_all_items_dict())
    print(b.get_all_items_count())

    b.remove_item(2)
    print(b.container)
    print(b.get_all_items_count())