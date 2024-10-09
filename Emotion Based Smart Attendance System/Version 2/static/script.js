document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureButton = document.getElementById('capture');
    const submitButton = document.getElementById('submit');
    const resetButton = document.getElementById('reset');
    const nameInput = document.getElementById('name');
    const rollNo = document.getElementById('rollNo'); // Ensure rollNo is defined here
    const emotionResult = document.getElementById('emotionResult');
    const loading = document.getElementById('loading');

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            video.srcObject = stream;
        })
        .catch(function(error) {
            console.error("Cannot access the camera: ", error);
            alert('Error accessing the camera. Please allow camera access.');
        });

    captureButton.addEventListener('click', function() {
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        video.style.display = 'none';
        canvas.style.display = 'block';
        captureButton.style.display = 'none';
        submitButton.style.display = 'inline';
    });

    submitButton.addEventListener('click', function() {
        const name = nameInput.value.trim();
        const roll = rollNo.value.trim(); // Use roll for clarity
        if (!name || !roll) {
            alert('Please enter your name and roll number.');
            return;
        }

        loading.style.display = 'block';  // Show loading GIF
        submitButton.style.display = 'none';  // Hide submit button

        canvas.toBlob(function(blob) {
            const formData = new FormData();
            formData.append('photo', blob);
            formData.append('name', name);
            formData.append('rollNo', roll); // Corrected to use roll's value

            fetch('/submit', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';  // Hide loading GIF
                if (data.message === 'Submission successful') {
                    emotionResult.innerHTML = `Detected emotion: ${data.emotion} with accuracy of ${data.accuracy}. Your attendance has been recorded.`;
                } else {
                    emotionResult.innerHTML = `Error: ${data.error}`;
                }
                resetButton.style.display = 'inline';  // Show reset button
            })
            .catch((error) => {
                loading.style.display = 'none';
                console.error('Error:', error);
                alert('An error occurred while submitting. Please try again.');
                resetButton.style.display = 'inline';
            });
        }, 'image/jpeg');
    });

    resetButton.addEventListener('click', function() {
        resetForm();
    });

    function resetForm() {
        video.style.display = 'inline';
        canvas.style.display = 'none';
        captureButton.style.display = 'inline';
        submitButton.style.display = 'none';
        resetButton.style.display = 'none';
        nameInput.value = '';
        rollNo.value = ''; // Ensure rollNo is also cleared
        emotionResult.innerHTML = '';
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
            });
    }
});

document.getElementById('downloadReport').addEventListener('click', function() {
    const downloadRollNo = document.getElementById('downloadRollNo').value.trim();
    if (downloadRollNo) {
        window.location.href = `/download-report/${downloadRollNo}`;
    } else {
        alert('Please enter your roll number.');
    }
});
