from PIL import Image, ImageDraw

# Tamanho do ícone
size = 256
img = Image.new('RGBA', (size, size), (245, 247, 252, 255))  # fundo claro

draw = ImageDraw.Draw(img)

# Círculo azul claro
draw.ellipse((32, 32, size-32, size-32), fill=(0, 168, 255, 255))
# Quadrado branco central
draw.rectangle((80, 80, size-80, size-80), fill=(255, 255, 255, 255))
# Sombra azul escuro à direita
shadow = Image.new('RGBA', (size, size), (0,0,0,0))
shadow_draw = ImageDraw.Draw(shadow)
shadow_draw.pieslice((32, 32, size-32, size-32), 315, 45, fill=(0, 98, 180, 180))
img = Image.alpha_composite(img, shadow)

img.save('icon_base.png')
img.save('icon.ico', format='ICO', sizes=[(64,64),(48,48),(32,32),(24,24),(16,16)])
print('Ícone gerado!')
