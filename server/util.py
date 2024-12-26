import joblib
import json
import numpy as np
import base64
import cv2
from wavelet import w2d

# Global variables to hold model and mappings
__class_name_to_number = {}
__class_number_to_name = {}
__model = None


def classify_image(image_base64_data, file_path=None):
    """
    Classifies an image based on the loaded model.

    :param image_base64_data: Base64 encoded image data
    :param file_path: Optional file path for an image
    :return: List of classification results
    """
    imgs = get_cropped_image_if_2_eyes(file_path, image_base64_data)
    if not imgs:
        return {'error': 'No valid images with two eyes detected'}

    result = []
    for img in imgs:
        try:
            # Preprocess the image
            scaled_raw_img = cv2.resize(img, (32, 32))
            img_har = w2d(img, 'db1', 5)
            scaled_img_har = cv2.resize(img_har, (32, 32))

            # Combine raw image and wavelet transform
            combined_img = np.vstack(
                (scaled_raw_img.reshape(32 * 32 * 3, 1),
                 scaled_img_har.reshape(32 * 32, 1))
            )
            len_image_array = 32 * 32 * 3 + 32 * 32
            final = combined_img.reshape(1, len_image_array).astype(float)

            # Predict using the model
            prediction = __model.predict(final)[0]
            class_probability = np.round(__model.predict_proba(final) * 100, 2).tolist()[0]

            result.append({
                'class': class_number_to_name(prediction),
                'class_probability': class_probability,
                'class_dictionary': __class_name_to_number
            })
        except Exception as e:
            result.append({'error': f"Error processing image: {str(e)}"})

    return result


def load_saved_artifacts():
    """
    Loads the model and supporting artifacts for classification.
    """
    global __class_name_to_number, __class_number_to_name, __model
    print("Loading saved artifacts...start")

    # Load class mappings
    with open("./artifacts/class_dictionar.json", "r") as f:
        __class_name_to_number = json.load(f)
        __class_number_to_name = {v: k for k, v in __class_name_to_number.items()}

    # Load model
    if __model is None:
        with open('./artifacts/saved_model.pkl', 'rb') as f:
            __model = joblib.load(f)

    print("Loading saved artifacts...done")


def class_number_to_name(class_num):
    """
    Converts a class number to its corresponding name.

    :param class_num: Class number
    :return: Class name
    """
    return __class_number_to_name.get(class_num, "Unknown")


def get_cv2_image_from_base64_string(b64str):
    """
    Converts a Base64 string to an OpenCV image.

    :param b64str: Base64 encoded image string
    :return: OpenCV image
    """
    encoded_data = b64str.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def get_cropped_image_if_2_eyes(image_path, image_base64_data):
    """
    Detects faces with two eyes in the given image.

    :param image_path: File path for an image
    :param image_base64_data: Base64 encoded image data
    :return: List of cropped images containing faces with two eyes
    """
    face_cascade = cv2.CascadeClassifier("./opencv/haarcascades/haarcascade_frontalface_default.xml")
    eye_cascade = cv2.CascadeClassifier("./opencv/haarcascades/haarcascade_eye.xml")

    if image_path:
        img = cv2.imread(image_path)
        if img is None:
            return []
    else:
        img = get_cv2_image_from_base64_string(image_base64_data)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    cropped_faces = []
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        if len(eyes) >= 2:
            cropped_faces.append(roi_color)

    return cropped_faces


def get_b64_test_image_for_shaq():
    """
    Reads a Base64 encoded test image from a file.
    :return: Base64 string of the test image
    """
    with open("b64.txt") as f:
        return f.read()


# Main execution block for testing
if __name__ == '__main__':
    load_saved_artifacts()
    print("Testing classify_image:")
    print(classify_image(None, "./test_images/00-promo-image-steph-curry.jpg"))
    print(classify_image(None, "./test_images/08bb64523effa1fc3d8bd38880c1b5f4.jpg"))
    print(classify_image(None, "./test_images/1550.png"))
    print(classify_image(None,
                         "./test_images/png-clipart-michael-jordan-michael-jordan-charlotte-hornets-athlete-nike-basketball-head-face-sport.png"))
