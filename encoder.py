import os
import pickle
import face_recognition


DATASET_PATH = "dataset"
ENCODINGS_FILE = "encodings.pickle"

class Encoder:
    def encode_faces(self):
        print("[INFO] Quantifying faces...")
        imagePaths = []
        
        # Traverse the dataset directory
        for root, dirs, files in os.walk(DATASET_PATH):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    imagePaths.append(os.path.join(root, file))

        knownEncodings = []
        knownNames = []

        for (i, imagePath) in enumerate(imagePaths):
            print(f"[INFO] Processing image {i + 1}/{len(imagePaths)}")
            # Extract the person name from the image path
            # Structure: dataset/ID_Name/image.jpg
            path_parts = imagePath.split(os.path.sep)
            # Assuming the folder name is the ID_Name or just Name. 
            # The prompt says "dataset/[ID]_[Name]"
            folder_name = path_parts[-2]
            name = folder_name # We will use the folder name as the identifier

            # Load the input image and convert it from BGR (OpenCV ordering)
            # to RGB (dlib ordering)
            image = face_recognition.load_image_file(imagePath)
            # face_recognition loads as RGB by default if using load_image_file

            # Detect the (x, y)-coordinates of the bounding boxes
            # corresponding to each face in the input image
            boxes = face_recognition.face_locations(image, model="hog")

            # Compute the facial embedding for the face
            encodings = face_recognition.face_encodings(image, boxes)

            # Loop over the encodings
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)

        print("[INFO] Serializing encodings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        with open(ENCODINGS_FILE, "wb") as f:
            f.write(pickle.dumps(data))
        print("[INFO] Encodings saved.")

if __name__ == "__main__":
    encoder = Encoder()
    encoder.encode_faces()
