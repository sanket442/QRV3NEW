# QR Label Generator V2.3 - Update Complete

I have successfully updated the application in `C:\Users\sanke\Desktop\QR_WORK_PART\frontend`.

## What's New in v2.3
1.  **Thermal Printer Optimization**: Switched print layout to use strict page breaks for each label, which prevents drifting on roll printers.
2.  **Silent Printing Guide**: Added instructions to bypass the system print dialog.

## Silent Printing (Cheat Sheet)
To print without the "BS" dialog:
1.  Create a shortcut to Chrome: `"path/to/chrome.exe" --kiosk-printing`
2.  Open the app with this shortcut.
3.  Configure your printer *once* (Ctrl+P) to set the correct size/margins.
4.  Future prints will be instant!

See [silent_printing_guide.md](file:///C:/Users/sanke/.gemini/antigravity/brain/9023eded-6830-4ef8-833f-94f91d8bdc4c/silent_printing_guide.md) for full details.
