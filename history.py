import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkinter import messagebox
import sqlite3
class HistoryPanel:
    def __init__(self, parent, database):
        self.frame = tk.Frame(parent, bg="#1e293b", width=300)
        self.database = database
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.frame, bg="#1e293b", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="Detection History",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Stats frame
        stats_frame = tk.Frame(self.frame, bg="#0f172a", height=60)
        stats_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.total_label = tk.Label(
            stats_frame,
            text="Total: 0",
            font=("Segoe UI", 10, "bold"),
            bg="#0f172a",
            fg="#10b981"
        )
        self.total_label.pack(pady=10)
        
        # Scrollable list
        canvas_frame = tk.Frame(self.frame, bg="#1e293b")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.canvas = tk.Canvas(canvas_frame, bg="#0f172a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#0f172a")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear button
        clear_btn = tk.Button(
            self.frame,
            text="Clear History",
            command=self.clear_history,
            bg="#2563eb", fg="#000000", 
            activebackground="#1d4ed8", 
            activeforeground="#000000",
            bd=0,
            pady=10,
            cursor="hand2"
        )
        clear_btn.pack(fill=tk.X, padx=15, pady=(0, 15))
    
    def refresh(self):
        """Refresh the history list"""
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get recent detections
        detections = self.database.get_recent_detections(50)
        total = self.database.get_detection_count()
        
        self.total_label.config(text=f"Total Detections: {total}")
        
        for plate, vehicle_type, det_time, confidence, source in detections:
            self.add_history_item(plate, vehicle_type, det_time, confidence, source)
    
    def add_history_item(self, plate, vehicle_type, det_time, confidence, source):
        """Add a history item to the list"""
        item_frame = tk.Frame(
            self.scrollable_frame,
            bg="#1e293b",
            highlightbackground="#334155",
            highlightthickness=1
        )
        item_frame.pack(fill=tk.X, pady=3)
        
        inner = tk.Frame(item_frame, bg="#1e293b")
        inner.pack(fill=tk.X, padx=10, pady=8)
        
        # Source icon
        source_icon = "📹" if source == "video" else "📷"
        
        # Plate number
        plate_label = tk.Label(
            inner,
            text=f"{source_icon} {plate}",
            font=("Consolas", 11, "bold"),
            bg="#1e293b",
            fg="#10b981"
        )
        plate_label.pack(anchor="w")
        
        # Vehicle type
        tk.Label(
            inner,
            text=vehicle_type,
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))
        
        # Time and confidence
        try:
            time_obj = datetime.strptime(det_time, "%Y-%m-%d %H:%M:%S")
            time_str = time_obj.strftime("%I:%M %p")
        except:
            time_str = det_time
        
        tk.Label(
            inner,
            text=f"{time_str} • {confidence}%",
            font=("Segoe UI", 7),
            bg="#1e293b",
            fg="#64748b"
        ).pack(anchor="w", pady=(2, 0))
    
    def clear_history(self):
        """Clear all history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all detection history?"):
            conn = sqlite3.connect(self.database.db_name)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM detections')
            conn.commit()
            conn.close()
            self.refresh()

