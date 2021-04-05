# prepare list
en = ['Balm', 'Lime Juice', 'Rat Poison', 'Quadrant', 'Sextant', 'Theodolite', 'Pocket Watch', 'Telescope', 'Cat', 'Tax Free Permit (E)', 'Tax Free Permit (H)', 'Tax Free Permit (I)', 'Tax Free Permit (P)', 'Tax Free Permit (S)', 'Tax Free Permit (T)', 'Candleholder', 'Crown of Glory', 'Garnet Brooch', 'Gold Bracelet', 'Malachite Box', 'Mermaid Bangle', 'Ruby Scepter', 'Aqua Tiara', 'China Dress', 'Circlet', 'Ermine Coat', 'Peacock Fan', 'Platinum Comb', 'Silk Scarf', 'Silk Shawl', 'Velvet Coat', 'Leather Armor', 'Chain Mail', 'Half Plate', 'Plate Mail', "Errol's Plate", 'Crusader Armor (*)', 'Short Saber', 'Scimitar', 'Japanese Sword', 'Saber', 'Magic Muramasa(*)', "Siva's Sword(*)", 'Flamberge', 'Rapier', 'Epee', 'Estock', 'Crusader Sword (*)', 'Cutlass', 'Broad Sword', 'Blue Crescent(*)', 'Claymore', 'Golden Dragon(*)', 'Treasure Box', 'Diamond Ring']
cn = ['香脂','酸橙汁','老鼠毒','象限','六分仪','经纬仪','怀表','望远镜','猫','免税许可证（E）','免税许可证（H）','免税许可证（I）','免税许可证（P）','免税许可证（S）','免税许可证（T）','烛台','荣耀之冠','石榴石胸针','金手镯','孔雀石盒','美人鱼手镯','红宝石权杖','水族头饰','中国裙','圆环','貂皮大衣','孔雀扇','白金梳子','丝巾','丝巾','丝绒大衣','皮甲','链甲','半板','板甲','埃罗尔板','十字军盔甲（*）','短刀','弯刀','日本剑','军刀','魔法村上春树（*）','湿婆之剑（*）','弗拉姆伯格','剑器','重剑','埃斯托克','十字军之剑（*）','弯刀','宽剑','蓝新月（*）','克莱默','金龙（*）','宝箱','钻戒']

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

