# prepare list
en = ['Clove', 'Cinnamon', 'Pepper', 'Nutmeg', 'Pimento', 'Ginger', 'Tobacco', 'Tea', 'Coffee', 'Cacao', 'Sugar', 'Cheese', 'Fish', 'Grain', 'Olive Oil', 'Wine', 'Rock Salt', 'Silk', 'Cotton', 'Wool', 'Flax', 'Cotton Cloth', 'Silk Cloth', 'Wool Cloth', 'Velvet', 'Linen Cloth', 'Coral', 'Amber', 'Ivory', 'Pearl', 'Tortoise Shell', 'Gold', 'Silver', 'Copper Ore', 'Tin Ore', 'Iron Ore', 'Art', 'Carpet', 'Musk', 'Perfume', 'Glass Beads', 'Dye', 'Porcelain', 'Glassware', 'Arms', 'Wood']
cn = ['丁香','肉桂','胡椒','肉豆蔻','青椒','生姜','烟草','茶','咖啡','可可','糖','奶酪','鱼','谷物','橄榄油','葡萄酒','岩盐','丝绸','棉花','羊毛','亚麻','棉布','棉布','羊毛布','丝绒','亚麻布','珊瑚','琥珀','象牙','珍珠','玳瑁甲','黄金','白银','铜矿石','锡矿石','铁矿石','艺术品','地毯','麝香','香水','玻璃珠','染料','瓷器','玻璃器皿','武器','木头']

# do
if len(en) == len(cn):
    for id, item in enumerate(en):
        print(f"'{item}'", ":", f"'{cn[id]}',")
else:
    print("the 2 lists have diff length!")


