import cv2
import numpy as np

def find_islands(image, x, y, w, h, rows, cols):
    """
    Analyzes the entire selected mathematical box (x, y, w, h) and finds the top
    N (rows * cols) largest discrete pixel islands (contours).
    
    Returns:
        List of bounding boxes [{'bx': bx, 'by': by, 'bw': bw, 'bh': bh}, ...] 
        sorted correctly top-to-bottom, left-to-right.
    """
    x, y, w, h = int(x), int(y), int(w), int(h)
    expected_count = int(rows) * int(cols)
    
    roi_img = image[y:y+h, x:x+w]
    if roi_img.size == 0 or expected_count <= 0:
        return []
        
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    
    # Try different strategies: from safest to most aggressive.
    # We want to find AT LEAST expected_count target islands.
    strategies = [
        # 1. Global Otsu (Perfect for standard clean scans)
        lambda img: cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        # 2. Generous fixed threshold (Catches faint/light pencil marks or thin texts like '1')
        lambda img: cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)[1],
        # 3. Very aggressive fixed threshold (Catches almost everything non-white)
        lambda img: cv2.threshold(img, 240, 255, cv2.THRESH_BINARY_INV)[1],
    ]
    
    top_boxes = []
    
    for strategy in strategies:
        thresh = strategy(gray)
        
        # We MUST use RETR_LIST (not EXTERNAL) because if the bubbles are inside a drawn rectangle 
        # frame on the form, EXTERNAL will only see the outer frame and ignore all the bubbles!
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            continue
            
        raw_boxes = [cv2.boundingRect(c) for c in cnts]
        
        # Filter out absolute noise
        valid_boxes = [(bx, by, bw, bh) for (bx, by, bw, bh) in raw_boxes if bw >= 4 and bh >= 4]
        
        # Sort boxes by bounding area descending
        valid_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
        
        # Dedup heavily overlapping boxes (inner vs outer rings of the same hollow bubble)
        unique_boxes = []
        for (bx, by, bw, bh) in valid_boxes:
            is_duplicate = False
            cx1, cy1 = bx + bw/2.0, by + bh/2.0
            
            for (ubx, uby, ubw, ubh) in unique_boxes:
                cx2, cy2 = ubx + ubw/2.0, uby + ubh/2.0
                
                # If their centers are very close compared to their size, they originate from the same ink blot
                if abs(cx1 - cx2) < max(bw, ubw) * 0.5 and abs(cy1 - cy2) < max(bh, ubh) * 0.5:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                unique_boxes.append((bx, by, bw, bh))
                
        # If we successfully found at least the requested number of boxes, we win!
        if len(unique_boxes) >= expected_count:
            top_boxes = unique_boxes[:expected_count]
            break
            
    # CRITICAL FAILSAFE:
    # If EVEN AFTER trying all aggressive strategies we STILL couldn't find enough islands,
    # we CANNOT just return incomplete islands, because mapping missing shapes will ruin
    # the question numbering (Q1, Q2...). We MUST return exactly N*M cells.
    # Therefore, we generate the perfect mathematical grid as a fallback!
    if len(top_boxes) < expected_count:
        sorted_grid = []
        cell_w = w / cols
        cell_h = h / rows
        for r in range(rows):
            for c in range(cols):
                sorted_grid.append({
                    "bx": int(x + (c * cell_w)),
                    "by": int(y + (r * cell_h)),
                    "bw": int(cell_w),
                    "bh": int(cell_h)
                })
        return sorted_grid
    
    # Now we need to sort these into a logical grid (rows and columns)
    # First sort purely by Y to distribute them into approximate rows
    top_boxes.sort(key=lambda b: b[1])
    
    sorted_grid = []
    # Process row by row
    max_iter_rows = min(rows, len(top_boxes) // cols + 1)
    
    for r in range(rows):
        # Slice out the items belonging to this mathematical row index
        row_items = top_boxes[r * cols : (r + 1) * cols]
        
        # Sort these row items by purely X coordinate (left to right)
        row_items.sort(key=lambda b: b[0])
        
        # Absolute coordinate projection mapping back to original image
        for (bx, by, bw, bh) in row_items:
            sorted_grid.append({
                "bx": x + bx, 
                "by": y + by, 
                "bw": bw, 
                "bh": bh
            })
            
    return sorted_grid

