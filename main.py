from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import textwrap
import requests
from io import BytesIO


def get_image(url):
    """Tải ảnh từ URL và lưu vào file tạm."""
    try:
        response = requests.get(url, timeout=10)  # Timeout để tránh treo
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        image = Image.open(BytesIO(response.content))
        image_path = "./temp_downloaded.jpg"
        image.save(image_path)
        return image_path
    except requests.RequestException as e:
        print(f"Lỗi tải ảnh: {e}")
        return None


def resize_image(image, target_height):
    """Resize ảnh theo chiều cao target_height, giữ nguyên tỷ lệ."""
    aspect_ratio = image.width / image.height
    new_width = int(aspect_ratio * target_height)
    return image.resize((new_width, target_height))


def overlay_images(background_path, overlay_path, blur_path, logo_path, output_path, y_position=0, target_height=1233):
    """Ghép overlay vào ảnh nền, thêm blur và logo."""
    try:
        background = Image.open(background_path).convert("RGBA")
        overlay = Image.open(overlay_path).convert("RGBA")
        blur = Image.open(blur_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        # Resize ảnh
        overlay = resize_image(overlay, target_height)
        blur = resize_image(blur, target_height)
        logo = resize_image(logo, 200)

        # Căn giữa overlay
        x_position = (background.width - overlay.width) // 2
        position = (x_position, y_position)

        # Ghép ảnh
        background.paste(overlay, position, overlay)
        background.paste(blur, (0, 0), blur)
        background.paste(logo, (106, 1135), logo)

        # Lưu ảnh kết quả
        background.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi khi ghép ảnh: {e}")
        return None


def add_text_to_image(image_path, output_path, text, text_position=(50, 50),
                      text_color="white", font_path="arial.ttf", font_size=50,
                      max_width=None, line_spacing=10, show=False):
    """Thêm chữ vào ảnh với tự động xuống dòng."""
    try:
        image = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Tải font, dùng font mặc định nếu bị lỗi
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Lỗi tải font {font_path}, dùng font mặc định.")
            font = ImageFont.load_default()

        # Xử lý tự động xuống dòng
        if max_width is None:
            max_width = image.width - 100  # Giới hạn chiều rộng chữ

        lines = textwrap.wrap(text, width=int(max_width / font_size * 1.8))

        # Vẽ từng dòng
        x, y = text_position
        for line in lines:
            draw.text((x, y), line, fill=text_color, font=font)
            y += font_size + line_spacing  # Xuống dòng

        # Lưu ảnh kết quả
        image.save(output_path)
        if show:
            image.show()
        return output_path
    except Exception as e:
        print(f"Lỗi khi thêm chữ: {e}")
        return None


# MAIN
try:
    with open("text.txt", "r", encoding="utf-8") as file:
        amount = int(file.readline().strip())  # Đọc số lượng ảnh
        for i in range(amount):
            filename = f"./output/output{i}.png"
            link = file.readline().strip()
            text = file.readline().strip()

            # Tải ảnh từ URL
            overlay_path = get_image(link)
            if not overlay_path:
                print(f"Bỏ qua ảnh {i} do lỗi tải ảnh.")
                continue

            # Ghép ảnh
            merged_image = overlay_images(
                "./src/pic1.png", 
                overlay_path,
                "./src/blur.png",
                "./src/logo.png",
                filename, 
                y_position=0, 
                target_height=1233  
            )
            if not merged_image:
                print(f"Bỏ qua ảnh {i} do lỗi ghép ảnh.")
                continue

            # Viết text chính
            text_image = add_text_to_image(
                merged_image, 
                filename, 
                text=text, 
                text_position=(103, 1414),  
                text_color="white",
                font_path="seguibl.ttf",
                font_size=90,
                max_width=1100,  
                line_spacing=15  
            )
            if not text_image:
                print(f"Bỏ qua ảnh {i} do lỗi viết text.")
                continue

            # Viết ngày tháng
            add_text_to_image(
                filename, 
                filename,
                text=datetime.now().strftime("%d/%m/%Y"), 
                text_position=(108, 1914),  
                text_color="#FFC91D",
                font_path="GOTHICB.TTF",
                font_size=100,
                max_width=1100,  
                line_spacing=15,  
                show=True
            )

except FileNotFoundError:
    print("Lỗi: Không tìm thấy file text.txt!")
except ValueError:
    print("Lỗi: File text.txt không đúng định dạng!")
except Exception as e:
    print(f"Lỗi không xác định: {e}")
