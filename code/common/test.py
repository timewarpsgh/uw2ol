# prepare list
en = ['John', 'Tommy Branson', 'Charlie Stephens', 'Amy Clement', 'Ambroise Einger', 'Amerigo Bassio', 'Anthony Morgan', 'Antoine Fitch', 'Antonio Pintado', 'Benito Gomez', 'Bernando Sanchez', 'Carmine Ragussa', 'Cisco Alvarez', 'Cizzario Fedeliti', 'Dante Peleira', 'Diego Fagundes', 'Fernan Pinto', 'Fritz Ramsey', 'Irma Gunter', 'Fabian Bernal', 'Francis Fielding', 'Raymond Brewster', 'Arthur Oliver', 'Gary Buck', 'Poppy Chapman', 'Peter Hobson', 'Dwight Stephens', 'Donald Russell', 'Edgar Wheeler', 'Boris Dutt', 'Saxon Wild', 'Ken Harrison', 'Erin Howard', 'Rudolf Flynn', 'Tim Hill', 'Mark Rhys', 'Paul Lindberg', 'Al Fasi', 'Carl Dupont', 'Wade Galbraith', 'Bernard Stevenson', 'Lawrence Thorndike', 'Abraham Pearson', 'Noah Holt', 'Duke Stowe', 'Antony Cooper', 'Perry Frederick', 'Kirk Churchill', 'York Wagner', 'Lester Walkley']
cn = ['约翰','汤米·布兰森','查理·斯蒂芬斯','艾米·克莱门特','安布罗伊斯·艾因格','阿梅里戈·巴西奥','安东尼·摩根','安托万·菲奇','安东尼奥·平塔多','贝尼托·戈麦斯','伯南多·桑切斯','卡门·拉古萨','思科·阿尔瓦雷斯','西扎里奥·费德丽蒂','但丁·佩莱拉','迭戈·法贡德','费尔南·平托','弗里茨·拉姆齐','伊尔玛·冈特','法比安·贝尔纳','弗朗西斯·菲尔丁','雷蒙德·布鲁斯特','亚瑟·奥利弗','加里·巴克','波比·查普曼','彼得·霍布森','德怀特·斯蒂芬斯','唐纳德·拉塞尔','埃德加·惠勒','鲍里斯·杜特','撒克逊·怀尔德','肯·哈里森','艾琳·霍华德','鲁道夫·弗林','蒂姆·希尔','马克·里斯','保罗·林德伯格','阿尔·法西','卡尔·杜邦','韦德·加尔布雷斯','伯纳德·史蒂文森','劳伦斯·劳伦斯''桑代克','亚伯拉罕·皮尔森','诺亚·霍尔特','杜克·斯托','安东尼·库珀','佩里·弗雷德里克','柯克·丘吉尔','约克·瓦格纳','莱斯特·沃克利']
# do
# if len(en) == len(cn):

for id, item in enumerate(en):
    print(f"'{item}'", ":", f"'{cn[id]}',")

# else:
#     print("the 2 lists have diff length!")
#     print(len(en), len(cn))
# for id, item in enumerate(en):
#     print(f"'{item}'", ":", f" ,")
# print(len(en), len(cn))

