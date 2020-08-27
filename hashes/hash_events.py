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
            ['I', "He? .... Thank you."],
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
            ['Tommy', "Captain... I wish to visit my teacher living in the church in Copenhagen before we embark on our jouney. "
                      "Could you help me with that?"],
            ['I', "Sure. Let's head to Copenhagen."],
        ],
        'figure_images': {
            'I': [1, 1],
            'Tommy': [16, 4],
        },
        'action_to_perform':['hire_mate', [2]],
    },

    4: {
        'port': 'Copenhagen',
        'building': 'church',
        'figure_images': {
            'Garry': [7, 2],
            'Lady': [4, 2],
            'Tommy': [16, 4],
                          },
        'dialogues': [
            ['Tommy', "Excuse me, is Mr. Garry still living here?"],
            ['Lady', "Yes. But I'm afraid he's not in good condition to see anyone."],
            ['Tommy', "I was one of his students. My name is Tommy Branson. "
                      "Please tell him that I wish to see him."],
            ['Lady', "Alright. Please wait for a second..."],
            ['Lady', "Coming in."],
            ['Tommy', "Mr. Garry, how are you?"],
            ['Garry', "Oh, Tommy, I remember you. You were among my best students. Look how you've grown. "
                      "How come you've never come back to see me?"],
            ['Tommy', "I wantted to, just didn't feel successful enough to see you. "
                      "Now I'm about to start a jouney with a friend of mine. We got a ship. "
                      "I've just come to say hi before we leave. What's wrong with your leg, Mr. Garry?"],
            ['Garry', "I'm not as young as when you were my student. My legs are failing as are my eyes. "
                      "You guys got a ship? How I wish I could join you. Taught geography for my entire life... "
                      "Famarilar with every part of the map, yet have never been outside of this little town. "],
            ['Tommy', "We fished and examed every stream in the town, remember?  "],
            ['Garry', "Yes, we did. Anyway, I wish you all the best. "
                      "I look forward to seeing your discoveries via your reports. "
                      "Don't forget to report though."],
            ['Tommy', "I'll try my best. See you Mr. Garry."],
                      ],

    },

    5: {
        'port': 'Copenhagen',
        'building': 'any',
        'figure_images': {
            'I': [1, 1],
            'Tommy': [16, 4],
        },
        'dialogues': [
            ['I', "Tommy, are you going to leave to explore the world on your own?"],
            ['Tommy', "No, I'll stay with you. I like being with you. "
                      "Just remember to do some exploration when you have time."],

            ['I', "I promise I will. But for the moment, I guess I'm interested in the Navy draft."],
            ['I', "Did you see the ad? It basicly says the Navy's in urgent need of personel. "
                  "Anyone interested is encouraged to apply at the Palace in London."],
            ['Tommy', "Sounds like a good idea. After we join the Navy, We'll be safe to explore anywhere. "
                      "Let's move then."],
        ],
    },

    6: {
        'port': 'London',
        'building': 'palace',
        'figure_images': {
            'I': [1, 1],
            'Tommy': [16, 4],
            'Officer': [14, 3],
        },
        'dialogues': [
            ['I', "Sir, we heard the Navy is seeking men to join. Can we apply?"],
            ['Officer', "You two? Sure. Fill this up..."],
            ['Officer', "Hmm... It seems that none of you have much experience."],
            ['Tommy', "We are hard working. Please have us."],
            ['Officer', "I'm afraid you don't qualify to fight for England on any of our battle ships. "
                        "But, we do have two bar tending positions at our naval base. Are you interested? "],
            ['Tommy', "Bar tending???"],
            ['I', "Yeah...Sir, please allow us some time to consider."],
            ['Officer', "OK. Let me know when you are ready."],
            ['Tommy', "Captain, I need a drink."],
            ['I', "I understand. I also need a drink."],
        ],
    },

    7: {
        'port': 'London',
        'building': 'bar',
        'action_to_perform':['hire_mate', [3]],

        'figure_images': {
            'I': [1, 1],
            'Tommy': [16, 4],
            'Charlie': [15, 3],
            'Girl': [6, 7],
            'Guy': [8, 1],
        },
        'dialogues': [
            ['I', "Hi, what's the most unexpensive drink here?"],
            ['Girl', "un... That'll be our beer with water."],
            ['I', "Two dozen, please."],
            ['Girl', "Wait a second ..."],
            ['Guy', "Hey you two. Your beer with water."],
            ['I', "... Thank you. Where... Never mind..."],
            ['Tommy', "I want more."],
            ['I', "No you don't."],
            ['Tommy', "I want more."],
            ['I', "You are drunk man. Look at you!"],
            ['Tommy', "No I'm not."],
            ['Tommy', "Bar tending? Am I suppose to bar tend my whole life? I'm a born bar tender."],
            ['Charlie', "You surely are."],
            ['I', "Who hell are you? Quit speaking to my friend like that!"],
            ['Charlie', "Oops... Sorry. I thought I was just thinking."],
            ['Charlie', "I'm Charlie. Charlie Stephens."],
            ['Charlie', "I saw you at the palace earlier. You guys also got rejected?"],
            ['Charlie', "That idiot officer... Said I'm too old."],
            ['I', "I think he's right. They want young men."],
            ['Charlie', "I'm 24!"],
            ['I', "You look like 42."],
            ['I', "You should have told him you are 24."],
            ['Charlie', "I did. Then he said my face's too big to fit in a crowded ship."],
            ['I', "Charlie..."],
            ['Charlie', "Huh?"],
            ['I', "He's right."],
            ['Charlie', "Idiot officer couldn't see my strength. I can punch him to death with my little finger."],
            ['I', "I can see that. So, would you like to join us? We only have a small ship though."],
            ['Charlie', "You are inviting me? Yes, you are inviting me. "
                        "Dear mum, someone's inviting me! "
                        "I've been seeking a job for a long time."],
            ['Charlie', "I'm in."],
            ['I', "Welcome aboard!"],
        ],
    },

    8: {
        'port': 'London',
        'building': 'any',
        'figure_images': {
            'I': [1, 1],
            'Charlie': [15, 3],
            'Tommy': [16, 4],
        },
        'dialogues': [
            ['Charlie', "Captain, this ship's too small to fit me."],
            ['I', "I know I know..."],
            ['Tommy', "But we can't afford a ship any bigger than this one."],
            ['Charlie', "Perhaps we shall sail for Venice. I heard there are many rich merchants."],
            ['Charlie', "I'm going to punch a few to death and inherit their wealth. "],
            ['I', "... ... Yeah. Let's head to Venice."],
        ],
    },

    9: {
        'port': 'Venice',
        'building': 'any',
        'figure_images': {
            'I': [1, 1],
            'Charlie': [15, 3],
        },
        'dialogues': [
            ['Charlie', "All merchants go to the market."],
            ['I', "Right. Let's go."],
        ],
    },

    10: {
        'port': 'Venice',
        'building': 'market',
        'figure_images': {
            'I': [1, 1],
            'Charlie': [15, 3],
            'Amy': [6, 8],
            'Seller': [12, 1],
            'Tommy': [16, 4],
        },
        'dialogues': [
            ['Seller', "Look, miss. You have eyes. These are the best apples you can ever find here."],
            ['Amy', "I don't dout that. Can you give me a more reasonable price? 5 is too much."],
            ['Amy', "People in my town won't be able to afford it. "
                    "I wish only to provide healthy food for everyone."],
            ['Seller', "...Alright. I'll make it 4, if you are buying 100 of them."],
            ['Amy', "That's very kind of you. I'll buy 150 if you make it 3."],
            ['Seller', "3? Are you nuts? I'd go bankrupt before you return to your store."],
            ['Amy', "This isn't my first time here. Everyone in my town love your apples. "
                    "I'm pretty sure the demand will continue so long as you are alive. "
                    "Even I myself eat apples daily."],
            ['Seller', "No, I can't. I have a family to raise, Miss."],
            ['Amy', "Your beard looks cute."],
            ['Seller', "Don't flatter me. That dosen't work. "],
            ['Charlie', "I'll punch you to death if that dosen't work. "],
            ['Seller', "... Please... Don't... 3. I'll make it 3. "],
            ['Amy', "Thank you, Sir!"],
            ['Charlie', "My pleasure. "],
            ['I', "You did right, Charlie. I was worried you might puch the miss."],
            ['Tommy', "The market place's closing soon. We'd better find a place for the night."],
        ],
    },

    11: {
        'port': 'Venice',
        'building': 'inn',
        'figure_images': {
            'I': [1, 1],
            'Charlie': [15, 3],
            'Amy': [6, 8],
            'Tommy': [16, 4],
        },
        'dialogues': [
            ['Seller', "Look, Miss. You have eyes. These are the best apples you can ever find here."],
            ['Amy', "I don't dout that. Can you give me a more reasonable price? 5 is too much."],

        ],
    },

}

if __name__ == '__main__':
    a = events_dict[1]
    print(a)
