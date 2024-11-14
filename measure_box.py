import pyrealsense2 as rs
import numpy as np
import cv2

# Завантаження даних калібрування
with open("calibration_data.txt", "r") as f:
    base_distance_to_floor = float(f.readline().strip())
    pixel_cm_ratio = float(f.readline().strip())

# Ініціалізація камери RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Запуск камери
pipeline.start(config)

# Масив для зберігання обраних точок на коробці
box_points = []  # зберігатиме чотири точки

def get_box_dimensions(event, x, y, flags, param):
    """
    Обробка події кліку миші для вибору точок на коробці.
    Перші три точки — кути, четверта — точка на верхній грані.
    """
    global depth_frame, box_points

    if event == cv2.EVENT_LBUTTONDOWN:
        distance = depth_frame.get_distance(x, y)
        
        # Додаємо обрану точку
        box_points.append((x, y, distance))
        print(f"Точка {len(box_points)} збережена: координати ({x}, {y}), відстань {distance:.3f} метра")
        
        # Обчислюємо розміри коробки після вибору всіх 4 точок
        if len(box_points) == 4:
            # Висота коробки
            box_height_m = base_distance_to_floor - box_points[3][2]
            box_height_cm = box_height_m * 100
            print(f"Висота коробки: {box_height_cm:.2f} см")

            # Довжина і ширина коробки
            width_pixels = np.sqrt((box_points[0][0] - box_points[1][0]) ** 2 + (box_points[0][1] - box_points[1][1]) ** 2)
            length_pixels = np.sqrt((box_points[1][0] - box_points[2][0]) ** 2 + (box_points[1][1] - box_points[2][1]) ** 2)

           # width_cm = (width_pixels / pixel_cm_ratio) * (base_distance_to_floor - box_height_m / base_distance_to_floor)
           # length_cm = (length_pixels / pixel_cm_ratio) * (base_distance_to_floor - box_height_m / base_distance_to_floor)
            width_cm = (width_pixels / pixel_cm_ratio) * (box_points[3][2] / base_distance_to_floor)
            length_cm = (length_pixels / pixel_cm_ratio) * (box_points[3][2] / base_distance_to_floor)
            
            print(f"Ширина коробки: {width_cm:.2f} см")
            print(f"Довжина коробки: {length_cm:.2f} см")

            # Очищуємо обрані точки для наступного вимірювання
            box_points = []

try:
    while True:
        # Отримання кадрів
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue

        # Конвертація кольорового зображення в Numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Отримуємо розміри зображення
        height, width, _ = color_image.shape
        center_x, center_y = width // 2, height // 2

        # Малювання осей
        cv2.line(color_image, (center_x, 0), (center_x, height), (0, 255, 0), 1)  # Вісь Y
        cv2.line(color_image, (0, center_y), (width, center_y), (255, 0, 0), 1)  # Вісь X

        # Додавання мітки нуля в центрі
        cv2.putText(color_image, "(0, 0)", (center_x + 5, center_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Відображення кольорового зображення для вибору точок
        cv2.imshow("Measure Box", color_image)
        cv2.setMouseCallback("Measure Box", get_box_dimensions)

        # Вихід за натисканням 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Завершення роботи з камерою
    pipeline.stop()
    cv2.destroyAllWindows()
