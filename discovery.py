from hashes.hash_villages import villages_dict


class Discovery:
    def __init__(self, discovery_id):
        # get dic
        dic = villages_dict[discovery_id]

        # assign attributes
        self.name = dic['name']
        self.x = dic['x']
        self.y = dic['y']
        self.latitude = dic['latitude']
        self.longitude = dic['longitude']

    