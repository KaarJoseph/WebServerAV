from flask import Flask, request, jsonify, send_from_directory, Response
import cv2
import os
import base64
import numpy as np
import time

app = Flask(__name__)

camera = None

def remove_green_background(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 80, 80])
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Aplicar operaciones morfológicas para eliminar ruido
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    # Aplicar suavizado para mejorar los bordes
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # Convertir la imagen a BGRA (añadir canal alfa)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    frame[:, :, 3] = cv2.bitwise_not(mask)

    return frame

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    if 'image' in data:
        image_data = data['image']
        image_data = base64.b64decode(image_data)
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
        
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        
        filepath = os.path.join('static', 'uploaded_image.png')
        cv2.imwrite(filepath, image)
        
        return jsonify({"message": "Imagen recibida exitosamente", "file_path": filepath}), 200, {'Content-Type': 'application/json'}
    return jsonify({"error": "No se encontró ninguna imagen en la solicitud"}), 400

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/uploaded_image')
def get_uploaded_image():
    filepath = os.path.join('static', 'uploaded_image.png')
    return jsonify({"file_path": filepath})

@app.route('/video_feed')
def video_feed():
    global camera
    if not camera:
        camera = cv2.VideoCapture(0)
    
    def generate():
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                frame = cv2.flip(frame, 1)
                frame = remove_green_background(frame)
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    global camera
    if not camera:
        camera = cv2.VideoCapture(0)
    
    success, frame = camera.read()
    if success:
        frame = cv2.flip(frame, 1)
        frame = remove_green_background(frame)
        timestamp = int(time.time())
        filepath = os.path.join('static', f'captured_image_{timestamp}.png')
        cv2.imwrite(filepath, frame)
        return jsonify({"file_path": filepath})
    else:
        return jsonify({"error": "Failed to capture image"}), 500

@app.route('/fuse_images', methods=['POST'])
def fuse_images():
    try:
        received_image_path = os.path.join('static', 'uploaded_image.png')
        captured_image_path = None

        # Buscar la última imagen capturada
        for file in sorted(os.listdir('static'), reverse=True):
            if file.startswith('captured_image_') and file.endswith('.png'):
                captured_image_path = os.path.join('static', file)
                break

        if not captured_image_path:
            return jsonify({"error": "No captured image found"}), 400

        # Cargar las imágenes
        received_image = cv2.imread(received_image_path, cv2.IMREAD_UNCHANGED)
        captured_image = cv2.imread(captured_image_path, cv2.IMREAD_UNCHANGED)
        background = cv2.imread('static/fondo.jpg', cv2.IMREAD_UNCHANGED)

        if received_image is None or captured_image is None or background is None:
            return jsonify({"error": "Error al cargar una o más imágenes"}), 400

        if received_image.shape[2] == 3:
            received_image = cv2.cvtColor(received_image, cv2.COLOR_BGR2BGRA)
        if captured_image.shape[2] == 3:
            captured_image = cv2.cvtColor(captured_image, cv2.COLOR_BGR2BGRA)

        # Redimenionar
        def resize_image(image, scale_percent):
            width = int(image.shape[1] * scale_percent / 100)
            height = int(image.shape[0] * scale_percent / 100)
            dim = (width, height)
            return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # Redimensionar
        received_image = resize_image(received_image, 900)
        captured_image = resize_image(captured_image, 470)

        # Función para colocar una imagen con alfa en el fondo
        def overlay_image(background, overlay, x, y):
            h, w = overlay.shape[:2]
            alpha_overlay = overlay[:, :, 3] / 255.0
            alpha_background = 1.0 - alpha_overlay

            for c in range(0, 3):
                background[y:y+h, x:x+w, c] = (alpha_overlay * overlay[:, :, c] + 
                                               alpha_background * background[y:y+h, x:x+w, c])

        # Coordenadas
        x_offset1, y_offset1 = 600, 1000
        x_offset2, y_offset2 = 2600, 1000

        overlay_image(background, received_image, x_offset1, y_offset1)

        overlay_image(background, captured_image, x_offset2, y_offset2)

        # Guardar la imagen resultante
        result_filepath = os.path.join('static', 'result_image.png')
        cv2.imwrite(result_filepath, background)

        return jsonify({"message": "Imágenes fusionadas exitosamente", "file_path": result_filepath}), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')
