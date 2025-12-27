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
from datetime import datetime
import pytz
import sqlite3
from database import Database
from videostream import VideoStreamWindow
from result import ResultsWindow
from history import HistoryPanel

PLATE_PATTERNS = {
    'standard': r'^[A-Z]{3}-?\d{3}[A-Z]{2}$', 
    'government': r'^[A-Z]{2}-?\d{2,4}-?[A-Z]{2}$',  
    'police': r'^(POL|NPF)-?\d{4,5}[A-Z]?$', 
    'military': r'^(NA|NAF|NN)-?\d{3,5}[A-Z]?$', 
    'diplomatic': r'^(CD|CMD|CC)-?\d{3,4}[A-Z]?$',
}
class PlateReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('ANPR System - License Plate Recognition')
        self.root.geometry('1600x900')
        self.root.configure(bg="#0f172a")
        self.reader = None
        self.is_processing = False
        self.database = Database()
        self.setup_ui()
        threading.Thread(target=self.load_ocr, daemon=True).start()

    def load_ocr(self):
        try:
            self.status_var.set("Initializing OCR Engine...")
            self.reader = easyocr.Reader(['en'], gpu=False) 
            self.root.after(0, lambda: self.status_var.set("System Ready"))
            self.root.after(0, lambda: self.detect_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.video_btn.config(state=tk.NORMAL))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"Error: {error_msg}"))

    def setup_ui(self):
        # Main container with history panel
        main_container = tk.Frame(self.root, bg="#0f172a")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # History panel on the right
        self.history_panel = HistoryPanel(main_container, self.database)
        self.history_panel.frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_panel.refresh()
        
        # Main content area
        content_container = tk.Frame(main_container, bg="#0f172a")
        content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Top navigation bar
        nav_bar = tk.Frame(content_container, bg="#1e293b", height=80)
        nav_bar.pack(fill=tk.X)
        nav_bar.pack_propagate(False)
        
        # Logo section
        logo_frame = tk.Frame(nav_bar, bg="#1e293b")
        logo_frame.pack(side=tk.LEFT, padx=40, pady=20)
        
        tk.Label(
            logo_frame,
            text="ANPR",
            font=("Segoe UI", 20, "bold"),
            bg="#1e293b",
            fg="#10b981"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            logo_frame,
            text=" SYSTEM",
            font=("Segoe UI", 20, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT)
        
        # Subtitle
        tk.Label(
            logo_frame,
            text="  |  Automatic Number Plate Recognition",
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#64748b"
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        status_frame = tk.Frame(nav_bar, bg="#1e293b")
        status_frame.pack(side=tk.RIGHT, padx=40)
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 16),
            bg="#1e293b",
            fg="#fbbf24"
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Main content area
        content_area = tk.Frame(content_container, bg="#0f172a")
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # Hero section
        hero_section = tk.Frame(content_area, bg="#0f172a")
        hero_section.pack(fill=tk.BOTH, expand=True, padx=60, pady=40)
        
        # Center container
        center_container = tk.Frame(hero_section, bg="#0f172a")
        center_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Upload area card
        upload_card = tk.Frame(
            center_container, 
            bg="#1e293b", 
            highlightbackground="#334155", 
            highlightthickness=2,
            width=750,
            height=450
        )
        upload_card.pack()
        upload_card.pack_propagate(False)
        
        # Image preview area
        preview_frame = tk.Frame(upload_card, bg="#0f172a")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        self.original_canvas = tk.Label(
            preview_frame,
            bg="#0f172a",
            fg="#64748b",
            font=("Segoe UI", 13)
        )
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initial placeholder
        self.show_placeholder()
        
        # Action buttons section
        button_section = tk.Frame(hero_section, bg="#0f172a")
        button_section.pack(pady=(30, 0))
        
        btn_style = {
            "font": ("Segoe UI", 11, "bold"),
            "bd": 0,
            "relief": tk.FLAT,
            "cursor": "hand2",
            "padx": 25,
            "pady": 16
        }
        
        # Upload button
        upload_btn = tk.Button(
            button_section,
            text="📁  Upload Image",
            command=self.upload_image,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            **btn_style
        )
        upload_btn.pack(side=tk.LEFT, padx=6)
        
        # Camera button
        camera_btn = tk.Button(
            button_section,
            text="📷  Capture Photo",
            command=self.open_camera,
            bg="#7c3aed",
            fg="#ffffff",
            activebackground="#6d28d9",
            activeforeground="#ffffff",
            **btn_style
        )
        camera_btn.pack(side=tk.LEFT, padx=6)
        
        # Video stream button
        self.video_btn = tk.Button(
            button_section,
            text="📹  Video Stream",
            command=self.open_video_stream,
            bg="#f59e0b",
            fg="#ffffff",
            activebackground="#d97706",
            activeforeground="#ffffff",
            state=tk.DISABLED,
            **btn_style
        )
        self.video_btn.pack(side=tk.LEFT, padx=6)
        
        # Detect button
        self.detect_btn = tk.Button(
            button_section,
            text="🔍  Detect Plate",
            command=self.process_image,
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            state=tk.DISABLED,
            **btn_style
        )
        self.detect_btn.pack(side=tk.LEFT, padx=6)
        
        # Clear button
        clear_btn = tk.Button(
            button_section,
            text="🗑️  Clear",
            command=self.clear_all,
            bg="#475569",
            fg="#f1f5f9",
            activebackground="#334155",
            activeforeground="#ffffff",
            **btn_style
        )
        clear_btn.pack(side=tk.LEFT, padx=6)
        
        # Add hover effects
        for btn, hover_color, normal_color in [
            (upload_btn, "#1d4ed8", "#2563eb"),
            (camera_btn, "#6d28d9", "#7c3aed"),
            (self.video_btn, "#d97706", "#f59e0b"),
            (self.detect_btn, "#047857", "#059669"),
            (clear_btn, "#334155", "#475569")
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=hover_color: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal_color: b.config(bg=c))
        
        self.current_image_path = None
        self.cv_image = None

    def open_video_stream(self):
        """Open video stream window"""
        VideoStreamWindow(self.root, self)

    def show_placeholder(self):
        # Clear any existing children
        for widget in self.original_canvas.winfo_children():
            widget.destroy()
        
        placeholder_frame = tk.Frame(self.original_canvas, bg="#0f172a")
        placeholder_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(
            placeholder_frame,
            text="📸",
            font=("Segoe UI", 72),
            bg="#0f172a",
            fg="#334155"
        ).pack()
        
        tk.Label(
            placeholder_frame,
            text="No Image Loaded",
            font=("Segoe UI", 18, "bold"),
            bg="#0f172a",
            fg="#e2e8f0"
        ).pack(pady=(20, 10))
        
        tk.Label(
            placeholder_frame,
            text="Upload an image or capture from camera to begin",
            font=("Segoe UI", 11),
            bg="#0f172a",
            fg="#64748b"
        ).pack()

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.current_image_path = file_path
            self.load_and_display_image(file_path)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            self.status_dot.config(fg="#10b981")

    def open_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            return
        
        cam_window = tk.Toplevel(self.root)
        cam_window.title("Camera Capture")
        cam_window.geometry("800x650")
        cam_window.configure(bg="#0f172a")
        
        # Header
        header = tk.Frame(cam_window, bg="#1e293b", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="Camera Capture",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header,
            text="Press SPACE to capture  •  Press Q to quit",
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#64748b"
        ).pack(side=tk.RIGHT, padx=20)
        
        cam_label = tk.Label(cam_window, bg="#0f172a")
        cam_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        def update_cam():
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(rgb_frame)
                img.thumbnail((760, 570))
                imgtk = PIL.ImageTk.PhotoImage(image=img)
                cam_label.imgtk = imgtk
                cam_label.configure(image=imgtk)
                
            if cam_window.winfo_exists():
                cam_window.after(10, update_cam)

        def on_key(event):
            if event.keysym == 'space':
                ret, frame = cap.read()
                if ret:
                    temp_path = "temp_capture.jpg"
                    cv2.imwrite(temp_path, frame)
                    self.current_image_path = temp_path
                    self.load_and_display_image(temp_path)
                    self.status_var.set("Image captured from camera")
                    self.status_dot.config(fg="#10b981")
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
            self.cv_image = cv2.imread(path)
            
            if self.cv_image is None:
                messagebox.showerror("Error", "Failed to load image")
                return
            
            # Clear placeholder widgets
            for widget in self.original_canvas.winfo_children():
                widget.destroy()
            
            rgb_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            pil_image.thumbnail((690, 390))
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
        self.status_var.set("Processing image...")
        self.status_dot.config(fg="#fbbf24")
        self.root.update_idletasks()

        threading.Thread(target=self.run_ocr, daemon=True).start()

    def identify_plate_type(self, text):
        """Identify which type of plate this is"""
        clean_text = text.replace(" ", "").replace("-", "").upper()
        
        for plate_type, pattern in PLATE_PATTERNS.items():
            if re.match(pattern, clean_text):
                return plate_type
        
        return None

    def format_plate_number(self, text, plate_type):
        """Format plate number based on its type"""
        if not text:
            return None
            
        text = text.upper()
        clean_text = text.replace(" ", "").replace("-", "").upper()
        
        # Character similarity mappings
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
        
        if plate_type == 'standard':
            if len(clean_text) != 8:
                return None
            
            if (clean_text[:3].isalpha() and clean_text[3:6].isdigit() and clean_text[6:].isalpha()):
                return f"{clean_text[:3]}-{clean_text[3:6]}{clean_text[6:]}"
            
            # Try to correct the format
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
        
        elif plate_type in ['government', 'police', 'military', 'diplomatic']:
            # Return as-is with proper formatting
            if '-' not in clean_text and len(clean_text) > 4:
                # Add hyphens intelligently
                if plate_type == 'government':
                    if len(clean_text) >= 6:
                        return f"{clean_text[:2]}-{clean_text[2:-2]}-{clean_text[-2:]}"
                elif plate_type in ['police', 'military']:
                    prefix_len = 3 if clean_text[:3] in ['POL', 'NPF', 'NAF'] else 2
                    return f"{clean_text[:prefix_len]}-{clean_text[prefix_len:]}"
                elif plate_type == 'diplomatic':
                    prefix_len = 3 if clean_text[:3] in ['CMD'] else 2
                    return f"{clean_text[:prefix_len]}-{clean_text[prefix_len:]}"
            return clean_text
        
        return None

    def detect_plate_color(self, bbox, image=None):
        """Detect the dominant color of the license plate region"""
        if bbox is None:
            return 'unknown'
        
        if image is None:
            image = self.cv_image
        
        try:
            # Get bounding box coordinates
            top_left = tuple(map(int, bbox[0]))
            bottom_right = tuple(map(int, bbox[2]))
            
            # Extract plate region
            x1, y1 = top_left
            x2, y2 = bottom_right
            
            # Add padding to capture more of the plate
            height, width = image.shape[:2]
            padding = 10
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)
            
            plate_region = image[y1:y2, x1:x2]
            
            if plate_region.size == 0:
                return 'unknown'
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(plate_region, cv2.COLOR_BGR2HSV)
            
            # Define color ranges in HSV
            # Blue range
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            
            # Red range (red wraps around in HSV, so we need two ranges)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            
            # Create masks
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            # Count pixels
            blue_pixels = cv2.countNonZero(blue_mask)
            red_pixels = cv2.countNonZero(red_mask)
            
            # Determine dominant color
            if blue_pixels > red_pixels and blue_pixels > 100:
                return 'blue'
            elif red_pixels > blue_pixels and red_pixels > 100:
                return 'red'
            else:
                return 'unknown'
                
        except Exception as e:
            print(f"Color detection error: {e}")
            return 'unknown'

    def get_vehicle_details(self, text, plate_type, max_conf, plate_color):
        """Get vehicle details based on plate type and color"""
        
        # Plate categories
        plate_categories = {
            'standard': 'Standard Private/Commercial',
            'government': 'Government Official',
            'police': 'Nigeria Police Force',
            'military': 'Military Personnel',
            'diplomatic': 'Diplomatic Corps'
        }
        
        confidence = round(max_conf * 100, 2) if max_conf else "N/A"
        plate_category = plate_categories.get(plate_type, 'Unknown')
        
        # Determine vehicle type based on plate type and color
        if plate_type == 'standard':
            if plate_color == 'blue':
                vehicle_type = 'Private Vehicle (Blue Plate)'
            elif plate_color == 'red':
                vehicle_type = 'Commercial Bus/Van/Truck (Red Plate)'
            else:
                vehicle_type = 'Private/Commercial Vehicle'
        elif plate_type == 'government':
            vehicle_type = 'Government Official Vehicle'
        elif plate_type == 'police':
            vehicle_type = 'Nigeria Police Force Vehicle'
        elif plate_type == 'military':
            vehicle_type = 'Nigerian Armed Forces Vehicle'
        elif plate_type == 'diplomatic':
            vehicle_type = 'Diplomatic Mission Vehicle'
        else:
            vehicle_type = 'Unknown Vehicle Type'
        
        # Registration area and owner info
        registration_area = "Not Available"
        registered_owner = "Not Available"
        
        # Only populate for standard plates
        if plate_type == 'standard' and text:
            nigerian_lga_codes = {
                "AAA": "Lagos Island LG", "AGL": "Ajeromi Ifelodun LG", "AKD": "Ibeju Lekki LGA (Akodo)",
                "APP": "Apapa LG", "BDG": "Badagry LG", "EKY": "Eti-Osa LG (Ikoyi)", "EPE": "Epe LG",
                "FKJ": "Ifako Ijaiye LG", "FST": "Amuwo Odofin LGA (Festac)", "GGE": "Agege LG",
                "JJJ": "Ojo LG", "KJA": "Ikeja LG", "KRD": "Ikorodu LG", "KSF": "Kosofe LG",
                "KTU": "Alimosho LGA (Ikotun)", "LND": "Lagos Mainland LG", "LSD": "Oshodi Isolo LG",
                "LSR": "Surulere LG", "MUS": "Mushin LG", "SMK": "Somolu LG", "ABC": "Abuja Municipal Council (AMAC)",
                "BWR": "Bwari Area Council", "KWL": "Kwali Area Council", "RSH": "Karshi Area Council",
            }
            
            prefix = text[:3]
            if prefix in nigerian_lga_codes:
                registration_area = nigerian_lga_codes[prefix]
                # Get consistent owner name from database
                registered_owner = self.database.get_or_create_owner(text, registration_area)
        elif plate_type == 'government':
            registration_area = "Federal/State Government"
            registered_owner = "Government Agency"
        elif plate_type == 'police':
            registration_area = "Nigeria Police Force"
            registered_owner = "NPF Command"
        elif plate_type == 'military':
            registration_area = "Nigerian Armed Forces"
            registered_owner = "Military Command"
        elif plate_type == 'diplomatic':
            registration_area = "Diplomatic Mission"
            registered_owner = "Embassy/Consulate"
        
        # Get current time
        oyo_timezone = pytz.timezone('Africa/Lagos')
        current_time = datetime.now(oyo_timezone).strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "registration_area": registration_area,
            "registered_owner": registered_owner,
            "current_time": current_time,
            "vehicle_type": vehicle_type,
            "plate_category": plate_category,
            "confidence": confidence
        }
        
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
            max_conf = 0
            best_plate_type = None

            for (box, text, prob) in results:
                clean_text = text.replace(" ", "").replace("-", "").upper()
                candidates.append((clean_text, text, box, prob))

            # Filter out slogans
            slogan_keywords = [
                "FEDERAL", "REPUBLIC", "CENTRE", "CENTER",
                "EXCELLENCE", "STATE", "NIGERIA", "GOVERNMENT"
            ]

            # Try to match against all plate patterns
            for (clean, text, box, prob) in candidates:
                # Skip slogans
                if any(keyword in clean for keyword in slogan_keywords):
                    continue
                if len(clean) < 5:
                    continue

                # Check against all patterns
                for plate_type, pattern in PLATE_PATTERNS.items():
                    if re.match(pattern, clean):
                        if prob > max_conf:
                            max_conf = prob
                            best_match = clean
                            detected_text = text
                            bbox = box
                            best_plate_type = plate_type
                        break

            # If no pattern match, try fuzzy matching
            if not best_match:
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
                        best_plate_type = 'standard'  # Default to standard

            is_valid = False
            processed_img = None

            if best_match:
                # Identify plate type if not already identified
                if not best_plate_type:
                    best_plate_type = self.identify_plate_type(best_match)
                    if not best_plate_type:
                        best_plate_type = 'standard'
                
                # Detect plate color
                plate_color = self.detect_plate_color(bbox)
                
                formatted_text = self.format_plate_number(best_match, best_plate_type)
                extra_info = self.get_vehicle_details(best_match, best_plate_type, max_conf, plate_color)
                
                if formatted_text:
                    is_valid = True
                else:
                    formatted_text = best_match  # Use unformatted if formatting fails

                if bbox:
                    top_left = tuple(map(int, bbox[0]))
                    bottom_right = tuple(map(int, bbox[2]))
                    
                    processed_img = self.cv_image.copy()
                    cv2.rectangle(processed_img, top_left, bottom_right, (0, 255, 0), 5)

                # Save to database
                plate_data = {
                    'plate_number': formatted_text,
                    'plate_category': extra_info['plate_category'],
                    'registration_area': extra_info['registration_area'],
                    'registered_owner': extra_info['registered_owner'],
                    'vehicle_type': extra_info['vehicle_type'],
                    'confidence': extra_info['confidence'],
                    'detection_time': extra_info['current_time'],
                    'image_path': self.current_image_path,
                    'source': 'image'
                }
                self.database.add_detection(plate_data)
                
                # Update history panel
                self.root.after(0, self.history_panel.refresh)

                self.root.after(0,
                    lambda: self.show_results_window(
                        formatted_text,
                        extra_info,
                        is_valid,
                        processed_img
                    )
                )
            else:
                self.root.after(0, lambda: self.display_failure())

        except Exception as e:
            print(e)
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

        finally:
            self.root.after(0, self.finish_processing)

    def show_results_window(self, plate_text, extra_info, is_valid, processed_image):
        self.root.withdraw()
        ResultsWindow(
            self.root,
            plate_text,
            extra_info,
            is_valid,
            processed_image,
            self.prepare_new_scan
        )

    def prepare_new_scan(self):
        self.clear_all()

    def finish_processing(self):
        self.is_processing = False
        self.detect_btn.config(state=tk.NORMAL)
        self.status_var.set("Processing complete")
        self.status_dot.config(fg="#10b981")

    def display_failure(self):
        messagebox.showinfo("No Plate Detected", "No license plate was detected in the image.")
        self.status_var.set("No plate detected")
        self.status_dot.config(fg="#ef4444")
        self.finish_processing()

    def clear_all(self):
        self.current_image_path = None
        self.cv_image = None
        self.original_canvas.configure(image="", text="")
        self.show_placeholder()
        self.status_var.set("System Ready")
        self.status_dot.config(fg="#10b981")


if __name__ == "__main__":
    root = tk.Tk()
    app = PlateReaderApp(root)
    root.mainloop()