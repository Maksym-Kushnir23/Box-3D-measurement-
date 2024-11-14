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

try:
    while True:
        # Отримання кадрів з камери
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue

        # Перетворення кадру з глибиною на Numpy-масив
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Налаштування глибинного діапазону для виявлення найближчого об'єкта
        min_distance = int(np.min(depth_image[depth_image > 0]))  # Знаходимо мінімальну відстань і приводимо до цілого
        tolerance = 50  # Допустиме відхилення від найменшої відстані в міліметрах

        # Створення маски, де об'єкти у вибраному діапазоні глибини виділяються
        mask = cv2.inRange(depth_image, min_distance, min_distance + tolerance)

        # Виконання морфологічних операцій для очищення маски
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Знаходження контурів на масці
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Пошук найбільшого контуру (припущення, що це - верхня грань коробки)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)

            # Побудова обмежувального прямокутника навколо контуру
            rect = cv2.minAreaRect(largest_contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # Обчислення довжини сторін прямокутника
            width = np.linalg.norm(box[0] - box[1])
            height = np.linalg.norm(box[1] - box[2])

            # Відображення розмірів на зображенні
            cv2.drawContours(color_image, [box], 0, (0, 255, 0), 2)
            cv2.putText(color_image, f"Width: {width:.1f} mm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(color_image, f"Height: {height:.1f} mm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Відображення зображення
        cv2.imshow("Color Image with Bounding Box", color_image)
        cv2.imshow("Depth Mask", mask)

        # Вихід за натисканням 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Завершення роботи з камерою
    pipeline.stop()
    cv2.destroyAllWindows()
