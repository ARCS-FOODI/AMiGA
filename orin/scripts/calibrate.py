import cv2
import numpy as np
import glob
import os

# --- Configuration ---
CHECKERBOARD = (9, 7) # Number of inner corners per a chessboard row and column
SQUARE_SIZE_MM = 6.35 # Size of a square in your defined unit (mm, cm, etc.)
IMAGES_DIR = "calibration_images"
OUTPUT_FILE = "calibration_data.yaml"

def main():
    # Termination criteria for refining the detected corners
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE_MM

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    
    images = glob.glob(os.path.join(IMAGES_DIR, '*.png'))
    if not images:
        print(f"No PNG images found in {IMAGES_DIR}. Please run capture_samples.py first.")
        return

    print(f"Found {len(images)} images for calibration.")
    
    gray = None
    img_shape = None

    window_name = 'Detecting Corners'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if img_shape is None:
            img_shape = gray.shape[::-1]
            
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            
            # Draw and display the corners (optional feedback)
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
            cv2.imshow(window_name, img)
            cv2.waitKey(100)
        else:
            print(f"Corners not found in {fname}")

    cv2.destroyAllWindows()

    if not objpoints:
        print("Error: Could not find checkerboard corners in any images.")
        return

    print("Calculating calibration matrix...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)

    if ret:
        print(f"Calibration successful! RMS Error: {ret}")
        print("Camera Matrix:")
        print(mtx)
        print("Distortion Coefficients:")
        print(dist)
        
        # Save the camera calibration result for later use
        print(f"Saving calibration data to {OUTPUT_FILE}...")
        cv_file = cv2.FileStorage(OUTPUT_FILE, cv2.FILE_STORAGE_WRITE)
        cv_file.write("camera_matrix", mtx)
        cv_file.write("dist_coeff", dist)
        cv_file.release()
        print("Done.")
    else:
        print("Calibration failed.")

if __name__ == "__main__":
    main()
