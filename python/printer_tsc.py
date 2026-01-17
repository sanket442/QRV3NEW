import win32print
import textwrap
from PIL import ImageOps
import qrcode


def mm_to_dots(mm): return int(mm * 8)

def print_tsc(printer, rows, w,h,gap,qr, qx,qy, tx,ty, media, code_format="QR", dm_w=None, dm_h=None, ecc="L"):
    """
    Sends print commands to a TSC printer in batches to prevent positional drift.
    """
    # 0. Coordinate Conversions
    qx = int(qx * 8)
    qy = int(qy * 8)
    tx = int(tx * 8)
    ty = int(ty * 8)

    # 1. Batch Configuration (User requested reset after every 5 tags)
    BATCH_SIZE = 5
    total_rows = len(rows)
    
    print(f"Starting Print Job: {total_rows} tags. Batch Method: {BATCH_SIZE} per job.")

    # 2. Iterate in Batches
    for i in range(0, total_rows, BATCH_SIZE):
        batch_rows = rows[i : i + BATCH_SIZE]
        print(f"Printing batch {i//BATCH_SIZE + 1}...")

        ph = win32print.OpenPrinter(printer)
        try:
            # Start a new document for this batch. 
            # This resets the printer's internal job tracking.
            win32print.StartDocPrinter(ph, 1, ("TSC LABEL BATCH", None, "RAW"))
            
            # Send Setup Commands (Resets sensor/gap tracking for this batch)
            setup_cmd = []
            setup_cmd.append(f"SIZE {w} mm,{h} mm")
            setup_cmd.append(f"GAP {gap} mm,0")
            setup_cmd.append("DIRECTION 1")
            
            # Send Setup
            win32print.WritePrinter(ph, "\r\n".join(setup_cmd).encode('utf-8') + b"\r\n")

            for r in batch_rows:
                cmd = []
                cmd.append("CLS") # Clear image buffer
                
                # --- Text Logic (Smart Check) ---
                limit_width_dots = 0
                if tx < qx:
                    limit_width_dots = qx - tx - 16 # 2mm safety
                else:
                    limit_width_dots = (w * 8) - tx - 8 # End of label
                    
                if limit_width_dots < 50: limit_width_dots = 50
                
                char_width_dots = 9 # Font 2 safe estimate
                max_chars_per_line = int(limit_width_dots / char_width_dots)
                
                y = ty
                original_lines = r["text"].splitlines()
                
                for line in original_lines:
                    wrapped = textwrap.wrap(line, width=max_chars_per_line)
                    for w_line in wrapped:
                        safe_text = w_line.replace('"', '\\"')
                        cmd.append(f"TEXT {tx},{y},\"2\",0,1,1,\"{safe_text}\"")
                        y += 24
                        if y > (h * 8) - 10: break 
                    if y > (h * 8) - 10: break
                
                # --- QR/One-Bit Bitmap Logic ---
                if "qr_image" in r and r["qr_image"] is not None:
                    try:
                        img = r["qr_image"]
                        # Ensure proper mode
                        if img.mode != 'L' and img.mode != '1':
                             img = img.convert('L')
                        
                        # Invert for Thermal (Black=1)
                        img_inv = ImageOps.invert(img.convert('L'))
                        img_bw = img_inv.convert('1')
                        
                        bw = img_bw.width
                        bh = img_bw.height
                        row_bytes = (bw + 7) // 8
                        
                        bitmap_data = img_bw.tobytes()
                        
                        # Send text commands first
                        full_command = "\r\n".join(cmd) + "\r\n"
                        win32print.WritePrinter(ph, full_command.encode('utf-8'))
                        
                        # Send BITMAP command
                        header = f"BITMAP {qx},{qy},{row_bytes},{bh},0,".encode('utf-8')
                        win32print.WritePrinter(ph, header + bitmap_data + b"\r\n")
                        
                        cmd = [] # Reset cmd
                        
                    except Exception as e:
                        print(f"Bitmap Print Error: {e}")
                        # Fallback to Firmware Code
                        cmd.append(f"QRCODE {qx},{qy},{ecc},{qr},A,0,\"{r['qr']}\"")
                else:
                    # --- DYNAMIC SIZE CALCULATION (Per Label) ---
                    # To prevent overflow with high-density data, we calculate the max safe cell size
                    # for this specific label's content.
                    try:
                        # 1. Estimate Complexity (Modules)
                        # using border=0 here because we add the logical quiet zone (+8) manually
                        q_temp = qrcode.QRCode(version=None, box_size=1, border=0)
                        q_temp.add_data(r['qr'])
                        q_temp.make(fit=True)
                        modules = q_temp.modules_count + 8 # Standard 4-module quiet zone on both sides
                        
                        # 2. Calculate Available Space (Height - 2mm margin)
                        avail_dots = (h * 8) - 16 
                        if avail_dots < 50: avail_dots = 50
                        
                        # 3. Calculate Maximum Integer Cell Size that fits
                        max_fit_size = int(avail_dots // modules)
                        if max_fit_size < 1: max_fit_size = 1
                        
                        # 4. Determine Final Size
                        final_qr_size = min(int(qr), max_fit_size)
                        
                    except Exception as e:
                        print(f"Dynamic Calc Error: {e}")
                        final_qr_size = int(qr)
    
                    # Send Firmware Command with DYNAMIC Size
                    if code_format == "DM":
                         dw = int(dm_w) if dm_w else int(qr/10)
                         dh = int(dm_h) if dm_h else int(qr/10)
                         cmd.append(f"DMATRIX {qx},{qy},{dw},{dh},\"{r['qr']}\"")
                    else:
                        cmd.append(f"QRCODE {qx},{qy},{ecc},{final_qr_size},A,0,\"{r['qr']}\"")
                    
                cmd.append("PRINT 1,1")
                
                # Send remaining commands for this label
                full_command = "\r\n".join(cmd) + "\r\n"
                win32print.WritePrinter(ph, full_command.encode('utf-8'))
        
            # End Batch Job
            win32print.EndDocPrinter(ph)
        
        except Exception as e:
            if "Access is denied" in str(e):
                 raise Exception(f"Failed to communicate with '{printer}'. Access Denied.")
            raise e
        finally:
            win32print.ClosePrinter(ph)
