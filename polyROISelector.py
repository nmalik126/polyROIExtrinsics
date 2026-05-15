import cv2
import numpy as np
from scipy.spatial.transform import Rotation


class Selector():
    
    def __init__(self, img, camera_matrix, dist_coeffs, ref_pts, window_name="input"):
        self.original_img = img
        self.window_name = window_name
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.ref_pts = ref_pts

        self.n_ref_pts = len(self.ref_pts)
        self.ref_pt_idx = 0
        self.selected_pts = []

        self.mouse_loc = None

        self.finished = False
        self.translation = None
        self.rotation = None
        self.reproj_pts = None

        cv2.imshow(self.window_name, self.original_img)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

    
    def display(self):
        if self.finished:
            current_img = self.display_result()
        else:
            current_img = self.display_selector()
        cv2.imshow(self.window_name, current_img)

    
    def display_result(self):
        current_img = self.original_img.copy()

        # write text
        cv2.putText(current_img, "User Selections", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, "Reprojections", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.putText(current_img, f"x: {self.translation[0]:.3f} m", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, f"y: {self.translation[1]:.3f} m", (50, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, f"z: {self.translation[2]:.3f} m", (50, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, f"roll: {self.rotation[0]:.3f} deg", (50, 270), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, f"pitch: {self.rotation[1]:.3f} deg", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(current_img, f"yaw: {self.rotation[2]:.3f} deg", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # draw points and lines
        for i, pt in enumerate(self.selected_pts):
            cv2.drawMarker(current_img, pt, (0, 255, 0))
            if i > 0:
                prev_pt = self.selected_pts[i-1]
                cv2.line(current_img, prev_pt, pt, (0, 255, 0), 1, cv2.LINE_AA)
        first_pt = self.selected_pts[0]
        last_pt = self.selected_pts[-1]
        cv2.line(current_img, last_pt, first_pt, (0, 255, 0), 1, cv2.LINE_AA)

        # draw reprojected object
        for pt in self.reproj_pts[0]:
            cv2.drawMarker(current_img, pt, (0, 0, 255))
        cv2.polylines(current_img, [self.reproj_pts], True, (0, 0, 255), 1)

        return current_img

    
    def display_selector(self):
        current_img = self.original_img.copy()

        # write text
        ref_pt_name, _ = self.ref_pts[self.ref_pt_idx]
        text = f"Select Reference Point: {ref_pt_name}"
        cv2.putText(current_img, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # draw points and lines
        for i, pt in enumerate(self.selected_pts):
            cv2.drawMarker(current_img, pt, (0, 255, 0))
            if i > 0:
                prev_pt = self.selected_pts[i-1]
                cv2.line(current_img, prev_pt, pt, (0, 255, 0), 1, cv2.LINE_AA)

        # draw current mouse location
        cv2.drawMarker(current_img, self.mouse_loc, (0, 255, 0))
        if self.ref_pt_idx > 0:
            last_pt = self.selected_pts[-1]
            cv2.line(current_img, last_pt, self.mouse_loc, (0, 255, 0), 1, cv2.LINE_AA)

        return current_img

    
    def write_extrinsics(self):
        # calc transformation
        img_pts = np.array(self.selected_pts, dtype=np.float32)
        obj_pts = np.array([loc for _, loc in self.ref_pts], dtype=np.float32)
        retval, rvec, tvec = cv2.solvePnP(
            obj_pts,
            img_pts,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_IPPE_SQUARE
        )

        # invert and save
        transform = np.eye(4)
        transform[:3, :3] = Rotation.from_rotvec(rvec.flatten()).as_matrix()
        transform[:3, 3] = tvec.flatten()
        print(transform)
        with open('cam_to_world.npy', 'wb') as f:
            np.save(f, transform)

        # calculate values for display
        self.translation = transform[:3, 3]
        self.rotation = Rotation.from_matrix(transform[:3, :3]).as_euler('xyz', degrees=True)
        
        reproj_pts_raw, _ = cv2.projectPoints(obj_pts, rvec, tvec, self.camera_matrix, self.dist_coeffs)
        self.reproj_pts = np.round(reproj_pts_raw).astype(np.int32)

    
    def mouse_callback(self, event, x, y, flags, param):
        if self.finished:
            return
        
        if event == cv2.EVENT_FLAG_LBUTTON:
            self.selected_pts.append((x, y))
            print(self.selected_pts)
            if self.ref_pt_idx == (self.n_ref_pts - 1):
                self.write_extrinsics()
                print('finished')
                self.finished = True
            else:
                self.ref_pt_idx += 1

        elif event == cv2.EVENT_MOUSEMOVE:
            self.mouse_loc = (x, y)
            