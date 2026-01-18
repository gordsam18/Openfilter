from ultralytics import YOLO
import sys
import os
import numpy as np
import cv2

def detect_objects_from_array(image_array):
    """
    Detect objects in a numpy array image
    
    Args:
        image_array: numpy.ndarray - The image as a numpy array (BGR or RGB format)
    
    Returns:
        list: List of dictionaries containing detected objects with 'class' and 'confidence' keys
    """
    # Load the YOLO model
    model = YOLO('yolov8n.pt')  # Using the smallest YOLOv8 model
    
    # Check if input is a numpy array
    if not isinstance(image_array, np.ndarray):
        print("Error: Input must be a numpy array.")
        return []
    
    # Run inference on the numpy array
    results = model(image_array, verbose=False)
    
    # Process results
    detected_objects = []
    for result in results:
        boxes = result.boxes
        if len(boxes) == 0:
            print("No objects detected in the image.")
            return []
        
        for box in boxes:
            # Get class name and confidence
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])
            
            # Add object to list
            detected_objects.append({
                'class': class_name,
                'confidence': confidence
            })
    
    return detected_objects

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detect_objects.py <path_to_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
    
    # Load image as numpy array
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image '{image_path}'.")
        sys.exit(1)
    
    # Run detection on numpy array
    objects = detect_objects_from_array(image)
    
    if objects:
        print("\nDetected objects:")
        for obj in objects:
            print(f"- {obj['class']} (confidence: {obj['confidence']:.2f})") 