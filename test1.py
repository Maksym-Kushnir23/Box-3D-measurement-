import pyrealsense2 as rs
import numpy as np
import cv2

# Ініціалізація камери RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Запуск камери
pipeline.start(config)

# Змінна для зберігання базової відстані до підлоги
base_distance_to_floor = None

# Масив для зберігання обраних точок на коробці
box_points = []

def get_distance(event, x, y, flags, param):
    """
    Функція для обробки події кліку миші
    і виведення відстані до обраної точки
    """
    global base_distance_to_floor, depth_frame, box_points

    if event == cv2.EVENT_LBUTTONDOWN:
        distance = depth_frame.get_distance(x, y)
        
        if base_distance_to_floor is None:
            # Встановлюємо базову відстань до підлоги
            base_distance_to_floor = distance
            print(f"Відстань до підлоги збережена: {base_distance_to_floor:.3f} метра")
        else:
            # Додаємо обрану точку до масиву для коробки
            box_points.append((x, y, distance))
            print(f"Точка {len(box_points)} збережена: координати ({x}, {y}), відстань {distance:.3f} метра")
        
        # Виводимо розміри коробки, коли обрано 4 точки
        if len(box_points) == 4:
            # Визначення висоти коробки
            box_height_m = base_distance_to_floor - box_points[3][2]
            box_height_cm = box_height_m * 100  # Конвертуємо в см
            print(f"Висота коробки: {box_height_cm:.2f} см")

            # Розрахунок довжини та ширини коробки в пікселях
            width_pixels = np.sqrt((box_points[0][0] - box_points[1][0]) ** 2 + (box_points[0][1] - box_points[1][1]) ** 2)
            length_pixels = np.sqrt((box_points[1][0] - box_points[2][0]) ** 2 + (box_points[1][1] - box_points[2][1]) ** 2)

            # Конвертуємо довжину і ширину в реальні одиниці (за необхідності калібруйте цей коефіцієнт)
            pixel_cm_ratio = 12.24  # Наприклад, визначений співвідношення пікселів до см
            width_cm = width_pixels / pixel_cm_ratio
            length_cm = length_pixels / pixel_cm_ratio

            print(f"Ширина коробки: {width_cm:.2f} см")
            print(f"Довжина коробки: {length_cm:.2f} см")

            # Очищуємо обрані точки для нових вимірювань
            box_points = []

try:
    while True:
        # Отримання кадрів
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue

        # Конвертація глибинного та кольорового зображень в Numpy arrays
        color_image = np.asanyarray(color_frame.get_data())

        # Відображення кольорового зображення для вибору точок
        cv2.imshow("Color Image", color_image)

        # Додавання обробника події кліку миші для отримання відстані на звичайному зображенні
        cv2.setMouseCallback("Color Image", get_distance)

        # Вихід за натисканням 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Завершення роботи з камерою
    pipeline.stop()
    cv2.destroyAllWindows()
