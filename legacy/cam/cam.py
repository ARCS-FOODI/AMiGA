import cv2

def preview_usb_cam(cam_index=0):
    cap = cv2.VideoCapture(cam_index)

    if not cap.isOpened():
        print("Cannot open camera")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        cv2.imshow('USB Webcam Preview', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

preview_usb_cam(0)  # Change to 1 if you have multiple cameras
