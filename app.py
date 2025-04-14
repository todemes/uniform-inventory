from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from database import init_db
from stock_management import StockManagement
from staff_management import StaffManagement
import csv
from io import StringIO
import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback-secret-key')

# Initialize database with error handling
try:
    init_db()
    stock_mgmt = StockManagement()
    staff_mgmt = StaffManagement()
    logger.info("Database and management systems initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock')
def stock_list():
    uniforms = stock_mgmt.get_uniform_list()
    return render_template('stock_list.html', uniforms=uniforms)

@app.route('/stock/add', methods=['GET', 'POST'])
def add_uniform():
    if request.method == 'POST':
        type = request.form['type']
        size = request.form['size']
        color = request.form['color']
        initial_stock = int(request.form['initial_stock'])
        reorder_level = int(request.form['reorder_level'])
        
        stock_mgmt.add_uniform_type(type, size, color, initial_stock)
        flash('Uniform added successfully!', 'success')
        return redirect(url_for('stock_list'))
    
    return render_template('add_uniform.html')

@app.route('/stock/update/<int:uniform_id>', methods=['POST'])
def update_stock(uniform_id):
    quantity = int(request.form['quantity'])
    movement_type = request.form['movement_type']
    notes = request.form.get('notes', '')
    
    stock_mgmt.update_stock(uniform_id, quantity, movement_type, notes)
    flash('Stock updated successfully!', 'success')
    return redirect(url_for('stock_list'))

@app.route('/staff')
def staff_list():
    staff = staff_mgmt.get_staff_list()
    return render_template('staff_list.html', staff=staff)

@app.route('/staff/add', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        
        staff_mgmt.add_staff(name, department)
        flash('Staff member added successfully!', 'success')
        return redirect(url_for('staff_list'))
    
    return render_template('add_staff.html')

@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        
        staff_mgmt.edit_staff(staff_id, name, department)
        flash('Staff member updated successfully!', 'success')
        return redirect(url_for('staff_list'))
    
    staff = staff_mgmt.get_staff_by_id(staff_id)
    if staff is None:
        flash('Staff member not found!', 'error')
        return redirect(url_for('staff_list'))
    
    return render_template('edit_staff.html', staff=staff)

@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    success, message = staff_mgmt.delete_staff(staff_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('staff_list'))

@app.route('/staff/assign', methods=['GET', 'POST'])
def assign_uniform():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        uniform_id = request.form['uniform_id']
        notes = request.form.get('notes', '')
        
        staff_mgmt.assign_uniform(staff_id, uniform_id, notes)
        flash('Uniform assigned successfully!', 'success')
        return redirect(url_for('staff_list'))
    
    staff = staff_mgmt.get_staff_list()
    uniforms = stock_mgmt.get_uniform_list()
    return render_template('assign_uniform.html', staff=staff, uniforms=uniforms)

@app.route('/staff/return/<int:assignment_id>', methods=['POST'])
def return_uniform(assignment_id):
    discard = request.form.get('discard') == 'true'
    notes = request.form.get('notes', '')
    
    staff_mgmt.return_uniform(assignment_id, discard, notes)
    flash('Uniform returned successfully!', 'success')
    return redirect(url_for('staff_list'))

@app.route('/history')
def history():
    movements = staff_mgmt.get_uniform_movement_history()
    return render_template('history.html', movements=movements)

@app.route('/history/export')
def export_history():
    movements = staff_mgmt.get_uniform_movement_history()
    
    # Create a string buffer to write CSV data
    si = StringIO()
    cw = csv.writer(si)
    
    # Write headers
    cw.writerow(['Date', 'Staff Member', 'Department', 'Uniform Type', 'Size', 'Color', 'Action', 'Notes'])
    
    # Write data
    for movement in movements:
        cw.writerow([
            movement[0].split('.')[0],  # Date without milliseconds
            movement[1],                # Staff Member
            movement[2],                # Department
            movement[3],                # Uniform Type
            movement[4],                # Size
            movement[5],                # Color
            movement[6],                # Action
            movement[7] or ''           # Notes
        ])
    
    output = si.getvalue()
    si.close()
    
    # Generate filename with current date
    filename = f"uniform_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename={filename}'
    }

@app.route('/history/delete', methods=['POST'])
def delete_history_entries():
    entry_ids = request.form.getlist('entry_ids[]')
    if entry_ids:
        staff_mgmt.delete_movement_history_entries(entry_ids)
        flash('Selected entries have been deleted successfully.', 'success')
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True, port=8080) 