// script.js

function updateReceivedImage() {
    fetch('/uploaded_image')
        .then(response => response.json())
        .then(data => {
            document.getElementById('receivedImage').src = data.file_path;
        })
        .catch(error => {
            console.error('Error al obtener la imagen:', error);
        });
}

function captureImage() {
    fetch('/capture_image', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.file_path) {
            var capturedImage = document.getElementById('cameraFeed');
            capturedImage.src = '/' + data.file_path;
            document.getElementById('captureButton').style.display = 'none';
            document.getElementById('retakeButton').style.display = 'inline-block';
        } else {
            console.error('Error al capturar la imagen:', data.error);
        }
    })
    .catch(error => console.error('Error al capturar la imagen:', error));
}

function retakeImage() {
    var cameraFeed = document.getElementById('cameraFeed');
    cameraFeed.src = '/video_feed';
    document.getElementById('captureButton').style.display = 'inline-block';
    document.getElementById('retakeButton').style.display = 'none';
}

function fuseImages() {
    fetch('/fuse_images', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.file_path) {
            var resultImage = document.getElementById('resultImage');
            resultImage.src = '/' + data.file_path;
        } else {
            console.error('Error al fusionar las imágenes:', data.error);
        }
    })
    .catch(error => console.error('Error al fusionar las imágenes:', error));
}

// Llama a la función cada 5 segundos
setInterval(updateReceivedImage, 5000);