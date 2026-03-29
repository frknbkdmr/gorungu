
import cv2
import numpy as np

def align_images(img, ref):
    """
    Align 'img' to 'ref' using SIFT or ORB.
    Returns (aligned_img, M).
    """
    print("[ALIGN] Görsel hizalama başlatıldı")
    if img is None or ref is None:
        return None, None
        
    h_ref, w_ref = ref.shape[:2]
    h_img, w_img = img.shape[:2]
    
    # convert to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    
    try:
        detector = cv2.SIFT_create()
        norm = cv2.NORM_L2
        print("[ALIGN] SIFT detektörü kullanılıyor")
    except AttributeError:
        detector = cv2.ORB_create(nfeatures=5000)
        norm = cv2.NORM_HAMMING
        print("[ALIGN] ORB detektörü kullanılıyor (SIFT mevcut değil)")
    
    kp1, des1 = detector.detectAndCompute(gray_img, None)
    kp2, des2 = detector.detectAndCompute(gray_ref, None)
    
    if des1 is None or des2 is None:
        print("[ERROR] Özellik tanımlayıcıları bulunamadı")
        return None, None

    bf = cv2.BFMatcher(norm)
    matches = bf.knnMatch(des1, des2, k=2)
    
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    
    if len(good_matches) > 10:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # Strategy 1: Homography
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        is_homography_good = False
        if M is not None:
            # sanity check
            corners = np.float32([[0, 0], [0, h_img], [w_img, h_img], [w_img, 0]]).reshape(-1, 1, 2)
            warped_corners = cv2.perspectiveTransform(corners, M)
            area = cv2.contourArea(warped_corners)
            ref_area = w_ref * h_ref
            
            area_ratio = area / ref_area if ref_area > 0 else 0
            if 0.5 < area_ratio < 1.5:
                is_homography_good = True
            else:
                print(f"[ALIGN] Homography reddedildi: Alan oranı {area_ratio:.2f}")

        if is_homography_good:
            aligned_img = cv2.warpPerspective(img, M, (w_ref, h_ref))
            return aligned_img, M
        
        # Strategy 2: Affine
        M_affine, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts)
        if M_affine is not None:
            aligned_img = cv2.warpAffine(img, M_affine, (w_ref, h_ref))
            # Pad 2x3 affine matrix to 3x3 for consistency with homography
            M_padded = np.vstack([M_affine, [0, 0, 1]])
            return aligned_img, M_padded
        
        return None, None
    else:
        print("[ERROR] Yetersiz iyi eşleşme")
        return None, None

def score_page(aligned_img, rois, threshold=0.12):
    """
    Scores a page given an aligned image and ROI definitions.
    Returns (page_score, page_subscales, page_log, page_details)
    """
    print(f"[SCORE] {len(rois)} bölge puanlanıyor (Eşik: {threshold})...")
    gray_aligned = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray_aligned, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                 cv2.THRESH_BINARY_INV, 15, 5)
    kernel = np.ones((2,2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    p_score = 0
    p_subscales = {}
    p_log = []
    p_details = []
    
    for item in rois:
        x, y, w, h = item['x'], item['y'], item['w'], item['h']
        val_str = item['value']
        label = item['label']
        subscale = item.get('subscale', 'Genel')
        
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.15)
        roi_x = x + margin_x
        roi_y = y + margin_y
        roi_w = w - (2 * margin_x)
        roi_h = h - (2 * margin_y)
        
        roi_bin = binary[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        
        if roi_w <= 0 or roi_h <= 0 or roi_bin.size == 0:
            non_zero = 0
            area = 1
            fill_ratio = 0.0
            mean_intensity = 0.0
        else:
            non_zero = cv2.countNonZero(roi_bin)
            area = roi_w * roi_h
            if area == 0: area = 1
            fill_ratio = non_zero / area
            
            roi_gray = gray_aligned[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            mean_intensity = cv2.mean(roi_gray)[0]
        
        is_marked = fill_ratio > threshold
        
        p_details.append({
            'roi_def': item,
            'is_marked': is_marked,
            'fill_ratio': fill_ratio,
            'mean_intensity': mean_intensity
        })
        
        status = "[ ]"
        if is_marked:
            status = "[X]"
            try:
                score = float(val_str)
                p_score += score
                p_subscales[subscale] = p_subscales.get(subscale, 0) + score
            except ValueError:
                pass
        
        p_log.append(f"{status} {label} [{subscale}]: {val_str if is_marked else '0'} ({fill_ratio:.2f})")
    
    return p_score, p_subscales, p_log, p_details

def detect_corners(image):
    """
    Auto-detect document corners.
    Returns (found_bool, corners_list)
    """
    print("[CORNERS] Otomatik köşe tespiti yapılıyor...")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        if len(approx) == 4:
            print("[CORNERS] Köşeler bulundu.")
            return True, [p[0].tolist() for p in approx]
            
    # fallback
    print("[CORNERS] Otomatik tespit başarısız, varsayılan köşeler kullanılıyor.")
    h, w = image.shape[:2]
    m = 50
    corners = [[m, m], [m, h-m], [w-m, h-m], [w-m, m]]
    return False, corners

def get_four_point_transform(image, pts):
    """
    Transforms image based on 4 points (corners).
    pts: list or array of 4 points [[x,y]...]
    """
    src_pts = np.array(pts, dtype="float32")
    
    # Sort corners: tl, tr, br, bl
    # We can reuse sort logic
    rect = sort_corners(src_pts)
    (tl, tr, br, bl) = rect

    # Compute width
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # Compute height
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst_pts = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst_pts)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped

def sort_corners(pts):
    """
    Sorts corners in order: top-left, top-right, bottom-right, bottom-left.
    pts: numpy array or list of 4 points.
    Returns numpy array of sorted points.
    """
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # TL
    rect[2] = pts[np.argmax(s)] # BR
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # TR
    rect[3] = pts[np.argmax(diff)] # BL
    return rect
