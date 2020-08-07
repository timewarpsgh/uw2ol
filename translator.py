from hashes.languages import chinese


class Translator():
    def __init__(self):
        self.to_langguage = 'CN'

    def translate(self, content):
        if self.to_langguage == 'CN':
            return  chinese.dic[content.lower()]
        elif self.to_langguage == 'EN':
            return content


if __name__ == '__main__':
    trans = Translator()

    a = trans.translate('Register')
    print(a)