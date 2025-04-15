import sqlite3
from datetime import datetime

class StockManagement:
    def __init__(self):
        self.db_path = 'uniform_inventory.db'

    def add_uniform_type(self, type_name, size, color, initial_stock=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uniforms (type, size, color, current_stock)
            VALUES (?, ?, ?, ?)
        ''', (type_name, size, color, initial_stock))
        conn.commit()
        conn.close()

    def update_stock(self, uniform_id, new_stock):
        """Update the stock level for a uniform."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update the stock level
            cursor.execute("""
                UPDATE uniforms 
                SET current_stock = ?
                WHERE id = ?
            """, (new_stock, uniform_id))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
            
        finally:
            if conn:
                conn.close()

    def get_current_stock(self, uniform_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if uniform_id:
            cursor.execute('''
                SELECT id, type, size, color, current_stock
                FROM uniforms
                WHERE id = ?
            ''', (uniform_id,))
        else:
            cursor.execute('''
                SELECT id, type, size, color, current_stock
                FROM uniforms
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert results to list of dictionaries
        stock_list = []
        for row in results:
            stock_list.append({
                'id': row[0],
                'type': row[1],
                'size': row[2],
                'color': row[3],
                'current_stock': row[4]
            })
        return stock_list

    def get_stock_movements(self, uniform_id=None, start_date=None, end_date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT sm.id, u.type, u.size, u.color, sm.movement_type, 
                   sm.quantity, sm.date, sm.notes
            FROM stock_movements sm
            JOIN uniforms u ON sm.uniform_id = u.id
        '''
        params = []
        
        if uniform_id:
            query += ' WHERE sm.uniform_id = ?'
            params.append(uniform_id)
        
        if start_date:
            query += ' AND sm.date >= ?' if uniform_id else ' WHERE sm.date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND sm.date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY sm.date DESC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Convert results to list of dictionaries
        movements = []
        for row in results:
            movements.append({
                'id': row[0],
                'type': row[1],
                'size': row[2],
                'color': row[3],
                'movement_type': row[4],
                'quantity': row[5],
                'date': row[6],
                'notes': row[7]
            })
        return movements

    def get_uniform_list(self):
        return self.get_current_stock()

    def delete_uniform(self, uniform_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First check if the uniform is assigned to any staff
            cursor.execute('''
                SELECT COUNT(*) FROM staff_assignments 
                WHERE uniform_id = ? AND returned_date IS NULL
            ''', (uniform_id,))
            assigned_count = cursor.fetchone()[0]
            
            if assigned_count > 0:
                return False, "Cannot delete uniform that is currently assigned to staff"
            
            # Delete the uniform
            cursor.execute('DELETE FROM uniforms WHERE id = ?', (uniform_id,))
            conn.commit()
            return True, "Uniform deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting uniform: {str(e)}"
        finally:
            conn.close()

    def get_uniform_by_details(self, type, size, color):
        """Get a uniform by its type, size, and color."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, type, size, color, current_stock
            FROM uniforms
            WHERE type = ? AND size = ? AND color = ?
        ''', (type, size, color))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'type': row[1],
                'size': row[2],
                'color': row[3],
                'stock': row[4]
            }
        return None 