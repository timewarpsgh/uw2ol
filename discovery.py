from hashes.hash_villages import villages_dict

import random


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

        # not yet all done

            # defaults
        self.description = 'discovery description'
        self.image_x = random.randint(1, 16)
        self.image_y = random.randint(1, 5)

            # if have set
        if 'description' in dic:
            self.description = dic['description']
        if 'image_x' in dic:
            self.image_x = dic['image_x']
        if 'image_y' in dic:
            self.image_y = dic['image_y']

    