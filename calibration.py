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
pixel_cm_ratio = None

def get_distance_and_calibrate(event, x, y, flags, param):
    """
    Функція для обробки події кліку миші
    для збереження відстані до підлоги та визначення pixel_cm_ratio
    """
    global base_distance_to_floor, depth_frame, pixel_cm_ratio

    if event == cv2.EVENT_LBUTTONDOWN:
        distance = depth_frame.get_distance(x, y)
        
        if base_distance_to_floor is None:
            # Встановлюємо базову відстань до підлоги
            base_distance_to_floor = distance
            print(f"Відстань до підлоги збережена: {base_distance_to_floor:.3f} метра")
        elif pixel_cm_ratio is None:
            # Зберігаємо координати двох точок на відомому об'єкті
            param.append((x, y))
            if len(param) == 2:
                # Розраховуємо відстань між двома точками
                pixel_distance = np.sqrt((param[0][0] - param[1][0]) ** 2 + (param[0][1] - param[1][1]) ** 2)
                
                # Запит на введення фактичної довжини об'єкта
                actual_length_cm = float(input("Введіть фактичну довжину між обраними точками в см: "))
                
                # Визначаємо співвідношення пікселів до сантиметрів
                pixel_cm_ratio = pixel_distance / actual_length_cm
                print(f"pixel_cm_ratio визначено: {pixel_cm_ratio:.3f} пікселів/см")

                # Зберігаємо дані для використання у другому файлі
                with open("calibration_data.txt", "w") as f:
                    f.write(f"{base_distance_to_floor}\n{pixel_cm_ratio}")

try:
    points = []  # Для збереження точок на відомому об'єкті
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
        cv2.imshow("Calibration Image", color_image)
        cv2.setMouseCallback("Calibration Image", get_distance_and_calibrate, param=points)

        # Вихід за натисканням 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Завершення роботи з камерою
    pipeline.stop()
    cv2.destroyAllWindows()
