ports_en = ['Lisbon', 'Seville', 'Istanbul', 'Barcelona', 'Algiers', 'Tunis', 'Valencia', 'Marseille', 'Genoa', 'Pisa', 'Naples', 'Syracuse', 'Palma', 'Venice', 'Ragusa', 'Candia', 'Athens', 'Salonika', 'Alexandria', 'Jaffa', 'Beirut', 'Nicosia', 'Tripoli', 'Kaffa', 'Azov', 'Trebizond', 'Ceuta', 'Bordeaux', 'Nantes', 'London', 'Bristol', 'Dublin', 'Antwerp', 'Amsterdam', 'Copenhagen', 'Hamburg', 'Oslo', 'Stockholm', 'Lubeck', 'Danzig', 'Riga', 'Bergen', 'Caracas', 'Cartegena', 'Havana', 'Margarita', 'Panama', 'Porto Velho', 'Santo Domingo', 'Veracruz', 'Jamaica', 'Guatemala', 'Pernambuco', 'Rio de Janeiro', 'Maracaibo', 'Santiago', 'Cayenne', 'Madeira', 'Santa Cruz', 'San Jorge', 'Bissau', 'Luanda', 'Argin', 'Bathurst', 'Timbuktu', 'Abidjan', 'Sofala', 'Malindi', 'Mogadishu', 'Mombasa', 'Mozambique', 'Quelimane', 'Aden', 'Hormuz', 'Massawa', 'Cairo', 'Basra', 'Mecca', 'Quatar', 'Shiraz', 'Muscat', 'Diu', 'Cochin', 'Ceylon', 'Amboa', 'Goa', 'Malacca', 'Ternate', 'Banda', 'Dili', 'Pasei', 'Sunda', 'Calicut', 'Bankao', 'Zeiton', 'Macao', 'Hanoi', 'Changan', 'Sakai', 'Nagasaki', 'Hekla', 'Narvik', 'Cape Town', 'Belgrade', 'Tamatave', 'Dikson', 'Lushun', 'Leveque', 'Mindanao', 'Tiksi', 'Ezo', 'Geelong', 'Guam', 'Moresby', 'Korf', 'Wanganui', 'Suva', 'Nome', 'Naalehu', 'Tahiti', 'Juneau', 'Coppermine', 'Santa Barbara', 'Churchill', 'Callao', 'Valparaiso', 'Mollendo', 'Cape Cod', 'Montevideo', 'Forel']
ports_cn = ['里斯本','塞维利亚','伊斯坦布尔','巴塞罗那','阿尔及尔','突尼斯','瓦伦西亚','马赛','热那亚','比萨','那不勒斯','锡拉丘兹','帕尔马','威尼斯','拉古萨','坎迪亚','雅典','萨洛尼卡','亚历山大','雅法','贝鲁特','尼科西亚','的黎波里','卡法','亚速尔夫','特雷比松','休达','波尔多','南特','伦敦','布里斯托','都柏林','安特卫普','阿姆斯特丹','哥本哈根','汉堡','奥斯陆','斯德哥尔摩','吕贝克','丹泽','里加','卑尔根','加拉加斯','卡特里娜','哈瓦那','玛格丽塔','巴拿马','维略港','圣多明各','维拉克鲁斯','牙买加','危地马拉','伯南布哥','里约热内卢','马拉开波','圣地亚哥','卡宴','马德拉','圣克鲁斯','圣乔治','比绍','罗', '阿尔金','巴瑟斯特','廷巴克图']
cn_1 = ['阿比让','索法拉','马林迪','摩加迪沙','蒙巴萨','莫桑比克','克利马内','亚丁','霍尔木兹','马萨瓦','开罗','巴士拉','麦加','卡塔尔','设拉子','马斯喀特','迪乌','科钦','锡兰','安博亚','果阿','马六甲','特内','班达','迪力','帕塞','翼它','卡利卡特','班考','泉州','澳门','河内','长安','酒井','长崎','赫克拉','纳尔维克','开普敦','贝尔格莱德','塔马塔夫','迪克森','旅顺','列夫奎','棉兰老','提克西','埃佐','吉隆','关岛','莫尔斯比','科尔夫','旺加努伊','苏瓦','诺姆','纳阿勒胡','塔希提','朱诺','铜人','圣巴巴拉','丘吉尔','卡劳','瓦尔帕莱索','蒙得维的亚','弗雷尔','蒙拖维迪亚','法雷尔']

all_cn_ports = []
for item in ports_cn:
    all_cn_ports.append(item)
for item in cn_1:
    all_cn_ports.append(item)

print(len(all_cn_ports))

for id, item in enumerate(ports_en):
    print(f"'{item}'", ":", f"'{all_cn_ports[id]}',")


