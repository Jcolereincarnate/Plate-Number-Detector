import time
import tkinter as tk
import cv2
from tkinter import messagebox
from database import Database
import threading
import PIL.Image
import PIL.ImageTk
import re
from config import PLATE_PATTERNS
class VideoStreamWindow:
    def __init__(self, parent, app):
        self.window = tk.Toplevel(parent)
        self.window.title("Live Video Stream - ANPR")
        self.window.geometry("1200x750")
        self.window.configure(bg="#0f172a")
        self.app = app
        self.is_running = False
        self.cap = None
        self.detection_cooldown = {}  # Track detection cooldowns
        self.setup_ui()
        self.database = Database()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#1e293b", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📹 Live Video Stream",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        self.status_indicator = tk.Label(
            header,
            text="● Stopped",
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#ef4444"
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=20)
        
        # Video display
        video_container = tk.Frame(self.window, bg="#0f172a")
        video_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.video_label = tk.Label(video_container, bg="#0f172a")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = tk.Frame(self.window, bg="#1e293b", height=80)
        control_frame.pack(fill=tk.X)
        control_frame.pack_propagate(False)
        
        btn_container = tk.Frame(control_frame, bg="#1e293b")
        btn_container.pack(expand=True)
        
        self.start_btn = tk.Button(
            btn_container,
            text="▶ Start Stream",
            command=self.start_stream,
            font=("Segoe UI", 11, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(
            btn_container,
            text="⏸ Stop Stream",
            command=self.stop_stream,
            font=("Segoe UI", 11, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(
            btn_container,
            text="✕ Close",
            command=self.close_window,
            font=("Segoe UI", 11, "bold"),
            bg="#475569",
            fg="#f1f5f9",
            activebackground="#334155",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2"
        )
        close_btn.pack(side=tk.LEFT, padx=10)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def start_stream(self):
        """Start video stream"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_indicator.config(text="● Live", fg="#10b981")
        
        threading.Thread(target=self.process_stream, daemon=True).start()
    
    def stop_stream(self):
        """Stop video stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(text="● Stopped", fg="#ef4444")
    
    def process_stream(self):
        """Process video stream and detect plates"""
        frame_count = 0
        detection_frame = None
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            display_frame = frame.copy()
            
            # Process every 15 frames for detection (more frequent)
            if frame_count % 15 == 0 and self.app.reader:
                detection_frame = frame.copy()
                threading.Thread(
                    target=self.detect_in_frame,
                    args=(detection_frame, display_frame),
                    daemon=True
                ).start()
            
            # Display frame
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(rgb_frame)
            img.thumbnail((1160, 650))
            imgtk = PIL.ImageTk.PhotoImage(image=img)
            
            if self.window.winfo_exists():
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            else:
                break
            
            frame_count += 1
            time.sleep(0.033)  # ~30 FPS
    
    def detect_in_frame(self, frame, display_frame=None):
        """Detect plate in a single frame"""
        try:
            # Show processing indicator
            if display_frame is not None and self.window.winfo_exists():
                cv2.putText(display_frame, "Scanning...", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
            
            results = self.app.reader.readtext(
                bfilter,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                paragraph=False
            )
            
            if not results:
                return
            
            best_match = None
            max_conf = 0
            best_plate_type = None
            bbox = None
            
            slogan_keywords = [
                "FEDERAL", "REPUBLIC", "CENTRE", "CENTER",
                "EXCELLENCE", "STATE", "NIGERIA", "GOVERNMENT"
            ]
            
            for (box, text, prob) in results:
                clean_text = text.replace(" ", "").replace("-", "").upper()
                
                # Skip slogans and short text
                if any(keyword in clean_text for keyword in slogan_keywords):
                    continue
                if len(clean_text) < 5:
                    continue
                
                # Check against all patterns
                for plate_type, pattern in PLATE_PATTERNS.items():
                    if re.match(pattern, clean_text):
                        if prob > max_conf:
                            max_conf = prob
                            best_match = clean_text
                            bbox = box
                            best_plate_type = plate_type
                        break
            
            # If no exact match, try fuzzy matching
            if not best_match:
                for (box, text, prob) in results:
                    clean_text = text.replace(" ", "").replace("-", "").upper()
                    
                    if any(keyword in clean_text for keyword in slogan_keywords):
                        continue
                    if len(clean_text) < 6:
                        continue
                    
                    has_letters = any(c.isalpha() for c in clean_text)
                    has_numbers = any(c.isdigit() for c in clean_text)
                    
                    if has_letters and has_numbers and prob > max_conf:
                        max_conf = prob
                        best_match = clean_text
                        bbox = box
                        best_plate_type = 'standard'
            
            if best_match and max_conf > 0.4:  # Lower threshold for video
                # Check cooldown (don't detect same plate within 3 seconds)
                current_time = time.time()
                if best_match in self.detection_cooldown:
                    if current_time - self.detection_cooldown[best_match] < 3:
                        return
                
                self.detection_cooldown[best_match] = current_time
                
                # Process detection
                if not best_plate_type:
                    best_plate_type = self.app.identify_plate_type(best_match)
                    if not best_plate_type:
                        best_plate_type = 'standard'
                
                plate_color = self.app.detect_plate_color(bbox, frame)
                formatted_text = self.app.format_plate_number(best_match, best_plate_type)
                
                if not formatted_text:
                    formatted_text = best_match
                
                extra_info = self.app.get_vehicle_details(formatted_text, best_plate_type, max_conf, plate_color)
                
                # Save to database
                plate_data = {
                    'plate_number': formatted_text,
                    'plate_category': extra_info['plate_category'],
                    'registration_area': extra_info['registration_area'],
                    'registered_owner': extra_info['registered_owner'],
                    'vehicle_type': extra_info['vehicle_type'],
                    'confidence': extra_info['confidence'],
                    'detection_time': extra_info['current_time'],
                    'source': 'video'
                }
                self.database.add_detection(plate_data)
                
                # Update history panel
                if hasattr(self.app, 'history_panel'):
                    self.window.after(0, self.app.history_panel.refresh)
                
                # Show detection notification
                print(f"✓ Detected: {formatted_text} - {extra_info['vehicle_type']} ({extra_info['confidence']}%)")
                
                # Draw bounding box on display frame
                if bbox is not None and display_frame is not None:
                    top_left = tuple(map(int, bbox[0]))
                    bottom_right = tuple(map(int, bbox[2]))
                    cv2.rectangle(display_frame, top_left, bottom_right, (0, 255, 0), 3)
                    cv2.putText(display_frame, formatted_text, (top_left[0], top_left[1] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        except Exception as e:
            print(f"Detection error: {e}")
    
    def close_window(self):
        """Close the video window"""
        self.stop_stream()
        self.window.destroy()

