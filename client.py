import requests

url = 'http://127.0.0.1:5000/upload'
file_path = '/home/kaarjoseph/Descargas/spiderman-y-spidercat_3840x2160_xtrafondos.com.jpg'  # Cambia esto a la ruta de una imagen de prueba en tu computadora

with open(file_path, 'rb') as img_file:
    files = {'image': img_file}
    response = requests.post(url, files=files)

print(response.json())

