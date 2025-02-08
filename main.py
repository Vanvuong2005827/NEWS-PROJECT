from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import textwrap
import requests
from io import BytesIO


def getImage(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    downimg = "./pngweb.jpg"
    image.save(downimg)
    return downimg


def resize_image(image, target_height):
    """Resize ảnh theo chiều cao target_height, giữ nguyên tỷ lệ."""
    aspect_ratio = image.width / image.height
    new_width = int(aspect_ratio * target_height)  # Tính chiều rộng mới
    return image.resize((new_width, target_height))

def overlay_images(background_path, overlay_path, blur_path, logo_path, output_path, y_position=0, target_height=1233):
    """Ghép ảnh overlay vào giữa ảnh nền."""
    background = Image.open(background_path).convert("RGBA")
    overlay = Image.open(overlay_path).convert("RGBA")
    blur = Image.open(blur_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")




    # Resize overlay theo chiều cao mong muốn
    overlay = resize_image(overlay, target_height)
    blur = resize_image(blur, target_height)
    logo = resize_image(logo, 200)



    # Căn giữa overlay theo chiều ngang
    x_position = (background.width - overlay.width) // 2
    position = (x_position, y_position)

    # Dán ảnh overlay lên ảnh nền
    background.paste(overlay, position, overlay)
    background.paste(blur, (0,0), blur)
    background.paste(logo, (106,1135), logo)


    # Lưu ảnh kết quả
    background.save(output_path)
    return output_path  # Trả về đường dẫn ảnh mới

def add_text_to_image(image_path, output_path, text, text_position=(50, 50),
                      text_color="white", font_path="arial.ttf", font_size=50,
                      max_width=None, line_spacing=10, show = False):
    """Viết chữ lên ảnh (tự động xuống dòng nếu quá dài)."""
    image = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(image)

    # Tải font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # Xử lý tự động xuống dòng
    if max_width is None:
        max_width = image.width - 100  # Mặc định giới hạn chiều rộng chữ

    # Chia nhỏ dòng chữ theo độ rộng tối đa
    lines = textwrap.wrap(text, width=int(max_width / font_size * 1.8))

    # Ghi từng dòng lên ảnh
    x, y = text_position
    for line in lines:
        draw.text((x, y), line, fill=text_color, font=font)
        y += font_size + line_spacing  # Xuống dòng

    # Lưu ảnh kết quả
    image.save(output_path)
    if show:
        image.show()

#MAIN
file = open("text.txt", "r")
amount = file.readline()
for i in range(int(amount)):
    filename = "output" + str(i) + ".png"
    link = file.readline()
    text = file.readline()

    merged_image = overlay_images(
        "./src/pic1.png", 
        getImage(link),
        "./src/blur.png",
        "./src/logo.png",
        filename, 
        y_position=0,  # Điều chỉnh vị trí overlay
        target_height=1233  # Chiều cao ảnh overlay
    )

    # 2️⃣ Viết chữ lên ảnh đã ghép
    text_image = add_text_to_image(
        merged_image, 
        filename, 
        text=text, 
        text_position=(103, 1414),  # Vị trí chữ (x, y)
        text_color="white",
        font_path="seguibl.ttf",
        font_size=80,
        max_width=1100,  # ✅ Giới hạn chiều rộng chữ để tự động xuống dòng
        line_spacing=15  # ✅ Khoảng cách giữa các dòng chữ
    )

    add_text_to_image(
        filename, 
        filename,
        text=datetime.now().strftime("%d/%m/%Y"), 
        text_position=(103, 1914),  # Vị trí chữ (x, y)
        text_color="#FFC91D",
        font_path="GOTHICB.TTF",
        font_size=80,
        max_width=1100,  # ✅ Giới hạn chiều rộng chữ để tự động xuống dòng
        line_spacing=15,  # ✅ Khoảng cách giữa các dòng chữ
        show = True
    )
