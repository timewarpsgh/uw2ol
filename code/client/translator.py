# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from hashes.languages import chinese


class Translator():
    def __init__(self):
        self.to_langguage = 'CN'

    def translate(self, content):
        if self.to_langguage == 'CN':
            if content.lower() in chinese.dic:
                return  chinese.dic[content.lower()]
            elif content in chinese.dic:
                return chinese.dic[content]
            else:
                return content
        elif self.to_langguage == 'EN':
            return content

    def set_to_language(self, lan):
        self.to_langguage = lan

if __name__ == '__main__':
    trans = Translator()

    a = trans.translate('Register')
    print(a)