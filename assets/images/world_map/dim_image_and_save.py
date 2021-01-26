import pygame


image = pygame.image.load('w_map regular tileset.png')
dim = 40

image.fill((dim, dim, dim), special_flags=pygame.BLEND_RGB_SUB)
pygame.image.save(image, '1.png')

image.fill((dim, dim, dim), special_flags=pygame.BLEND_RGB_SUB)
pygame.image.save(image, '2.png')

image.fill((dim, dim, dim), special_flags=pygame.BLEND_RGB_SUB)
pygame.image.save(image, '3.png')
