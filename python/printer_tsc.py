import win32print

def mm_to_dots(mm): return int(mm * 8)

def print_tsc(printer, rows, w,h,gap,qr, qx,qy, tx,ty, media, code_format="QR", dm_w=None, dm_h=None, ecc="L"):
    ph = win32print.OpenPrinter(printer)
    try:
        # Tuple structure: (DocName, OutputFile, DataType)
        # We must set OutputFile to None to print to the device.
        # DataType must be "RAW" to send TSPL commands.
        win32print.StartDocPrinter(ph, 1, ("TSC LABEL", None, "RAW"))
    except Exception as e:
        if "Access is denied" in str(e):
            raise Exception(f"Failed to send RAW commands to '{printer}'.\nReason: This printer does generally NOT support Thermal/RAW mode.\n\nSolution: Please select your actual PHYSICAL Barcode/Thermal printer, not 'Microsoft Print to PDF' or similar.")
        raise e
    
    # win32print.StartPagePrinter(ph) # RAW mode doesn't need Page signals typically

    # Convert coordinates from mm to dots (203 DPI standard = 8 dots/mm)
    qx = int(qx * 8)
    qy = int(qy * 8)
    tx = int(tx * 8)
    ty = int(ty * 8)
    
    # 0. Send Setup Commands (ONCE per batch) to prevent sensor reset/drifting
    setup_cmd = []
    setup_cmd.append(f"SIZE {w} mm,{h} mm")
    setup_cmd.append(f"GAP {gap} mm,0")
    setup_cmd.append("DIRECTION 1")
    win32print.WritePrinter(ph, "\r\n".join(setup_cmd).encode('utf-8') + b"\r\n")

    # Import textwrap for handling long labels
    import textwrap

    for r in rows:
        cmd = []
        cmd.append("CLS")
        
        # 1. Print Text (Smart Check)
        # Calculate Safe Width (Text Start -> QR Start - Margin)
        # Assuming Font 2 is approx 8 dots wide + 1 dot spacing = 9 dots/char
        
        # Determine strict boundary: Where does the text area end?
        # If QR is to the right (tx < qx), limit is qx.
        # If QR is to the left (qx < tx), limit is Label Width.
        
        limit_width_dots = 0
        if tx < qx:
            limit_width_dots = qx - tx - 16 # 2mm safety margin
        else:
            limit_width_dots = (w * 8) - tx - 8 # End of label
            
        if limit_width_dots < 50: limit_width_dots = 50 # Minimum safety
        
        # Estimate Check
        char_width_dots = 9 # Font 2 safe estimate
        max_chars_per_line = int(limit_width_dots / char_width_dots)
        
        y = ty
        original_lines = r["text"].splitlines()
        
        # Process each original line (like "Line1\nLine2")
        # And wrap them individually so they don't bleed.
        for line in original_lines:
            wrapped = textwrap.wrap(line, width=max_chars_per_line)
            for w_line in wrapped:
                # Vertical Safety Check: Don't print if we hit the bottom
                # (Assuming standard height or just reasonable limit)
                # But user said "in last cut" -> implies truncation.
                
                safe_text = w_line.replace('"', '\\"')
                cmd.append(f"TEXT {tx},{y},\"2\",0,1,1,\"{safe_text}\"")
                y += 24 # Line height for Font 2 (12 dots font + 12 dots spacing)
                
                # Optional: Stop if too many lines? User said "last cut".
                # If we want to prevent running OFF the label.
                # Let's assume 10 lines max to prevent infinite drift.
                if y > (h * 8) - 10: 
                    break 
            if y > (h * 8) - 10: break
        
        # 2. Print QR (Bitmap Mode for Fidelity)
        # If 'qr_image' is passed in the row (PIL Image), we print it as a BITMAP.
        # This matches the Python preview exactly.
        if "qr_image" in r and r["qr_image"] is not None:
            try:
                img = r["qr_image"]
                
                # Resize if needed (optional, assuming server.py handled sizing)
                # Ensure 1-bit monochrome
                # PIL: 0=Black, 255=White. TSPL: 1=Black, 0=White.
                # So we need 0->1 and 255->0. This is Inversion.
                from PIL import ImageOps
                if img.mode != 'L' and img.mode != '1':
                     img = img.convert('L')
                
                # Invert so that Black(0) becomes White(255) for the logic below? 
                # Wait. TSPL: 1 is Print (Black).
                # We want Black parts of QR to be 1.
                # In PIL '1' mode, value is stored as 0 or 1. 
                # Usually 0 is Black, 1 is White.
                # If we convert straight to bytes, we pack pixels.
                # We need to test. Usually Invert -> Convert '1' works for Thermal.
                
                img_inv = ImageOps.invert(img.convert('L'))
                img_bw = img_inv.convert('1')
                
                bw = img_bw.width
                bh = img_bw.height
                row_bytes = (bw + 7) // 8
                
                bitmap_data = img_bw.tobytes()
                
                # Send text commands first
                full_command = "\r\n".join(cmd) + "\r\n"
                win32print.WritePrinter(ph, full_command.encode('utf-8'))
                
                # Send BITMAP command header
                # BITMAP X,Y,width_bytes,height,mode,bitmap_data
                header = f"BITMAP {qx},{qy},{row_bytes},{bh},0,".encode('utf-8')
                win32print.WritePrinter(ph, header + bitmap_data + b"\r\n")
                
                # Reset cmd for the PRINT command
                cmd = []
                
            except Exception as e:
                print(f"Bitmap Print Error: {e}")
                # Fallback to Firmware Code
                cmd.append(f"QRCODE {qx},{qy},{ecc},{qr},A,0,\"{r['qr']}\"")
        else:
            # Firmware Mode (Fallback)
            if code_format == "DM":
                 dw = int(dm_w) if dm_w else int(qr/10)
                 dh = int(dm_h) if dm_h else int(qr/10)
                 if dw < 1: dw = 6
                 if dh < 1: dh = 6
                 cmd.append(f"DMATRIX {qx},{qy},{dw},{dh},\"{r['qr']}\"")
            else:
                cmd.append(f"QRCODE {qx},{qy},{ecc},{qr},A,0,\"{r['qr']}\"")
            
        cmd.append("PRINT 1,1")
        
        # Send remaining commands
        full_command = "\r\n".join(cmd) + "\r\n"
        win32print.WritePrinter(ph, full_command.encode('utf-8'))

    win32print.EndDocPrinter(ph)
    win32print.ClosePrinter(ph)
