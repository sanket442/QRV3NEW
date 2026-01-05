import os, sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import win32print
import qrcode
import requests
from io import StringIO
from PIL import Image

from app.printer_tsc import print_tsc
from app.printer_normal import print_normal

# ================= APP CONFIG =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# ================= HELPERS =================
def to_mm(val, unit):
    val = float(val)
    if unit == "mm": return val
    if unit == "cm": return val * 10
    return val * 25.4

def google_sheet_to_df(url):
    sid = url.split("/d/")[1].split("/")[0]
    csv = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
    return pd.read_csv(StringIO(requests.get(csv).text))

def detect_cols(df):
    cols = {c.lower().strip(): c for c in df.columns}
    tag = next((v for k,v in cols.items() if k=="tag"), None)
    qr  = next((v for k,v in cols.items() if "unique" in k and "ord" in k), None)
    return tag, qr

# ================= MAIN APP =================
class QRLabelApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("CHAIN N CHAINS | QR Label Printer")
        self.state("zoomed")

        # DATA
        self.rows = []
        self.index = 0

        # VARIABLES
        self.unit = ctk.StringVar(value="mm")
        self.printer_type = ctk.StringVar(value="TSC")
        self.roll_size = ctk.StringVar(value="70x15")
        self.page_size = ctk.StringVar(value="A4")
        self.layout = ctk.StringVar(value="Portrait")
        self.media_type = ctk.StringVar(value="CONTINUOUS")

        self.print_mode = ctk.StringVar(value="ALL")
        self.range_from = ctk.StringVar(value="1")
        self.range_to = ctk.StringVar(value="")
        self.copies = ctk.StringVar(value="1")

        self.build_ui()

    # ================= UI =================
    def build_ui(self):

        # HEADER
        header = ctk.CTkFrame(self, height=70)
        header.pack(fill="x")

        logo_path = os.path.join(ROOT_DIR, "assets", "logo.png")
        if os.path.exists(logo_path):
            logo = ctk.CTkImage(Image.open(logo_path), size=(260, 55))
            ctk.CTkLabel(header, image=logo, text="").pack(side="left", padx=20)

        # BODY (SCROLLABLE)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        card = ctk.CTkFrame(self.scroll, corner_radius=12)
        card.pack(fill="x", padx=10)

        # ================= FILE INPUT =================
        ctk.CTkLabel(card, text="Excel File").grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkButton(card, text="Browse", command=self.load_excel).grid(row=0, column=1)
        self.file_lbl = ctk.CTkLabel(card, text="")
        self.file_lbl.grid(row=0, column=2, padx=10)

        ctk.CTkLabel(card, text="Google Sheet URL").grid(row=1, column=0, sticky="w", padx=10)
        self.sheet_entry = ctk.CTkEntry(card, width=420)
        self.sheet_entry.grid(row=1, column=1, columnspan=2)
        ctk.CTkButton(card, text="Fetch", command=self.load_sheet).grid(row=1, column=3)

        # ================= PRINTER =================
        ctk.CTkLabel(card, text="Printer").grid(row=2, column=0, sticky="w", padx=10)
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        self.printer_box = ctk.CTkComboBox(card, values=printers, width=420)
        self.printer_box.grid(row=2, column=1, columnspan=2)

        ctk.CTkLabel(card, text="Printer Type").grid(row=3, column=0, sticky="w", padx=10)
        ctk.CTkComboBox(card, values=["TSC","NORMAL"],
                        variable=self.printer_type,
                        command=self.toggle_printer_type
        ).grid(row=3, column=1, sticky="w")

        # ================= PREVIEW =================
        preview_frame = ctk.CTkFrame(card)
        preview_frame.grid(row=4, column=0, columnspan=4, pady=15, sticky="ew")

        self.preview = ctk.CTkCanvas(preview_frame, height=140, bg="white")
        self.preview.pack(fill="x", padx=10, pady=10)

        nav = ctk.CTkFrame(card)
        nav.grid(row=5, column=0, columnspan=4)
        ctk.CTkButton(nav, text="< Prev", width=80, command=self.prev).pack(side="left", padx=5)
        self.counter = ctk.CTkLabel(nav, text="0/0")
        self.counter.pack(side="left", padx=10)
        ctk.CTkButton(nav, text="Next >", width=80, command=self.next).pack(side="left", padx=5)

        # ================= PRINT =================
        ctk.CTkButton(card, text="PRINT LABELS",
                      height=45, font=("Segoe UI",14,"bold"),
                      command=self.print_all).grid(row=6, column=0, columnspan=4, sticky="ew", pady=10)

        # ================= ADVANCED =================
        self.adv_btn = ctk.CTkButton(card, text="▶ Advanced Settings",
                                     fg_color="transparent",
                                     command=self.toggle_adv)
        self.adv_btn.grid(row=7, column=0, columnspan=4)

        self.adv = ctk.CTkFrame(card)
        self.adv_visible = False

        self.build_advanced()

    # ================= ADVANCED SETTINGS =================
    def build_advanced(self):

        # UNIT
        ctk.CTkLabel(self.adv, text="Unit").grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkComboBox(self.adv, values=["mm","cm","inch"], variable=self.unit).grid(row=0, column=1)

        # LABEL / QR
        self.fields = {}
        labels = [
            ("Label Width","70"), ("Label Height","15"),
            ("QR Size","12"), ("QR X Offset","50"), ("QR Y Offset","2"),
            ("Text X Offset","3"), ("Text Y Offset","2"),
            ("Page Width","210"), ("Page Height","297"),
            ("Gap","2")
        ]
        for i,(k,v) in enumerate(labels, start=1):
            ctk.CTkLabel(self.adv, text=k).grid(row=i, column=0, sticky="w", padx=10)
            e = ctk.CTkEntry(self.adv, width=80)
            e.insert(0,v)
            e.grid(row=i, column=1)
            self.fields[k] = e

        # TSC OPTIONS
        self.roll_box = ctk.CTkComboBox(self.adv,
                values=["25x15","50x25","70x15","100x50","Custom"],
                variable=self.roll_size,
                command=self.apply_roll_preset)
        self.roll_box.grid(row=1, column=3)

        self.media_box = ctk.CTkComboBox(self.adv,
                values=["CONTINUOUS","DIECUT"],
                variable=self.media_type)
        self.media_box.grid(row=2, column=3)

        # NORMAL OPTIONS
        self.page_box = ctk.CTkComboBox(self.adv,
                values=["A4","A5","Legal","Custom"],
                variable=self.page_size,
                command=self.apply_page_preset)
        self.page_box.grid(row=1, column=5)

        self.layout_box = ctk.CTkComboBox(self.adv,
                values=["Portrait","Landscape"],
                variable=self.layout)
        self.layout_box.grid(row=2, column=5)

        # PRINT RANGE
        ctk.CTkLabel(self.adv, text="Print Mode").grid(row=10, column=0, sticky="w", padx=10)
        ctk.CTkRadioButton(self.adv, text="All Labels",
                           variable=self.print_mode, value="ALL").grid(row=11, column=0)
        ctk.CTkRadioButton(self.adv, text="Custom Range",
                           variable=self.print_mode, value="CUSTOM").grid(row=12, column=0)

        ctk.CTkEntry(self.adv, textvariable=self.range_from, width=60).grid(row=12, column=1)
        ctk.CTkEntry(self.adv, textvariable=self.range_to, width=60).grid(row=12, column=2)
        ctk.CTkEntry(self.adv, textvariable=self.copies, width=60).grid(row=12, column=3)

    # ================= TOGGLES =================
    def toggle_adv(self):
        if self.adv_visible:
            self.adv.pack_forget()
            self.adv_btn.configure(text="▶ Advanced Settings")
        else:
            self.adv.pack(fill="x", pady=10)
            self.adv_btn.configure(text="▼ Advanced Settings")
        self.adv_visible = not self.adv_visible

    def toggle_printer_type(self, *_):
        is_tsc = self.printer_type.get()=="TSC"
        self.roll_box.configure(state="normal" if is_tsc else "disabled")
        self.media_box.configure(state="normal" if is_tsc else "disabled")
        self.page_box.configure(state="disabled" if is_tsc else "normal")
        self.layout_box.configure(state="disabled" if is_tsc else "normal")

    # ================= PRESETS =================
    def apply_roll_preset(self, *_):
        if self.roll_size.get()!="Custom":
            w,h = map(int,self.roll_size.get().split("x"))
            self.fields["Label Width"].delete(0,"end")
            self.fields["Label Width"].insert(0,w)
            self.fields["Label Height"].delete(0,"end")
            self.fields["Label Height"].insert(0,h)

    def apply_page_preset(self, *_):
        presets = {"A4":(210,297),"A5":(148,210),"Legal":(216,356)}
        if self.page_size.get() in presets:
            w,h = presets[self.page_size.get()]
            self.fields["Page Width"].delete(0,"end")
            self.fields["Page Width"].insert(0,w)
            self.fields["Page Height"].delete(0,"end")
            self.fields["Page Height"].insert(0,h)

    # ================= DATA =================
    def load_excel(self):
        f = filedialog.askopenfilename(filetypes=[("Excel","*.xlsx")])
        if not f: return
        df = pd.read_excel(f)
        self.process(df)
        self.file_lbl.configure(text=os.path.basename(f))

    def load_sheet(self):
        df = google_sheet_to_df(self.sheet_entry.get())
        self.process(df)
        self.file_lbl.configure(text="Google Sheet")

    def process(self, df):
        tag, qr = detect_cols(df)
        if not tag or not qr:
            messagebox.showerror("Error","TAG / UNIQUE_ORD_NO not found")
            return
        self.rows = [{"text":str(r[tag]),"qr":str(r[qr])} for _,r in df.iterrows()]
        self.index = 0
        self.draw()

    # ================= PREVIEW =================
    def draw(self):
        self.preview.delete("all")
        if not self.rows: return
        row = self.rows[self.index]
        y=10
        for l in row["text"].splitlines():
            self.preview.create_text(10,y,anchor="nw",text=l)
            y+=18
        img = ImageTk.PhotoImage(qrcode.make(row["qr"]).resize((100,100)))
        self.qr_img = img
        self.preview.create_image(self.preview.winfo_width()-120,20,anchor="nw",image=img)
        self.counter.configure(text=f"{self.index+1}/{len(self.rows)}")

    def next(self):
        if self.index<len(self.rows)-1:
            self.index+=1
            self.draw()

    def prev(self):
        if self.index>0:
            self.index-=1
            self.draw()

    # ================= PRINT =================
    def print_all(self):
        rows = self.rows
        if self.print_mode.get()=="CUSTOM":
            s = int(self.range_from.get())-1
            e = int(self.range_to.get() or len(rows))
            rows = rows[s:e]
        rows = rows * int(self.copies.get())

        u = self.unit.get()
        f = {k: to_mm(v.get(),u) for k,v in self.fields.items()}

        if self.printer_type.get()=="TSC":
            print_tsc(self.printer_box.get(), rows,
                f["Label Width"], f["Label Height"], f["Gap"],
                f["QR Size"], f["QR X Offset"], f["QR Y Offset"],
                f["Text X Offset"], f["Text Y Offset"],
                self.media_type.get()
            )
        else:
            print_normal(self.printer_box.get(), rows,
                f["Page Width"], f["Page Height"],
                self.layout.get()
            )

        messagebox.showinfo("Done","Printing Started")

# ================= RUN =================
if __name__ == "__main__":
    app = QRLabelApp()
    app.mainloop()
