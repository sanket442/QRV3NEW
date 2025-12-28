# How to Skip the Print Dialog (Kiosk Mode)

To make your barcode printer print immediately without asking for settings every time, you can run Chrome/Edge in "Kiosk Printing" mode.

## Step 1: Create a Shortcut
1.  Right-click on your Desktop and select **New > Shortcut**.
2.  Browse to your Chrome or Edge browser executable (e.g., `C:\Program Files\Google\Chrome\Application\chrome.exe`).
3.  Add the following flags to the end of the path:
    ```
    --kiosk-printing
    ```
    **Example Target:**
    `"C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk-printing`

4.  Name the shortcut "QR Label Printer".

## Step 2: Configure Default Printer
1.  Open the app using this new shortcut.
2.  Press **Ctrl+P** (or click Print) **ONE LAST TIME**.
3.  In the dialog:
    -   Select your **Barcode Printer** as the destination.
    -   Ensure **Paper Size** is correct (e.g., User Defined / 100x25mm).
    -   Click **Print**.
4.  Chrome will remember this printer as the default.

## Step 3: One-Click Printing
From now on, whenever you click **Print Labels** in the app while using this shortcut, it will print instantly to that printer without showing the dialog!
