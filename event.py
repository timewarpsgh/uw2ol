from hashes.hash_events import events_dict


class Event:
    def __init__(self, id):
        dic = events_dict[id]

        # place where the event is triggered
        self.port = dic['port']
        self.building = dic['building']

        # sequences of dialogues
        self.dialogues = dic['dialogues']

        # figure image
        self.figure_images = dic['figure_images']

        # action if any
        self.action_to_perform = None
        if 'action_to_perform' in dic:
            self.action_to_perform = dic['action_to_perform']