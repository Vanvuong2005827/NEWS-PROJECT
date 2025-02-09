from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import textwrap
import requests
from io import BytesIO
import re
from google import genai

def get_image(url):
    """Tải ảnh từ URL và lưu vào file tạm."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image_path = "./temp_downloaded.png"
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

        overlay = resize_image(overlay, target_height)
        blur = resize_image(blur, target_height)
        logo = resize_image(logo, 200)

        x_position = (background.width - overlay.width) // 2
        position = (x_position, y_position)

        background.paste(overlay, position, overlay)
        background.paste(blur, (0, 0), blur)
        background.paste(logo, (106, 1135), logo)

        if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg") or output_path.lower().endswith(".png"):
            background.convert("RGB").save(output_path, "JPEG")
        else:
            background.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi khi ghép ảnh: {e}")
        return None

def add_text_to_image(image_path, output_path, text, text_position=(50, 50),
                     text_color="white", font_path="arial.ttf", font_size=50,
                     max_width=None, line_spacing=10):
    """Thêm chữ vào ảnh với định dạng màu cho text trong dấu {} và giữ nguyên cụm từ."""
    try:
        image = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Lỗi tải font {font_path}, dùng font mặc định.")
            font = ImageFont.load_default()

        if max_width is None:
            max_width = image.width - 100

        # Định nghĩa line_height
        line_height = font_size + line_spacing

        # Tách text thành các phần theo dấu {}
        parts = re.split(r'({[^}]*})|(\s+)', text)
        parts = [p for p in parts if p is not None and p.strip()]

        x, y = text_position
        current_y = y
        current_x = x
        current_line = []
        current_line_width = 0

        for part in parts:
            is_special = part.startswith('{') and part.endswith('}')
            
            # Tính toán chiều rộng của phần text
            if is_special:
                part_text = part[1:-1]  # Bỏ dấu {}
                part_width = draw.textlength(part_text, font=font)
            else:
                part_text = part
                part_width = draw.textlength(part, font=font)

            # Kiểm tra xem có cần xuống dòng không
            if current_x + part_width > x + max_width:
                # Vẽ dòng hiện tại
                draw_line_position = x
                for line_part, line_special in current_line:
                    color = "#FFC91D" if line_special else text_color
                    draw.text((draw_line_position, current_y), line_part, fill=color, font=font)
                    draw_line_position += draw.textlength(line_part + " ", font=font)
                
                # Xuống dòng mới
                current_y += line_height
                current_x = x
                current_line = []
                current_line_width = 0

            # Thêm phần text vào dòng hiện tại
            if is_special:
                current_line.append((part_text, True))
            else:
                current_line.append((part_text, False))
            current_x += part_width + draw.textlength(" ", font=font)
            current_line_width += part_width + draw.textlength(" ", font=font)

        # Vẽ dòng cuối cùng nếu có
        if current_line:
            draw_line_position = x
            for line_part, line_special in current_line:
                color = "#FFC91D" if line_special else text_color
                draw.text((draw_line_position, current_y), line_part, fill=color, font=font)
                draw_line_position += draw.textlength(line_part + " ", font=font)

        image.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi khi thêm chữ: {e}")
        return None

def get_ai_formatted_text(text):
    """Lấy text đã được format từ AI."""
    try:
        client = genai.Client(api_key="AIzaSyDaQhCfd8t8ZrZ029sTHElzylZavE5SWPM")
        prompt = f"Bạn là một chuyên gia tóm tắt 20 năm kinh nghiệm. Hãy nhấn mạnh các từ ngữ trong nội dùng sau đây  '{text}' từ nào cần nhấn mạnh chỉ cần để là {{từ ngữ cần nhấn mạnh}}. Chỉ được nhấn mạnh tối đa 20% số chữ trong câu (bắt buộc phải 20%). Hãy xuất ra kết quả luôn ( không có các dẫu * hay đóng ngoặc gì hết) "
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi gọi AI: {e}")
        return text

# MAIN
try:
    with open("text.txt", "r", encoding="utf-8") as file:
        amount = int(file.readline().strip())
        for i in range(amount):
            filename = f"./output/output{i}.png"
            link = file.readline().strip()
            original_text = file.readline().strip()
            
            # Lấy text được format từ AI
            if i == 0:
                formatted_text = original_text
            else:
                formatted_text = get_ai_formatted_text(original_text)
            
            # Ghi đè lại text.txt với text mới từ AI
            with open("text.txt", "r", encoding="utf-8") as file_read:
                lines = file_read.readlines()
            
            lines[2 + i * 2] = formatted_text + "\n"  # 2 + i * 3 là vị trí của dòng text

            overlay_path = get_image(link)
            if not overlay_path:
                print(f"Bỏ qua ảnh {i} do lỗi tải ảnh.")
                continue

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

            # Sử dụng text đã được format từ AI
            text_image = add_text_to_image(
                merged_image, 
                filename, 
                text=formatted_text,
                text_position=(103, 1414),
                text_color="white",
                font_path="seguibl.ttf",
                font_size=95,
                max_width=1100,
                line_spacing=15
            )
            if not text_image:
                print(f"Bỏ qua ảnh {i} do lỗi viết text.")
                continue
            if i == 0:
                add_text_to_image(
                    filename, 
                    filename,
                    text=datetime.now().strftime("%d/%m/%Y"), 
                    text_position=(108, 1960),
                    text_color="#FFC91D",
                    font_path="CENTURY.TTF",
                    font_size=95,
                    max_width=1100,
                    line_spacing=15
                )
    print("Done")

except FileNotFoundError:
    print("Lỗi: Không tìm thấy file text.txt!")
except ValueError:
    print("Lỗi: File text.txt không đúng định dạng!")
except Exception as e:
    print(f"Lỗi không xác định: {e}")
