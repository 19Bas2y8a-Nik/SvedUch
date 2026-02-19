"""
Генератор иконки приложения SvedUch.
Создаёт иконку app.ico с изображением книги/журнала с данными.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_book_icon(size):
    """
    Создаёт изображение книги/журнала с данными заданного размера.
    
    Args:
        size: размер изображения (width, height)
    
    Returns:
        PIL.Image: изображение иконки
    """
    # Создаём изображение с прозрачным фоном
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    width, height = size
    
    # Определяем масштаб для разных размеров
    scale = width / 256.0
    
    # Цвета
    book_color = (70, 130, 180)  # Steel Blue - цвет обложки книги
    pages_color = (255, 255, 250)  # Почти белый для страниц
    text_color = (50, 50, 50)  # Тёмно-серый для текста
    spine_color = (50, 100, 140)  # Более тёмный синий для корешка
    
    # Координаты книги (центрированы)
    book_width = max(8, int(140 * scale))  # Минимум 8 пикселей
    book_height = max(10, int(180 * scale))  # Минимум 10 пикселей
    book_x = (width - book_width) // 2
    book_y = (height - book_height) // 2
    
    # Рисуем корешок книги (слева)
    spine_width = max(1, int(20 * scale))  # Минимум 1 пиксель
    draw.rectangle(
        [book_x, book_y, book_x + spine_width, book_y + book_height],
        fill=spine_color
    )
    
    # Рисуем обложку книги
    draw.rectangle(
        [book_x + spine_width, book_y, book_x + book_width, book_y + book_height],
        fill=book_color,
        outline=(40, 80, 110),
        width=max(1, int(2 * scale))
    )
    
    # Рисуем страницы (белые прямоугольники внутри)
    page_margin = max(1, min(int(15 * scale), (book_width - spine_width) // 4))
    # Убеждаемся, что страницы не выходят за границы книги
    page_x1 = book_x + spine_width + page_margin
    page_y1 = book_y + page_margin
    page_x2 = max(page_x1 + 2, book_x + book_width - page_margin)
    page_y2 = max(page_y1 + 2, book_y + book_height - page_margin)
    
    if page_x2 > page_x1 and page_y2 > page_y1:
        draw.rectangle(
            [page_x1, page_y1, page_x2, page_y2],
            fill=pages_color,
            outline=(200, 200, 200),
            width=max(1, int(1 * scale))
        )
    
    # Рисуем линии текста на страницах (символизируют данные)
    # Для маленьких размеров упрощаем отрисовку
    line_spacing = max(1, int(8 * scale))  # Минимум 1 пиксель
    line_y_start = book_y + int(30 * scale)
    line_width = book_width - spine_width - int(30 * scale)
    
    # Вычисляем количество строк, избегая деления на ноль
    available_height = book_height - int(60 * scale)
    if line_spacing > 0 and available_height > 0:
        max_lines = min(8, max(1, available_height // line_spacing))
        for i in range(max_lines):
            line_y = line_y_start + i * line_spacing
            if line_y >= book_y + book_height - int(20 * scale):
                break
            line_length = int(line_width * (0.7 + (i % 3) * 0.1))  # Разная длина строк
            if line_length > 0:
                draw.rectangle(
                    [
                        book_x + spine_width + int(20 * scale),
                        line_y,
                        book_x + spine_width + int(20 * scale) + line_length,
                        line_y + max(1, int(2 * scale))
                    ],
                    fill=text_color
                )
    
    # Рисуем декоративные элементы на обложке
    # Горизонтальные линии на корешке (символизируют переплёт)
    # Только для размеров больше 32x32, чтобы не перегружать маленькие иконки
    if width >= 32:
        for i in range(3):
            line_y = book_y + int((i + 1) * book_height / 4)
            line_x_start = book_x + max(1, int(5 * scale))
            line_x_end = book_x + spine_width - max(1, int(5 * scale))
            if line_x_end > line_x_start:
                draw.line(
                    [line_x_start, line_y, line_x_end, line_y],
                    fill=(30, 70, 100),
                    width=max(1, int(2 * scale))
                )
    
    return img


def create_icon():
    """Создаёт иконку app.ico с несколькими размерами."""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    print("Создание иконки app.ico...")
    print(f"Размеры: {', '.join([f'{w}x{h}' for w, h in sizes])}")
    
    # Создаём изображения всех размеров
    images = []
    for size in sizes:
        img = create_book_icon(size)
        images.append(img)
        print(f"  ✓ Создано изображение {size[0]}x{size[1]}")
    
    # Сохраняем как .ico файл
    # ICO формат поддерживает несколько размеров в одном файле
    output_path = 'app.ico'
    
    # Создаём ICO файл с несколькими размерами
    # Используем первое изображение как основное и добавляем остальные
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images]
    )
    
    # Альтернативный метод: если предыдущий не работает со всеми размерами,
    # можно использовать библиотеку icoextract или сохранить через другой способ
    # Но стандартный метод Pillow должен работать
    
    if os.path.exists(output_path):
        print(f"\nИконка сохранена: {output_path}")
        print(f"Размер файла: {os.path.getsize(output_path) / 1024:.1f} KB")
    else:
        print(f"\n⚠ Предупреждение: файл {output_path} не был создан")


if __name__ == '__main__':
    try:
        create_icon()
        print("\n✓ Готово!")
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
