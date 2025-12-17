import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import cv2
import PIL.Image
import PIL.ImageTk
import threading
import re
import easyocr
import numpy as np
import os
import random
import time
from datetime import datetime
import pytz
NIGERIAN_PLATE_PATTERN = r'[A-Z]{3}-?\d{3}?[A-Z]{2}'

class PlateReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Automatic Car Plate Number Recognition System')
        self.root.geometry('1000x700')
        self.root.configure(bg="#f0f0f0")
        self.reader = None
        self.is_processing = False
        self.setup_ui()
        threading.Thread(target=self.load_ocr, daemon=True).start()

    def load_ocr(self):
        try:
            self.status_var.set("Loading OCR Engine... Please wait.")
            self.reader = easyocr.Reader(['en'], gpu=False) 
            self.root.after(0, lambda: self.status_var.set("Ready"))
            self.root.after(0, lambda: self.detect_btn.config(state=tk.NORMAL))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"Error loading OCR: {error_msg}"))

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#1e3a8a", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame, 
            text="License Plate Recognition", 
            font=("Segoe UI", 24, "bold"), 
            bg="#1e3a8a", 
            fg="white"
        )
        title_label.pack(pady=20)

        subtitle_label = tk.Label(
            header_frame,
            text="Automatic Vehicle Identification System",
            font=("Segoe UI", 10),
            bg="#1e3a8a",
            fg="#93c5fd"
        )
        subtitle_label.place(relx=0.5, rely=0.7, anchor="center")
        control_frame = tk.Frame(self.root, bg="white", pady=20)
        control_frame.pack(fill=tk.X)

        btn_style = {
            "font": ("Segoe UI", 11, "bold"),
            "width": 16,
            "height": 2,
            "bd": 0,
            "relief": tk.FLAT,
            "cursor": "hand2"
        }

        btn_container = tk.Frame(control_frame, bg="white")
        btn_container.pack()

        # Upload button
        upload_btn = tk.Button(
            btn_container,
            text="📁 Upload Image",
            command=self.upload_image,
            bg="#3b82f6",
            fg="white",
            activebackground="#2563eb",
            activeforeground="white",
            **btn_style
        )
        upload_btn.pack(side=tk.LEFT, padx=8)

        # Camera button
        camera_btn = tk.Button(
            btn_container,
            text="📷 Capture Photo",
            command=self.open_camera,
            bg="#8b5cf6",
            fg="white",
            activebackground="#7c3aed",
            activeforeground="white",
            **btn_style
        )
        camera_btn.pack(side=tk.LEFT, padx=8)

        # Detect button
        self.detect_btn = tk.Button(
            btn_container,
            text="🔍 Detect Plate",
            command=self.process_image,
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            state=tk.DISABLED,
            **btn_style
        )
        self.detect_btn.pack(side=tk.LEFT, padx=8)

        # Clear button
        clear_btn = tk.Button(
            btn_container,
            text="🗑️ Clear All",
            command=self.clear_all,
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            **btn_style
        )
        clear_btn.pack(side=tk.LEFT, padx=8)

        # --- Main Content Area with cards ---
        content_frame = tk.Frame(self.root, bg="#f8fafc")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # Left Panel: Original Image Card
        left_panel = tk.Frame(content_frame, bg="white", relief=tk.FLAT, borderwidth=0)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Add subtle shadow effect with frame
        left_shadow = tk.Frame(left_panel, bg="#e2e8f0", height=2)
        left_shadow.pack(fill=tk.X)

        left_header = tk.Frame(left_panel, bg="white", height=50)
        left_header.pack(fill=tk.X)
        left_header.pack_propagate(False)

        tk.Label(
            left_header,
            text="Original Image",
            bg="white",
            font=("Segoe UI", 14, "bold"),
            fg="#1e293b"
        ).pack(pady=15, padx=15, anchor="w")

        self.original_canvas = tk.Label(
            left_panel,
            bg="#f1f5f9",
            text="📸\n\nNo Image Loaded\n\nUpload or capture an image to begin",
            font=("Segoe UI", 11),
            fg="#94a3b8"
        )
        self.original_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Right Panel: Results Card
        right_panel = tk.Frame(content_frame, bg="white", relief=tk.FLAT, borderwidth=0)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Add subtle shadow effect
        right_shadow = tk.Frame(right_panel, bg="#e2e8f0", height=2)
        right_shadow.pack(fill=tk.X)

        right_header = tk.Frame(right_panel, bg="white", height=50)
        right_header.pack(fill=tk.X)
        right_header.pack_propagate(False)

        tk.Label(
            right_header,
            text="Detection Results",
            bg="white",
            font=("Segoe UI", 14, "bold"),
            fg="#1e293b"
        ).pack(pady=15, padx=15, anchor="w")

        self.result_canvas = tk.Label(
            right_panel,
            bg="#f1f5f9",
            text="🎯\n\nProcessed Image\n\nResults will appear here",
            font=("Segoe UI", 11),
            fg="#94a3b8"
        )
        self.result_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 10))

        # Result Details Section
        result_frame = tk.Frame(right_panel, bg="white")
        result_frame.pack(fill=tk.X, padx=15, pady=10)

        # Detected plate number display
        plate_container = tk.Frame(result_frame, bg="#eff6ff", relief=tk.FLAT, bd=2)
        plate_container.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            plate_container,
            text="DETECTED PLATE NUMBER",
            font=("Segoe UI", 9, "bold"),
            bg="#eff6ff",
            fg="#3b82f6"
        ).pack(pady=(10, 5))

        self.plate_number_label = tk.Label(
            plate_container,
            text="---",
            font=("Consolas", 28, "bold"),
            fg="#1e40af",
            bg="#eff6ff"
        )
        self.plate_number_label.pack(pady=(0, 10))

        # Additional info
        info_container = tk.Frame(result_frame, bg="#f8fafc", relief=tk.FLAT)
        info_container.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            info_container,
            text="Detection Details",
            font=("Segoe UI", 9, "bold"),
            bg="#f8fafc",
            fg="#475569"
        ).pack(pady=(8, 5), padx=10, anchor="w")

        self.extra_info_text = tk.Text(
            info_container,
            height=4,
            font=("Segoe UI", 10),
            bg="#f8fafc",
            fg="#64748b",
            wrap="word",
            relief=tk.FLAT,
            bd=0
        )
        self.extra_info_text.pack(pady=(0, 8), padx=10, fill=tk.X)
        self.extra_info_text.insert("1.0", "Awaiting detection...\n\nConfidence, processing time, and other details will appear here.")
        self.extra_info_text.config(state="disabled")

        # Validation status
        self.validation_label = tk.Label(
            result_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#059669"
        )
        self.validation_label.pack(pady=(5, 10))

        # --- Modern Status Bar ---
        status_frame = tk.Frame(self.root, bg="#f1f5f9", height=35)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)

        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Ready")

        status_bar = tk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor=tk.W,
            bg="#f1f5f9",
            fg="#475569",
            font=("Segoe UI", 9),
            padx=20
        )
        status_bar.pack(fill=tk.BOTH, expand=True)

        # Variables
        self.current_image_path = None
        self.cv_image = None

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.current_image_path = file_path
            self.load_and_display_image(file_path)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            self.reset_results()

    def open_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            return
        cam_window = tk.Toplevel(self.root)
        cam_window.title("Camera Capture (Press SPACE to Capture, Q to Quit)")
        
        cam_label = tk.Label(cam_window)
        cam_label.pack()

        def update_cam():
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(rgb_frame)
                imgtk = PIL.ImageTk.PhotoImage(image=img)
                cam_label.imgtk = imgtk
                cam_label.configure(image=imgtk)
                
            if cam_window.winfo_exists():
                cam_window.after(10, update_cam)

        def on_key(event):
            if event.keysym == 'space':
                ret, frame = cap.read()
                if ret:
                    # Save temp file
                    temp_path = "temp_capture.jpg"
                    cv2.imwrite(temp_path, frame)
                    self.current_image_path = temp_path
                    self.load_and_display_image(temp_path)
                    self.status_var.set("Image captured from camera")
                    self.reset_results()
                    close_cam()
            elif event.keysym == 'q':
                close_cam()

        def close_cam():
            cap.release()
            cam_window.destroy()

        cam_window.bind('<Key>', on_key)
        cam_window.protocol("WM_DELETE_WINDOW", close_cam)
        update_cam()

    def load_and_display_image(self, path):
        try:
            # Load with OpenCV
            self.cv_image = cv2.imread(path)
            
            if self.cv_image is None:
                messagebox.showerror("Error", "Failed to load image")
                return
            
            # Convert to RGB for Tkinter
            rgb_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
            # Resize for display
            pil_image.thumbnail((400, 400))
            tk_image = PIL.ImageTk.PhotoImage(pil_image)
            
            self.original_canvas.configure(image=tk_image, text="")
            self.original_canvas.image = tk_image
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def process_image(self):
        if self.cv_image is None:
            messagebox.showwarning("Warning", "Please upload or capture an image first.")
            return

        if not self.reader:
            messagebox.showwarning("Warning", "OCR Engine is still loading. Please wait.")
            return

        if self.is_processing:
            messagebox.showinfo("Info", "Already processing an image. Please wait.")
            return

        self.is_processing = True
        self.status_var.set("Processing... Detecting text...")
        self.root.update_idletasks()

        threading.Thread(target=self.run_ocr, daemon=True).start()

    def format_plate_number(self, text):
        if not text:
            return None
        text = text.upper()
        map_similar_values = {
            "0": "O", "O": "0",
            "1": "I", "I": "1", "L": "1",
            "2": "Z", "Z": "2",
            "5": "S", "S": "5",
            "6": "G", "G": "6",
            "8": "B", "B": "8",
            "9": "G", "Q": "9",
            "4": "A", "A": "4",
            "7": "T", "T": "7",
        }
        clean_text = text.replace(" ", "").replace("-", "").upper()
        if len(clean_text) != 8:
            return None
        if (clean_text[:3].isalpha() and clean_text[3:6].isdigit() and clean_text[6:].isalpha()):
            return f"{clean_text[:3]}-{clean_text[3:6]}{clean_text[6:]}"
        corrected = list(clean_text)

        for i in range(0, 3):  
            if not corrected[i].isalpha() and corrected[i] in map_similar_values:
                corrected[i] = map_similar_values[corrected[i]]

        for i in range(3, 6):
            if not corrected[i].isdigit() and corrected[i] in map_similar_values:
                corrected[i] = map_similar_values[corrected[i]]

        for i in range(6, 8):
            if not corrected[i].isalpha() and corrected[i] in map_similar_values:
                corrected[i] = map_similar_values[corrected[i]]

        corrected_text = "".join(corrected)
        if (corrected_text[:3].isalpha() and corrected_text[3:6].isdigit() and corrected_text[6:].isalpha()):
            return f"{corrected_text[:3]}-{corrected_text[3:6]}{corrected_text[6:]}"

        return None

    def additional_details(self, text, max_conf):
        if max_conf:
            max_val = round(max_conf * 100, 2)
        value = ""
        nigerian_lga_codes = {
        # Lagos State
        "AAA": "Lagos Island LG",
        "AGL": "Ajeromi Ifelodun LG",
        "AKD": "Ibeju Lekki LGA (Akodo)",
        "APP": "Apapa LG",
        "BDG": "Badagry LG",
        "EKY": "Eti-Osa LG (Ikoyi)",
        "EPE": "Epe LG",
        "FKJ": "Ifako Ijaiye LG",
        "FST": "Amuwo Odofin LGA (Festac)",
        "GGE": "Agege LG",
        "JJJ": "Ojo LG",
        "KJA": "Ikeja LG",
        "KRD": "Ikorodu LG",
        "KSF": "Kosofe LG",
        "KTU": "Alimosho LGA (Ikotun)",
        "LND": "Lagos Mainland LG",
        "LSD": "Oshodi Isolo LG",
        "LSR": "Surulere LG",
        "MUS": "Mushin LG",
        "SMK": "Somolu LG",

        # FCT Abuja
        "ABC": "Abuja Municipal Council (AMAC)",
        "BWR": "Bwari Area Council",
        "KWL": "Kwali Area Council",
        "RSH": "Karshi Area Council",

        # Oyo State
        "AME": "Arowomole (Ogbomoso)",
        "BDJ": "Bodija (Ibadan)",
        "GBR": "Igbo Ora",
        "LUY": "Oluyole (Ibadan)",
        "MAP": "Mapo (Ibadan)",
        "NRK": "Onireke (Ibadan)",
        "SEY": "Iseyin",

        # Rivers State
        "ABM": "Akukutoru",
        "ABU": "Aboa/Odual",
        "AHD": "Ahoada-East",
        "BGM": "Asari-Toru",
        "BNY": "Bonny",
        "BRR": "Khana",
        "DEG": "Degema",
        "GGU": "Ogu/Bolo",
        "KHE": "Etche",
        "KNM": "Ahoada-West",
        "KPR": "Gokana",
        "KRK": "Okirika",
        "MHA": "Emuoha",
        "NCH": "Eleme",
        "NDN": "Andoni",
        "PBT": "Opobo/Nkoro",
        "RGM": "Ogba/Egbema/Ndoni",
        "RUM": "Onia/Akpor",
        "SKP": "Ikwerre",

        # Ogun State
        "ABE": "Abeokuta South LG",
        "ADG": "Ado-Odo/Ota LG",
        "EWE": "Ewekoro LG",
        "AAB": "Abeokuta South LG",
        "ABG": "Ogun Waterside LG (Abigi)",
        "IAR": "Ilaro LG",
        "GBE": "Ijebu East LG (Ogbere)",
        
        # Ondo State
        "AKR": "Akure South LG",
        "FFN": "Ose LG (Ifon)",
        "JTA": "Akure North LG (Ita Ogbolu)",
        "KEK": "Ile Oluji LG",
        "KTP": "Okitipupa LG",
        "NND": "Ondo West LG",
        "REE": "Odigbo LG (Ore)",
        "SUA": "Akoko South East LG (Isua)",
        "WEN": "Idanre LG (Owena)",

        # Ekiti State
        "ADK": "Ado Ekiti",
        "AMK": "Aramoko",
        "EFY": "Efon Alaye",
        "EMR": "Emure Ekiti",
        "KER": "Ikere Ekiti",
        "KLE": "Ikole Ekiti",
        "TUN": "Moba LG (Otun)",

        # Kano State
        "DAL": "Dala",
        "DTF": "Dawakin Tofa",
        "GWL": "Gwale",
        "KMC": "Kano Municipal",
        "NSR": "Nasarawa",
        "TRN": "Tarauni",
        "UGG": "Ungogo",

        # Cross River State
        "ANA": "Calabar South (Anatigha)",
        "BKS": "Bakassi",
        "BJE": "Boki (Boje)",
        "BRA": "Obubra",
        "BNS": "Obanliku (Sankwala)",
        "CAL": "Calabar Municipal",
        "CKK": "Yala (Okpoma)",
        "DUK": "Odukpani",
        "EFE": "Etung (Effraya)",
        "GEP": "Yakurr",
        "GGJ": "Ogoja",
        "KAM": "Akamkpa",
        "KMM": "Ikom",
        "TGD": "Abi (Itigidi)",
        "UDU": "Obudu",

        # Abia State
        "ABA": "Aba South",
        "ACH": "Arochukwu",
        "BND": "Bende",
        "EZA": "Aba North",
        "KPU": "Isiala-Ngwa North",
        "KWU": "Ikwuano",
        "OHF": "Ohafia",

        # Katsina State
        "BAT": "Batagarawa",
        "BDW": "Bindawa",
        "BKR": "Bakori",
        "BRE": "Baure",
        "CRC": "Charanchi",
        "DDM": "Dandume",
        "DJA": "Danja",
        "DTS": "Dutse",
        "DMS": "Danmusa",
        "JBY": "Jibia",
        "KFY": "Kafur",
        "KTN": "Katsina",
        "MLF": "Malumfashi",
        "NGW": "Ingawa",

        # Osun State
        "EDE": "Ede",
        "FNN": "Ifon Osun",
        "GBN": "Gbongan",
        "KER": "Ikire",
        "LES": "Ilesa",
        "SGB": "Osogbo",
    }

        first_name = ["Chinedu","Fatima","Ayodele","Aminu","Ngozi","Tunde","Hauwa","Emeka","Sade","Mohammed",
                      "Ifunanya","Olumide","Zainab","Obinna","Abiola","Musa","Ifeoma","Segun","Aisha",
                      "Chisom","Damilola","Uche","Bola","Abdulahi","Adaobi","Kayode","Maryam","Ibrahim","Funmi","Efe"]
        surname = [ "Adekunle","Okoro","Malami","Dike","Ogunyemi","Abdullahi","Nwosu","Bello",
                   "Adebayo","Okeke","Aliyu","Eze","Adewale","Usman","Chukwu","Dada","Gambo",
                   "Ibekwe","Lawal","Nwafor","Oyelade","Sanusi","Ugwuanyi","Yusuf","Akinola","Audu","Idowu","Mustapha","Peters","Williams"]
        name = random.choice(surname) + " " + random.choice(first_name)
        oyo_timezone = pytz.timezone('Africa/Lagos')
        current_time = datetime.now(oyo_timezone)
        if text:
            prefix = text[:3]
            if prefix in nigerian_lga_codes:
                value = nigerian_lga_codes[prefix]
        context = {
            "value": value,
            "name": name,
            "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "vehicle_type": "Private Vehicle",
            "Confidence": max_val if max_conf else "N/A"
        }
        
        return context
    def run_ocr(self):
        try:
            gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
            bfilter = cv2.bilateralFilter(gray, 11, 17, 17)

            results = self.reader.readtext(
                bfilter,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
            )

            best_match = None
            detected_text = ""
            bbox = None
            candidates = []

            for (box, text, prob) in results:
                clean_text = text.replace(" ", "").replace("-", "").upper()
                candidates.append((clean_text, text, box, prob))

            STRICT_PATTERN = r'^[A-Z]{3}\d{3}[A-Z]{2}$'

            regex_candidates = [c for c in candidates if re.match(STRICT_PATTERN, c[0])]

            if regex_candidates:
                best_candidate = max(regex_candidates, key=lambda x: x[3])
                best_match = best_candidate[0]
                detected_text = best_candidate[1]
                bbox = best_candidate[2]
            else:
                slogan_keywords = [
                    "FEDERAL", "REPUBLIC", "CENTRE", "CENTER",
                    "EXCELLENCE", "STATE", "NIGERIA", "GOVERNMENT"
                ]

                max_conf = 0

                for (clean, text, box, prob) in candidates:
                    if any(keyword in clean for keyword in slogan_keywords):
                        continue
                    if len(clean) < 6:
                        continue

                    has_letters = any(c.isalpha() for c in clean)
                    has_numbers = any(c.isdigit() for c in clean)

                    if has_letters and has_numbers and prob > max_conf:
                        max_conf = prob
                        best_match = clean
                        detected_text = text
                        bbox = box

            # Validation and Formatting
            is_valid = False

            if best_match:
                # FORMAT FIRST
                formatted_text = self.format_plate_number(best_match)
                extra_text = self.additional_details(best_match, max_conf)
                if formatted_text:  # formatting succeeded
                    is_valid = True

                # Display result
                self.root.after(0,
                    lambda: self.display_result(formatted_text if formatted_text else best_match, extra_text,
                                                is_valid, bbox)
                )
            else:
                self.root.after(0, lambda: self.display_failure())

        except Exception as e:
            print(e)
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

        finally:
            self.root.after(0, self.finish_processing)

    def finish_processing(self):
        self.is_processing = False
        self.detect_btn.config(state=tk.NORMAL)

    def display_result(self, text, extra_text, is_valid, bbox):
        area = extra_text.get("value", "Unknown LGA")
        name = extra_text.get("name", "Unknown Owner")
        current_time = extra_text.get("current_time", "Unknown Time")
        vehicle_type = extra_text.get("vehicle_type", "Unknown Type")
        confidence = extra_text.get("Confidence", "N/A")
        self.extra_info_text.config(state="normal")
        self.extra_info_text.delete("1.0", tk.END)
        self.extra_info_text.insert(
            "1.0", 
            f"Additional Info:\n"
            f"Vehicle was registered in {area}\n"
            f"Owner is: {name}\n "
            f"Vehicle Type: {vehicle_type}\n "
            f"Time of Detection: {current_time}\n"
            f"OCR Confidence: {confidence}"
            )
        self.extra_info_text.config(state="disabled")
        self.plate_number_label.config(text=text)
        if is_valid:
            self.validation_label.config(text="Valid Plate Number Format", fg="green")
        else:
            self.validation_label.config(text="Invalid Format / Unrecognized", fg="orange")
        
        self.status_var.set("Detection Complete")

        if bbox:
            top_left = tuple(map(int, bbox[0]))
            bottom_right = tuple(map(int, bbox[2]))
            
            processed_img = self.cv_image.copy()
            cv2.rectangle(processed_img, top_left, bottom_right, (0, 255, 0), 5)

            rgb_image = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            pil_image.thumbnail((400, 400))
            tk_image = PIL.ImageTk.PhotoImage(pil_image)
            
            self.result_canvas.configure(image=tk_image, text="")
            self.result_canvas.image = tk_image

    def display_failure(self):
        self.plate_number_label.config(text="No Plate Found")
        self.validation_label.config(text="", fg="black")
        self.status_var.set("No text detected that resembles a license plate.")
        self.finish_processing()

    def clear_all(self):
        self.current_image_path = None
        self.cv_image = None
        self.original_canvas.configure(image="", text="No Image")
        self.result_canvas.configure(image="", text="Processed Image")
        self.plate_number_label.config(text="---")
        self.validation_label.config(text="")
        self.extra_info_text.config(state="normal")
        self.extra_info_text.delete("1.0", tk.END )
        self.extra_info_text.insert("1.0", "Awaiting detection...\n\nConfidence, processing time, and other details will appear here.")
        self.status_var.set("Ready")

    def reset_results(self):
        self.result_canvas.configure(image="", text="Processed Image")
        self.extra_info_text.config(state="normal")
        self.plate_number_label.config(text="---")
        self.validation_label.config(text="")


if __name__ == "__main__":
    root = tk.Tk()
    app = PlateReaderApp(root)
    root.mainloop()