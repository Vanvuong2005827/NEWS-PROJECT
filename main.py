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
        background.paste(logo, (90, 1135), logo)

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
                     max_width=1200, line_spacing=10):
    """Thêm chữ vào ảnh với vùng giới hạn, tự động xuống dòng bằng text box."""
    try:
        image = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Lỗi tải font {font_path}, dùng font mặc định.")
            font = ImageFont.load_default()

        if max_width is None:
            max_width = image.width - text_position[0] * 2  # Đặt giới hạn theo ảnh

        x, y = text_position

        # Tách văn bản thành các phần, giữ nguyên các cụm từ trong {}
        parts = []
        start = 0
        while True:
            # Tìm vị trí của dấu {
            brace_start = text.find("{", start)
            if brace_start == -1:
                # Nếu không còn dấu {, thêm phần còn lại của văn bản
                parts.append((text[start:], text_color))
                break
            # Thêm phần trước dấu {
            parts.append((text[start:brace_start], text_color))
            # Tìm vị trí của dấu }
            brace_end = text.find("}", brace_start)
            if brace_end == -1:
                # Nếu không có dấu }, coi toàn bộ phần còn lại là cụm từ
                parts.append((text[brace_start:], "#fada23"))
                break
            # Thêm cụm từ trong {}
            parts.append((text[brace_start + 1:brace_end], "#fada23"))
            start = brace_end + 1

        # Xử lý từng phần
        for part, color in parts:
            words = re.findall(r'\w+|\W+', part)
            for word in words:
                # Kiểm tra xem thêm từ này có vượt quá max_width không
                test_line = word
                test_width = draw.textlength(test_line, font=font)
                if x + test_width > max_width:
                    # Nếu vượt quá, xuống dòng mới
                    x = text_position[0]
                    y += font_size + line_spacing

                # Vẽ từ hiện tại với màu tương ứng
                draw.text((x, y), word, fill=color, font=font)
                x += test_width 

        image.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi khi thêm chữ: {e}")
        return None


def get_ai_formatted_text(text):
    """Lấy text đã được format từ AI."""
    try:
        client = genai.Client(api_key="AIzaSyDaQhCfd8t8ZrZ029sTHElzylZavE5SWPM")
        prompt = f"Bạn là một chuyên gia xử lý ngôn ngữ. Nhiệm vụ của bạn là chọn một vài từ quan trọng trong đoạn văn và đặt chúng trong {{ }} để nhấn mạnh. Hãy ưu tiên danh từ riêng (tên người, địa danh, công ty), số liệu quan trọng (ngày tháng, năm, giá tiền) và từ khóa chính giúp làm rõ nội dung. Đảm bảo giữ nguyên nội dung, ngữ pháp và chỉ sử dụng {{ }} để đánh dấu mà không thêm bất kỳ ký hiệu nào khác (lưu lý kĩ điều này). Hãy áp dụng quy tắc này cho đoạn văn sau và xuất ra kết quả: '{text}'."
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        pretext = response.text
# Kiểm tra và xóa nếu vẫn còn dấu nháy đơn hoặc dấu chấm ở đầu/cuối
        clean_text = pretext.replace("'", "")
        clean_text = clean_text.replace(".", "")
        clean_text = clean_text.replace('"', '')
        if clean_text.startswith("{") :
            clean_text = clean_text[:1] + clean_text[1].upper() + clean_text[2:]
        return clean_text.strip()
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
                time = datetime.now().strftime("%d/%m/%Y")
                formatted_text = f"{original_text}       {{{time}}}"
            else:
                formatted_text = get_ai_formatted_text(original_text)
            
            # Ghi đè lại text.txt với text mới từ AI
            with open("text.txt", "r", encoding="utf-8") as file_read:
                lines = file_read.readlines()
            
            lines[2 + i * 2] = formatted_text + "\n"

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
                font_path="./EBGaramond-Bold.ttf",
                font_size=105,
                max_width=1100,
                line_spacing=15
            )

            if i == 0:
                text_image = add_text_to_image(
                    merged_image, 
                    filename, 
                    text="- Chỉ 10 giây mỗi ngày để nắm bắt tin tức -",
                    text_position=(113, 1884),
                    text_color="white",
                    font_path="./EBGaramond-Bold.ttf",
                    font_size=55,
                    max_width=1100,
                    line_spacing=15
               )

            if not text_image:
                print(f"Bỏ qua ảnh {i} do lỗi viết text.")
                continue
    print("Done")

except FileNotFoundError:
    print("Lỗi: Không tìm thấy file text.txt!")
except ValueError:
    print("Lỗi: File text.txt không đúng định dạng!")
except Exception as e:
    print(f"Lỗi không xác định: {e}")
