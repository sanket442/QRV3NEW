from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
from PIL import Image, ImageDraw
import io
import base64
import pandas as pd
import requests
from printer_tsc import print_tsc
from printer_normal import print_normal
import win32print

app = Flask(__name__)
CORS(app)

try:
    from pylibdmtx.pylibdmtx import encode as dmtx_encode
    HAS_DMTX = True
except (ImportError, OSError):
    print("Warning: pylibdmtx library not found. Data Matrix preview will be disabled.")
    HAS_DMTX = False

def generate_qr_base64(data, ecc="L", box_size=10, border=1, code_format="QR", dm_w=None, dm_h=None):
    buffered = io.BytesIO()
    
    img = None
    if code_format == "DM":
        if HAS_DMTX:
            try:
                # Data Matrix Generation
                encoded = dmtx_encode(data.encode('utf-8'))
                img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            except Exception as e:
                print(f"DMTX Generation Error: {e}")
                # Fallback to a placeholder
                img = Image.new('RGB', (100, 100), color=(200, 200, 200))
                from PIL import ImageDraw
                d = ImageDraw.Draw(img)
                d.text((10, 40), "DM Error", fill=(255, 0, 0))
        else:
            # Fallback if library missing: Generate a QR Code instead for visual preview
            # We use version=None (auto) to handle large data
            try:
                # Basic generation for DM fallback
                qr = qrcode.QRCode(version=None, box_size=1, border=1)
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
            except Exception as e:
                img = Image.new('RGB', (150, 50), color=(255, 200, 200))
                from PIL import ImageDraw
                d = ImageDraw.Draw(img)
                d.text((10, 20), "Data Limit", fill=(0,0,0))

        # Data Matrix Resizing Logic (User Dynamic)
        if dm_w and dm_h and int(dm_w) > 0 and int(dm_h) > 0:
             ratio = float(dm_w) / float(dm_h)
             base_dim = 150 
             
             if ratio >= 1:
                 target_w = int(base_dim * ratio)
                 target_h = base_dim
             else:
                 target_w = base_dim
                 target_h = int(base_dim / ratio)
             
             if target_w > 600: target_w = 600
             if target_h > 600: target_h = 600
             
             img = img.resize((target_w, target_h), Image.LANCZOS)
        else:
             img = img.resize((img.width * 10, img.height * 10), Image.NEAREST)
             
    else:
        # Standard QR Generation - ADVANCED MATHEMATICAL MODEL
        # To handle 500+ characters scannably:
        # 1. We optimize ECC (drop to 'L' for large data to save space).
        # 2. We optimize scaling (use higher res + Lanczos for dense codes).
        
        try:
            data_len = len(data)
            
            # Logic: We respect the requested ECC. 
            # If the user wants 'H' for high robustness/density, we give it to them.
            # qrcode library treats ecc parameter as the enum key. 
            
            ecc_map = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }
            ecc_level = ecc_map.get(ecc, qrcode.constants.ERROR_CORRECT_M)
            
            qr = qrcode.QRCode(
                version=None, # Auto-size (will go up to Version 40 if needed)
                error_correction=ecc_level,
                box_size=10, 
                border=4
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Smart Resizing Logic for Preview
            # Use NEAREST for checking dense binary patterns (crisp edges)
            if data_len > 400:
                # High Density: ensure it's large enough to be seen clearly
                target_size = 500
                img = img.resize((target_size, target_size), Image.NEAREST)
            elif data_len > 150:
                img = img.resize((300, 300), Image.NEAREST)
            else:
                img = img.resize((150, 150), Image.NEAREST)
            
        except Exception as e:
             # Handle capacity overflow gracefully
             img = Image.new('RGB', (100, 100), color=(255, 200, 200))
             from PIL import ImageDraw
             d = ImageDraw.Draw(img)
             d.text((10, 40), "Error", fill=(0, 0, 0))
    
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

@app.route('/api/generate_qr', methods=['POST'])
def api_generate_qr():
    data = request.json
    text = data.get('text', '')
    ecc = data.get('ecc', 'L')
    code_format = data.get('format', 'QR') # QR or DM
    dm_w = data.get('dm_w')
    dm_h = data.get('dm_h')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    img_data = generate_qr_base64(text, ecc, code_format=code_format, dm_w=dm_w, dm_h=dm_h)
    return jsonify({"image": img_data})

@app.route('/api/fetch_sheet', methods=['POST'])
def api_fetch_sheet():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Extract Sheet ID and download CSV
        if "/d/" in url:
            sid = url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
            
            # Support Specific Tab (GID)
            import re
            gid_match = re.search(r'[?&]gid=(\d+)', url)
            if gid_match:
                csv_url += f"&gid={gid_match.group(1)}"
        else:
            # Assume it's a direct CSV link or try as is
            csv_url = url

        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV string
        df = pd.read_csv(io.StringIO(response.text))
        
        # Replace NaN with empty string
        df = df.fillna("")
        
        headers = df.columns.tolist()
        rows = df.values.tolist()
        
        return jsonify({"headers": headers, "rows": rows})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/printers', methods=['GET'])
def api_printers():
    try:
        # EnumPrinters(Flags). Flags: 2=LOCAL, 4=CONNECTIONS. Use 6 to get both.
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers_info = win32print.EnumPrinters(flags)
        # Verify structure: (flags, description, name, comment) usually
        printers = [p[2] for p in printers_info]
        return jsonify({"printers": printers})
    except Exception as e:
        print(f"Error listing printers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/print', methods=['POST'])
def api_print():
    data = request.json
    printer_name = data.get('printer')
    rows = data.get('rows', []) # Expected list of {text: "...", qr: "..."}
    printer_type = data.get('printer_type', 'TSC')
    
    # Settings (dimensions in mm usually)
    width = float(data.get('width', 70))
    height = float(data.get('height', 15))
    gap = float(data.get('gap', 2))
    
    # Offsets/Positions
    # DYNAMIC LAYOUT: Defaults if not provided
    if 'qr_x' in data:
        qr_x = float(data['qr_x'])
    else:
        # Default QR to Right side (approx 60% of width)
        qr_x = width * 0.60
        
    if 'text_x' in data:
        text_x = float(data['text_x'])
    else:
        # Default Text to Left margin (3mm)
        text_x = 3.0

    qr_y = float(data.get('qr_y', 2))
    text_y = float(data.get('text_y', 2))
    
    qr_size = float(data.get('qr_size', 12)) # Module Size in Dots
    
    media_type = data.get('media_type', 'CONTINUOUS')
    page_width = float(data.get('page_width', 210))
    page_height = float(data.get('page_height', 297))
    layout = data.get('layout', 'Portrait')

    code_format = data.get('format', 'QR')
    ecc = data.get('ecc', 'L') # Default L, but frontend might send H
    dm_w = data.get('dm_w')
    dm_h = data.get('dm_h')

    if not printer_name or not rows:
        return jsonify({"error": "Missing printer or rows"}), 400

    # --- INTELLIGENT AUTO-SCALING ALGORITHM ---
    # Solution for "Difficulties above 400 chars"
    # 1. Calculate the densest QR in the batch.
    # 2. Ensure it fits within the Label Width (with safe margins).
    
    if printer_type == "TSC" and code_format == "QR":
        try:
            max_len = 0
            for r in rows:
                if len(r.get('qr', '')) > max_len:
                    max_len = len(r['qr'])
            
            # Estimate Version
            # Pure heuristic isn't perfect, so we generate a dummy one to get matrix size
            # We use 'ecc' passed by user (usually 'H' now)
            dummy_qr = qrcode.QRCode(version=None, error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{ecc}"), box_size=1, border=0)
            dummy_qr.add_data("A" * max_len) # Approximation
            # QR Standard requires 4 modules of whitespace (Quiet Zone) around the code.
            # If we cut this too close, scanners fail to detect the finder patterns.
            modules = dummy_qr.modules_count + 8 # Restore 4-module quiet zone (4 left + 4 right)
            
            # Available Width (Remaining space on Right side)
            avail_width_mm = width - qr_x - 1.0 # Restore 1mm safety margin
            avail_dots_w = (avail_width_mm * 8) 
            
            # Width Constraint
            max_safe_cell_size = int(avail_dots_w / modules)
            
            # Height Constraint
            # We need a physical margin for the scanner to "breathe"
            margin_h_mm = 0.5 if height < 30 else 3.0
            avail_height_dots = (height - margin_h_mm) * 8
            max_safe_h = int(avail_height_dots / modules)
            
            # Choose the stricter constraint (usually Height on strip labels)
            if max_safe_h < max_safe_cell_size: 
                max_safe_cell_size = max_safe_h

            # Minimum Safety
            if max_safe_cell_size < 1: max_safe_cell_size = 1
            
            # --- AUTO-SCALING (CAP ONLY) ---
            # We respect the user's requested qr_size (e.g., 6) UNLESS it's too big for the label.
            # If it's too big, we shrink it. We do NOT expand small codes to be huge.
            if qr_size > max_safe_cell_size:
                print(f"Auto-Scaling: Reducing QR from {qr_size} to {max_safe_cell_size} dots due to constraints.")
                qr_size = max_safe_cell_size
            else:
                 print(f"Auto-Scaling: User size {qr_size} fits within safe limit {max_safe_cell_size}. Keeping it.")
                
            # --- VERTICAL CENTERING LOGIC ---
            # ONLY apply if user did not specify a custom Y position
            if 'qr_y' not in data:
                total_qr_dots = modules * qr_size
                total_label_dots = height * 8
                
                if total_qr_dots < total_label_dots:
                    # Center it
                    center_offset_dots = (total_label_dots - total_qr_dots) / 2
                    qr_y = center_offset_dots / 8
                    # ensure reasonable top margin
                    if qr_y < 0.5: qr_y = 0.5
                else:
                    # Overflow case: Align top
                    qr_y = 0
            else:
                 print(f"Using Custom Y={qr_y}mm")
                
             # Log for debug
            print(f"Auto-Centering: Calculated Y={qr_y}mm for Size={qr_size}")

        except Exception as ex:
            print(f"Auto-Scaling Error: {ex}")
            pass

    # --- REVERTED TO PROVEN LOGIC (FROM OLD CODE) ---
    # We maintain the "Auto-Scaling" safety for Version sizing, 
    # but we DO NOT generate bitmaps. We let the printer firmware do it.
    
    # Just ensure we have valid rows
    if not rows: return jsonify({"error": "No rows"}), 400

    # --- ROBUST BITMAP GENERATION (Restored & Optimized) ---
    # This ensures Consistent Physical Size + Max Scannability
    
    for r in rows:
        if printer_type == "TSC" and code_format == "QR":
            try:
                # 1. OPTIMIZE ECC for Density
                # If text is long, drop ECC to 'L' to save space (fewer modules = bigger dots = better scan)
                loop_ecc = ecc
                if len(r['qr']) > 150:
                    loop_ecc = 'L'
                    
                ecc_map = {'L': qrcode.constants.ERROR_CORRECT_L, 'M': qrcode.constants.ERROR_CORRECT_M, 'Q': qrcode.constants.ERROR_CORRECT_Q, 'H': qrcode.constants.ERROR_CORRECT_H}
                ecc_val = ecc_map.get(loop_ecc, qrcode.constants.ERROR_CORRECT_M)

                # 2. Constraints (Label Dimensions)
                # Maximize size within the label height
                avail_h_dots = int((height - 1.0) * 8)
                avail_w_dots = int((width - qr_x - 1.0) * 8)
                max_box_side = min(avail_h_dots, avail_w_dots)
                
                # 3. Generate Base Matrix
                qr = qrcode.QRCode(version=None, error_correction=ecc_val, box_size=1, border=4)
                qr.add_data(r['qr'])
                qr.make(fit=True)
                
                # 4. Calculate Perfect Integer Scale
                # We want the largest integer multiplier (e.g. 3x) that fits in max_box_side
                matrix_dim = qr.modules_count + 8 # +8 for border
                
                scale = max_box_side // matrix_dim
                if scale < 2: scale = 2 # Minimum readability floor (might clip slightly if huge data, but better than unreadable)
                
                final_qr_dim = matrix_dim * scale
                
                # 5. Create Crisp Image
                # Resize matrix to final dimension
                img_raw = qr.make_image(fill_color="black", back_color="white")
                img_crisp = img_raw.resize((final_qr_dim, final_qr_dim), Image.NEAREST)
                
                # 6. Center on Consistent Canvas
                # We create a canvas of 'max_box_side' so all labels look same size
                # Ensure canvas is multiple of 8 width for printer safety
                canvas_dim = (max_box_side // 8) * 8 
                if canvas_dim < final_qr_dim: canvas_dim = final_qr_dim # Expand if needed
                
                final_canvas = Image.new('1', (canvas_dim, canvas_dim), 1) # 1=White
                
                ox = (canvas_dim - final_qr_dim) // 2
                oy = (canvas_dim - final_qr_dim) // 2
                
                final_canvas.paste(img_crisp, (ox, oy))
                r['qr_image'] = final_canvas
                
                print(f"Bitmap Gen: DataLen={len(r['qr'])}, ECC={loop_ecc}, Scale={scale}, Canvas={canvas_dim}")

            except Exception as e:
                print(f"Bitmap Error: {e}") 

    try:
        if printer_type == "TSC":
            print_tsc(
                printer_name, 
                rows,
                width, height, gap,
                qr_size, qr_x, qr_y,
                text_x, text_y,
                media_type,
                code_format=code_format,
                dm_w=dm_w,
                dm_h=dm_h,
                ecc=ecc
            )
        else:
            print_normal(
                printer_name,
                rows,
                page_width, page_height,
                layout
            )
        return jsonify({"status": "success", "message": "Print job sent"})
    except Exception as e:
        # print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
