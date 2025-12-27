import tkinter as tk
import cv2
import PIL.Image
import PIL.ImageTk
class ResultsWindow:
    def __init__(self, parent, plate_text, extra_info, is_valid, processed_image, callback):
        self.window = tk.Toplevel(parent)
        self.window.title('Detection Results - License Plate Recognition')
        self.window.geometry('1200x800')
        self.window.configure(bg="#0f172a")
        self.callback = callback
        self.parent = parent
        
        #Main Container
        main_container = tk.Frame(self.window, bg="#0f172a")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Navigation bar
        nav_bar = tk.Frame(main_container, bg="#1e293b", height=70)
        nav_bar.pack(fill=tk.X)
        nav_bar.pack_propagate(False)
        
        # Logo section
        title_frame = tk.Frame(nav_bar, bg="#1e293b")
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        tk.Label(
            title_frame,
            text="ANPR",
            font=("Segoe UI", 16, "bold"),
            bg="#1e293b",
            fg="#10b981"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text=" SYSTEM",
            font=("Segoe UI", 16, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT)
        
        #  Status indicator
        status_frame = tk.Frame(nav_bar, bg="#1e293b")
        status_frame.pack(side=tk.RIGHT, padx=30)
        status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 20),
            bg="#1e293b",
            fg="#10b981"
        )
        status_dot.pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            status_frame,
            text="Detection Complete",
            font=("Segoe UI", 11),
            bg="#1e293b",
            fg="#94a3b8"
        ).pack(side=tk.LEFT)
        
        # Body
        content_area = tk.Frame(main_container, bg="#0f172a")
        content_area.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Left side 
        left_section = tk.Frame(content_area, bg="#0f172a")
        left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Image card
        image_card = tk.Frame(left_section, bg="#1e293b", highlightbackground="#334155", highlightthickness=1)
        image_card.pack(fill=tk.BOTH, expand=True)
        
        # Image header
        image_header = tk.Frame(image_card, bg="#1e293b", height=50)
        image_header.pack(fill=tk.X)
        image_header.pack_propagate(False)
        
        tk.Label(
            image_header,
            text="Processed Image",
            font=("Segoe UI", 12, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Image display area
        image_container = tk.Frame(image_card, bg="#0f172a")
        image_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.image_canvas = tk.Label(
            image_container,
            bg="#0f172a"
        )
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display the processed image
        if processed_image is not None:
            rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            pil_image.thumbnail((600, 450))
            tk_image = PIL.ImageTk.PhotoImage(pil_image)
            self.image_canvas.configure(image=tk_image)
            self.image_canvas.image = tk_image
        
        # Right side - Detection results
        right_section = tk.Frame(content_area, bg="#0f172a", width=450)
        right_section.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_section.pack_propagate(False)
        
        # Results header
        results_header = tk.Frame(right_section, bg="#0f172a")
        results_header.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(
            results_header,
            text="Detection Results",
            font=("Segoe UI", 20, "bold"),
            bg="#0f172a",
            fg="#f1f5f9"
        ).pack(anchor="w")
        
        tk.Label(
            results_header,
            text="Vehicle identification summary",
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#64748b"
        ).pack(anchor="w", pady=(5, 0))
        
        # Plate number card - featured
        plate_card = tk.Frame(right_section, bg="#10b981", highlightbackground="#059669", highlightthickness=2)
        plate_card.pack(fill=tk.X, pady=(0, 20))
        
        plate_inner = tk.Frame(plate_card, bg="#10b981")
        plate_inner.pack(fill=tk.X, padx=25, pady=20)
        
        tk.Label(
            plate_inner,
            text="LICENSE PLATE",
            font=("Segoe UI", 9, "bold"),
            bg="#10b981",
            fg="#dcfce7"
        ).pack(anchor="w")
        
        tk.Label(
            plate_inner,
            text=plate_text,
            font=("Consolas", 36, "bold"),
            bg="#10b981",
            fg="#ffffff"
        ).pack(anchor="w", pady=(8, 5))
        
        # Validation badge
        validation_frame = tk.Frame(plate_inner, bg="#10b981")
        validation_frame.pack(anchor="w")
        
        validation_text = "✓ Valid Format" if is_valid else "⚠ Unrecognized"
        validation_bg = "#dcfce7" if is_valid else "#fef3c7"
        validation_fg = "#166534" if is_valid else "#92400e"
        
        validation_badge = tk.Label(
            validation_frame,
            text=validation_text,
            font=("Segoe UI", 9, "bold"),
            bg=validation_bg,
            fg=validation_fg,
            padx=12,
            pady=4
        )
        validation_badge.pack(side=tk.LEFT)
        
        # Vehicle information cards
        area = extra_info.get("registration_area", "Not Available")
        name = extra_info.get("registered_owner", "Not Available")
        current_time = extra_info.get("current_time", "Unknown Time")
        vehicle_type = extra_info.get("vehicle_type", "Unknown Type")
        plate_category = extra_info.get("plate_category", "Unknown")
        confidence = extra_info.get("confidence", "N/A")
        
        # Info grid
        info_items = [
            ("Plate Category", plate_category),
            ("Registration Area", area),
            ("Registered Owner", name),
            ("Vehicle Type", vehicle_type),
            ("Detection Time", current_time),
            ("Confidence Score", f"{confidence}%")
        ]
        for label, value in info_items:
            info_card = tk.Frame(right_section, bg="#1e293b", highlightbackground="#334155", highlightthickness=1)
            info_card.pack(fill=tk.X, pady=(0, 3))
            
            info_inner = tk.Frame(info_card, bg="#1e293b")
            info_inner.pack(fill=tk.X, padx=10, pady=5)
            
            # Icon and label
            header_frame = tk.Frame(info_inner, bg="#1e293b")
            header_frame.pack(fill=tk.X)
            
            tk.Label(
                header_frame,
                text=label,
                font=("Segoe UI", 8),
                bg="#1e293b",
                fg="#94a3b8"
            ).pack(side=tk.LEFT)
            
            # Value
            tk.Label(
                info_inner,
                text=value,
                font=("Segoe UI", 10, "bold"),
                bg="#1e293b",
                fg="#e2e8f0",
                wraplength=350,
                justify=tk.LEFT
            ).pack(anchor="w", pady=(6, 0), padx=(0, 0))
        
        # Bottom action bar
        action_bar = tk.Frame(main_container, bg="#1e293b", height=90)
        action_bar.pack(side=tk.BOTTOM, fill=tk.X)
        action_bar.pack_propagate(False)
        
        action_container = tk.Frame(action_bar, bg="#1e293b")
        action_container.pack(expand=True)
        
        # Modern buttons with better contrast
        new_scan_btn = tk.Button(
            action_container,
            text="🔄  New Scan",
            command=self.new_scan,
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=35,
            pady=15,
            cursor="hand2",
            relief=tk.FLAT
        )
        new_scan_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(
            action_container,
            text="✕  Close",
            command=self.close_window,
            font=("Segoe UI", 11, "bold"),
            bg="#475569",
            fg="#f1f5f9",
            activebackground="#334155",
            activeforeground="#ffffff",
            bd=0,
            padx=35,
            pady=15,
            cursor="hand2",
            relief=tk.FLAT
        )
        close_btn.pack(side=tk.LEFT, padx=10)
        
        # Hover effects
        def on_enter_new(e):
            new_scan_btn['bg'] = '#1d4ed8'
        
        def on_leave_new(e):
            new_scan_btn['bg'] = '#2563eb'
        
        def on_enter_close(e):
            close_btn['bg'] = '#334155'
        
        def on_leave_close(e):
            close_btn['bg'] = '#475569'
        
        new_scan_btn.bind("<Enter>", on_enter_new)
        new_scan_btn.bind("<Leave>", on_leave_new)
        close_btn.bind("<Enter>", on_enter_close)
        close_btn.bind("<Leave>", on_leave_close)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def new_scan(self):
        self.window.destroy()
        self.parent.deiconify()
        if self.callback:
            self.callback()
    
    def close_window(self):
        self.window.destroy()
        self.parent.deiconify()
