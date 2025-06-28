from PIL import Image

# 1) open your png
img = Image.open("resources/icon.png")

# 2) save an .ico containing multiple sizes
img.save(
    "resources/icon.ico",
    format="ICO",
    sizes=[ (256,256),
            (128,128),
            (64,64),
            (48,48),
            (32,32),
            (16,16) ]
)
