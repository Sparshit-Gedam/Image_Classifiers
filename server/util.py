import joblib
import json
import numpy as np
import base64
import cv2
from wavelet import w2d
import os
import logging

# Global variables to hold model and mappings
__class_name_to_number = {}
__class_number_to_name = {}
__model = None


def classify_image(image_base64_data, file_path=None):
    """
    Classifies an image based on the loaded model.

    :param image_base64_data: Base64 encoded image data
    :param file_path: Optional file path for an image
    :return: List of classification results or an error message
    """
    global __model
    if __model is None:
        raise ValueError("The model is not loaded. Ensure load_saved_artifacts() is called.")

    if not image_base64_data and not file_path:
        logging.error("No image data or file path provided.")
        return {'error': 'No image data or file path provided'}

        # Validate Base64 image format
    if image_base64_data and not isinstance(image_base64_data, str):
        logging.error("Invalid Base64 image data.")
        return {'error': 'Invalid Base64 image data'}

    imgs = get_cropped_image_if_2_eyes(file_path, image_base64_data)
    if not imgs:
        return [{'error': 'No valid images with two eyes detected'}]

    results = []
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

            results.append({
                'class': class_number_to_name(prediction),
                'class_probability': class_probability,
                'class_dictionary': __class_name_to_number
            })
        except Exception as e:
            results.append({
                'class': None,
                'class_probability': [],
                'error': f"Error processing image: {str(e)}"
            })

            # Handle case where no valid images were found
    if not results:
                return [{'class': None, 'class_probability': [], 'error': 'No valid images with two eyes detected'}]

    return results


def load_saved_artifacts():
    """
    Loads model and class mapping artifacts.
    """
    global __class_name_to_number, __class_number_to_name, __model
    print("Loading saved artifacts...start")

    # Load class mappings
    try:
        artifacts_path = "./artifacts"
        class_dict_path = os.path.join(artifacts_path, "class_dictionar.json")
        model_path = os.path.join(artifacts_path, "saved_model.pkl")

        with open(class_dict_path, "r") as f:
            __class_name_to_number = json.load(f)
            __class_number_to_name = {v: k for k, v in __class_name_to_number.items()}
        print("Class dictionary loaded successfully.")

        # Load model
        if __model is None:
            with open(model_path, 'rb') as f:
                __model = joblib.load(f)
            print("Model loaded successfully.")

    except Exception as e:
        print(f"Error loading artifacts: {e}")

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
    try:
        if not isinstance(b64str, str):
            logging.error("Provided Base64 data is not a string.")
            return None

        if ',' in b64str:
            encoded_data = b64str.split(',')[1]
        else:
            encoded_data = b64str
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logging.error("Decoded image is None.")
            return None
        return img
    except Exception as e:
        logging.error(f"Error decoding Base64 string: {str(e)}")
        return None


def get_cropped_image_if_2_eyes(image_path, image_base64_data):
    """
    Detects faces with two eyes in the given image.

    :param image_path: File path for an image
    :param image_base64_data: Base64 encoded image data
    :return: List of cropped images containing faces with two eyes
    """
    face_cascade_path = "./resources/haarcascade_frontalface_default.xml"
    eye_cascade_path = "./resources/haarcascade_eye.xml"

    if not os.path.exists(face_cascade_path) or not os.path.exists(eye_cascade_path):
        print("Cascade files are missing.")
        return []

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    img = None
    if image_path:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Image at path {image_path} not found.")
            return []
    elif image_base64_data:
        img = get_cv2_image_from_base64_string(image_base64_data)
        if img is None:
            print("Invalid Base64 image data.")
            return []

    try:

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        cropped_faces = []
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            if len(eyes) >= 2:
                cropped_faces.append(roi_color)

        if not cropped_faces:
            logging.error("No valid faces with two eyes detected.")
        return cropped_faces

    except Exception as e:
       logging.error(f"Error in face/eye detection: {str(e)}")
       return []


def get_b64_test_image_for_shaq():
    """
    Reads a Base64 encoded test image from a file.
    :return: Base64 string of the test image
    """
    try:
        with open("b64.txt") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading test image file: {e}")
        return None


# Main execution block for testing
if __name__ == '__main__':
    load_saved_artifacts()
    print("Testing classify_image:")
    print(classify_image(None, "./test_images/00-promo-image-steph-curry.jpg"))
    print(classify_image(None, "./test_images/2544.png"))
    print(classify_image(None, "./test_images/1550.png"))


