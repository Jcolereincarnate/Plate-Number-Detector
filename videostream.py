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
import signal
class VideoStreamWindow:
    def __init__(self, parent, app):
        self.window = tk.Toplevel(parent)
        self.window.title("Live Video Stream - ANPR")
        self.window.geometry("1200x750")
        self.window.configure(bg="#0f172a")
        self.app = app
        self.is_running = False
        self.cap = None
        self.detection_cooldown = {}
        self.is_detecting = False  # Add flag to prevent overlapping detections
        self.detection_count = 0
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#1e293b", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="Live Video Stream",
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
            text="Start Stream",
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
            text="Stop Stream",
            command=self.stop_stream,
            font=("Segoe UI", 11, "bold"),
            bg="#000000",
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
            text="Close",
            command=self.close_window,
            font=("Segoe UI", 11, "bold"),
            bg="#000000",
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
        if not self.app.reader:
            messagebox.showwarning("OCR Not Ready", "OCR Engine is still loading. Please wait.")
            return
        
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
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(text="● Stopped", fg="#ef4444")
    
    def process_stream(self):
        frame_count = 0
        last_detection_frame = -100
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            display_frame = frame.copy()
            
            # Add status text to frame
            status_text = f"Frame: {frame_count} | Detections: {self.detection_count}"
            if self.is_detecting:
                status_text += " | DETECTING..."
            cv2.putText(display_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Only trigger detection if:
            # 1. Every 30 frames (slower rate)
            # 2. OCR reader is loaded
            # 3. Not currently detecting
            # 4. At least 30 frames since last detection
            if (frame_count % 30 == 0 and 
                self.app.reader and 
                not self.is_detecting and 
                frame_count - last_detection_frame >= 30):
                self.is_detecting = True
                last_detection_frame = frame_count
                detection_frame = frame.copy()
                
                # Start detection in background
                threading.Thread(
                    target=self.detect_in_frame,
                    args=(detection_frame, frame_count),
                    daemon=True
                ).start()
            
            # Display frame - with error handling
            try:
                if not self.window.winfo_exists():
                    print("Window closed, stopping stream")
                    break
                    
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(rgb_frame)
                img.thumbnail((1160, 650))
                imgtk = PIL.ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            except tk.TclError:
                print("Display error, window likely closed")
                break
            except Exception as e:
                print(f"Display error: {e}")
                break
            
            frame_count += 1
            time.sleep(0.033)  # ~30 FPS
        
        # Clean up
        self.is_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
    def detect_in_frame(self, frame, frame_number):
        """Detect plate in a single frame"""
        start_time = time.time()
        try:
            # Step 1: Preprocessing
            print(f"[Frame {frame_number}] Preprocessing image...")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Apply additional preprocessing for better detection
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(bfilter)
            
            preprocess_time = time.time()
            print(f"[Frame {frame_number}] Preprocessing done ({preprocess_time - start_time:.2f}s)")
            
            # Step 2: Run OCR with timeout warning
            print(f"[Frame {frame_number}] Running OCR (this may take 2-5 seconds)...")
            ocr_start = time.time()
            
            results = self.app.reader.readtext(
                enhanced,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                paragraph=False,
                detail=1,
                min_size=10,
                text_threshold=0.5,  # Slightly higher for better accuracy
                low_text=0.4
            )
            
            ocr_time = time.time() - ocr_start
            print(f"[Frame {frame_number}]OCR completed in {ocr_time:.2f}s")
            print(f"[Frame {frame_number}]Found {len(results)} text regions")
            
            # If no results after all that time
            if len(results) == 0:
                print(f"[Frame {frame_number}] NO TEXT DETECTED")
                print(f"[Frame {frame_number}] Suggestions:")
                print(f"   • Is there a license plate visible?")
                print(f"   • Is it in focus and well-lit?")
                print(f"   • Try holding a printed plate closer to camera")
                self.is_detecting = False
                return
            
            # Step 3: Process results
            best_match = None
            max_conf = 0
            best_plate_type = None
            bbox = None
            
            slogan_keywords = [
                "FEDERAL", "REPUBLIC", "CENTRE", "CENTER",
                "EXCELLENCE", "STATE", "NIGERIA", "GOVERNMENT"
            ]
            
            for idx, (box, text, prob) in enumerate(results):
                clean_text = text.replace(" ", "").replace("-", "").upper()
                print(f"[Frame {frame_number}]   #{idx+1}: '{clean_text}' (conf: {prob:.3f})")
                
                # Skip slogans and short text
                if any(keyword in clean_text for keyword in slogan_keywords):
                    print(f"[Frame {frame_number}]      Skipped (slogan)")
                    continue
                if len(clean_text) < 5:
                    print(f"[Frame {frame_number}]      Skipped (too short)")
                    continue
                
                # Check against all patterns
                matched = False
                for plate_type, pattern in PLATE_PATTERNS.items():
                    if re.match(pattern, clean_text):
                        print(f"[Frame {frame_number}]      Matched {plate_type} pattern!")
                        if prob > max_conf:
                            max_conf = prob
                            best_match = clean_text
                            bbox = box
                            best_plate_type = plate_type
                        matched = True
                        break
                
                if not matched:
                    print(f"[Frame {frame_number}]      No pattern match")
            
            # Fuzzy matching if needed
            if not best_match:
                print(f"[Frame {frame_number}]  Trying fuzzy matching...")
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
                        print(f"[Frame {frame_number}]    Fuzzy match: {clean_text}")
            
            # Step 4: Process detection if found
            if best_match and max_conf > 0.35:
                print(f"[Frame {frame_number}] CANDIDATE FOUND: '{best_match}' (conf: {max_conf:.3f})")
                
                # Check cooldown
                current_time = time.time()
                if best_match in self.detection_cooldown:
                    time_since = current_time - self.detection_cooldown[best_match]
                    if time_since < 3:
                        print(f"[Frame {frame_number}] Cooldown active ({3 - time_since:.1f}s remaining)")
                        self.is_detecting = False
                        return
                
                self.detection_cooldown[best_match] = current_time
                
                # Process detection
                if not best_plate_type:
                    best_plate_type = self.app.identify_plate_type(best_match)
                    if not best_plate_type:
                        best_plate_type = 'standard'
                
                print(f"[Frame {frame_number}]  Detecting color...")
                plate_color = self.app.detect_plate_color(bbox, frame)
                
                print(f"[Frame {frame_number}]  Formatting...")
                formatted_text = self.app.format_plate_number(best_match, best_plate_type)
                
                if not formatted_text:
                    formatted_text = best_match
                
                print(f"[Frame {frame_number}] Getting vehicle details...")
                extra_info = self.app.get_vehicle_details(formatted_text, best_plate_type, max_conf, plate_color)
                
                # Save to database
                print(f"[Frame {frame_number}] Saving to database...")
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
                self.app.database.add_detection(plate_data)
                
                # Update counter
                self.detection_count += 1
                
                # Update history panel
                if hasattr(self.app, 'history_panel'):
                    try:
                        self.window.after(0, self.app.history_panel.refresh)
                    except:
                        pass
                
                # Show success
                total_time = time.time() - start_time
                print(f"PLATE DETECTED! (Total time: {total_time:.2f}s)")
                print(f"   Plate: {formatted_text}")
                print(f"   Type: {extra_info['vehicle_type']}")
                print(f"   Owner: {extra_info['registered_owner']}")
                print(f"   Confidence: {extra_info['confidence']}%")
                
            else:
                if best_match:
                    print(f"[Frame {frame_number}]  Confidence too low: {max_conf:.3f} < 0.35")
                else:
                    print(f"[Frame {frame_number}]  No valid plate pattern found")
            
            # Mark detection as complete
            total_time = time.time() - start_time
            print(f"[Frame {frame_number}]  Total detection time: {total_time:.2f}s")
            
        except Exception as e:
            print(f"[Frame {frame_number}]  ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Always release the detection lock
            self.is_detecting = False
            print(f"[Frame {frame_number}]  Detection thread finished\n")
    
    def close_window(self):
        """Close the video window"""
        print("Closing video window...")
        self.stop_stream()
        self.window.destroy()
        print("Video window closed")