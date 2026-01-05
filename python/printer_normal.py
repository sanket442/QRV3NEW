import win32ui
import win32con
import win32print

def print_normal(printer_name, rows, pw, ph, layout):
    """
    Prints a simple list of labels on A4/Normal paper using Windows GDI.
    This avoids complex bitmap manipulation to prevent crashes.
    """
    try:
        # Verify printer exists
        hprinter = win32print.OpenPrinter(printer_name)
        win32print.ClosePrinter(hprinter)
    except Exception as e:
        raise Exception(f"Cannot access printer '{printer_name}'. Is it installed?")

    dc = win32ui.CreateDC()
    try:
        dc.CreatePrinterDC(printer_name)
    except Exception:
        raise Exception(f"Failed to create device context for '{printer_name}'.")

    dc.StartDoc("QR List")

    # simple font
    font_height = 80 # fairly large for readability
    font = win32ui.CreateFont({
        "name": "Arial",
        "height": font_height,
        "weight": 400,
    })
    dc.SelectObject(font)

    # Printing Logic: List view
    y = 100
    x = 100
    page_height_limit = 3000 # Safety margin for typical 300dpi A4
    
    dc.StartPage()
    dc.TextOut(x, y, f"QR Label Report - {len(rows)} Items")
    y += 150

    for i, row in enumerate(rows):
        # Format: 1. Label Text [QR Data]
        line_text = f"{i+1}. {row['text']}  ---  [QR: {row['qr']}]"
        dc.TextOut(x, y, line_text)
        y += font_height + 20
        
        # New page if needed
        if y > page_height_limit:
            dc.EndPage()
            dc.StartPage()
            y = 100

    dc.EndPage()
    dc.EndDoc()
    
    # Cleanup
    del dc
