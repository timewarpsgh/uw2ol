from PIL import Image


def make_white_bg_transparent(img_file):
    pic = Image.open(img_file)

    pic = pic.convert('RGBA')  # 转为RGBA模式
    width, height = pic.size
    array = pic.load()  # 获取图片像素操作入口
    for i in range(width):
        for j in range(height):
            pos = array[i, j]  # 获得某个像素点，格式为(R,G,B,A)元组
            # 如果R G B三者都大于240(很接近白色了，数值可调整)
            isEdit = (sum([1 for x in pos[0:3] if x > 240]) == 3)
            if isEdit:
                # 更改为透明
                array[i, j] = (255, 255, 255, 0)

    # 保存图片
    pic.save('result.png')


if __name__ == '__main__':
    make_white_bg_transparent('explosion.png')