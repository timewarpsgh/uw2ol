events_dict = {
    1: {
        'port': 'London',
        'building': 'any',
        'dialogues': [
            ['someone', "John, what are you doing here? Head to the port quickly. Your father is back."],
            ['I', "He's back? Alright. I'll be there right away. Thank you."],
        ],
        'figure_images':{
            'I': [1,1],
            'someone': [6,3],
        }
    },

    2: {
        'port': 'London',
        'building': 'harbor',
        'dialogues': [
            ['navy guy', "You are John, right?"],
            ['I', "Yes, I am."],
            ['navy guy', "I'm the captain of Eagle... You two look so"
                         " much alike... I'm sorry to inform you that your"
                         " father, carpenter on board Eagle, died bravely during"
                         " battle with the Spanish Navy. He was buried at sea. "
                         "We found this letter in his wardrobe, "
                         "which must have been written in advance."
                         " Here, take it and be strong."],
            ['I', "Thank you."],
            ['the letter', "Dear John, my son, when you are reading this letter," 
                        "that means I've gone to the moon to meet your"
                        " mom. Poor kid. I will no longer be able to guide you nor protect you. "
                           "I will no longer kick you in an attempt to"
                        " get you right. You are on yourself now. I have not been a successful"
                        " sailor, serving as a carpenter for the majority of my life. Don't be like me."
                        ],
            ['the letter', "I saved my wage as much as possible so that the figure in my "
                           "bank account might some day be able to fund"
                        " a ship. Now, it's yours. Use it wisely."],
            ['the letter', "Do you remember Tommy Branson? "
                            "He's father is an old friend of mine. "
                            "I believe he'll be interested in joining you. "
                            "He knows the way in the water as well as any professional navigator. "
                            "He's likely still working at the bar in Amsterdam."],
        ],
        'figure_images': {
            'I': [1, 1],
            'navy guy': [10, 2],
            'the letter': [1, 1],
        }
    },

    3: {
        'port': 'Amsterdam',
        'building': 'bar',
        'dialogues': [
            ['I', "Excuse me, is Tommy Branson working here?"],
            ['Tommy', "Hey, John? How are you? Taking a tour here?"],
            ['I', "I'm OK. I'm here for you."],
            ['Tommy', "For me?"],
            ['I', "Yes. I bought a ship. Do you want to sail with me?"],
            ['Tommy', "You got a ship? Well... Why not? I've done enough bar tending."],
        ],
        'figure_images': {
            'I': [1, 1],
            'Tommy': [16, 4],
        },
        'action_to_perform':['hire_mate', [38]],
    },

}

if __name__ == '__main__':
    a = events_dict[1]
    print(a)
