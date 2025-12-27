import sqlite3
import hashlib
class Database:
    def __init__(self, db_name="anpr_detections.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                plate_category TEXT,
                registration_area TEXT,
                registered_owner TEXT,
                vehicle_type TEXT,
                confidence REAL,
                detection_time TIMESTAMP,
                image_path TEXT,
                source TEXT
            )
        ''')
        
        # Plate owners table (for consistency)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plate_owners (
                plate_number TEXT PRIMARY KEY,
                owner_name TEXT NOT NULL,
                registration_area TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_detection(self, plate_data):
        """Add a new detection to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detections 
            (plate_number, plate_category, registration_area, registered_owner, 
             vehicle_type, confidence, detection_time, image_path, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plate_data['plate_number'],
            plate_data['plate_category'],
            plate_data['registration_area'],
            plate_data['registered_owner'],
            plate_data['vehicle_type'],
            plate_data['confidence'],
            plate_data['detection_time'],
            plate_data.get('image_path', ''),
            plate_data.get('source', 'image')
        ))
        
        conn.commit()
        conn.close()
    
    def get_or_create_owner(self, plate_number, registration_area):
        """Get existing owner or create new one for a plate"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT owner_name FROM plate_owners WHERE plate_number = ?', (plate_number,))
        result = cursor.fetchone()
        
        if result:
            owner_name = result[0]
        else:
            # Generate consistent name based on plate number
            owner_name = self.generate_consistent_name(plate_number)
            cursor.execute('''
                INSERT INTO plate_owners (plate_number, owner_name, registration_area)
                VALUES (?, ?, ?)
            ''', (plate_number, owner_name, registration_area))
            conn.commit()
        
        conn.close()
        return owner_name
    
    def generate_consistent_name(self, plate_number):
        """Generate a consistent name based on plate number hash"""
        first_names = ["Chinedu","Fatima","Ayodele","Aminu","Ngozi","Tunde","Hauwa","Emeka","Sade","Mohammed",
                      "Ifunanya","Olumide","Zainab","Obinna","Abiola","Musa","Ifeoma","Segun","Aisha",
                      "Chisom","Damilola","Uche","Bola","Abdulahi","Adaobi","Kayode","Maryam","Ibrahim","Funmi","Efe"]
        surnames = ["Adekunle","Okoro","Malami","Dike","Ogunyemi","Abdullahi","Nwosu","Bello",
                   "Adebayo","Okeke","Aliyu","Eze","Adewale","Usman","Chukwu","Dada","Gambo",
                   "Ibekwe","Lawal","Nwafor","Oyelade","Sanusi","Ugwuanyi","Yusuf","Akinola","Audu","Idowu","Mustapha","Peters","Williams"]
        
        # Use hash to consistently select names
        hash_value = int(hashlib.md5(plate_number.encode()).hexdigest(), 16)
        surname = surnames[hash_value % len(surnames)]
        first_name = first_names[(hash_value // len(surnames)) % len(first_names)]
        
        return f"{surname} {first_name}"
    
    def get_recent_detections(self, limit=10):
        """Get recent detections"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT plate_number, vehicle_type, detection_time, confidence, source
            FROM detections
            ORDER BY detection_time DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_detection_count(self):
        """Get total number of detections"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM detections')
        count = cursor.fetchone()[0]
        conn.close()
        return count
