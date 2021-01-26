


image = pygame.image.load(my_imagename)
brighten = 128
image.fill((brighten, brighten, brighten), special_flags=pygame.BLEND_RGB_SUB)

image.save("sea_img.png")