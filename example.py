import cv2
import numpy as np

from polyROISelector import Selector


img = cv2.imread("input.png")
camera_matrix = np.load("camera_matrix.npy")
dist_coeffs = np.load("dist_coeffs.npy")
ref_pts = [
    ("top_left", [-0.2, 0.2, 0]),
    ("top_right", [0.2, 0.2, 0]),
    ("bottom_right", [0.2, -0.2, 0]),
    ("bottom_left", [-0.2, -0.2, 0]),
]

selector = Selector(img, camera_matrix, dist_coeffs, ref_pts)

try:
    while True:
        selector.display()
        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            break

finally:
    cv2.destroyAllWindows()