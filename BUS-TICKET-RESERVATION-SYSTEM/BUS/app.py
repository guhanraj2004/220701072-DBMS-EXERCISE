from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE_URL = 'postgres://ermmmhea:o3nwulL9fesvtV9VHHcPAiXIlC6irytd@snuffleupagus.db.elephantsql.com/ermmmhea'

# Function to fetch buses from the database
def get_buses(from_location=None, to_location=None, travel_date=None):
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        select_query = "SELECT * FROM buses WHERE 1=1"
        params = []

        if from_location:
            select_query += " AND route LIKE %s"
            params.append(f"%{from_location}%")

        if to_location:
            select_query += " AND route LIKE %s"
            params.append(f"%{to_location}%")

        if travel_date:
            select_query += " AND date = %s"
            params.append(travel_date)

        cursor.execute(select_query, params)
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print("Error:", e)
        return []

    finally:
        if conn is not None:
            conn.close()

# Database setup
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id SERIAL PRIMARY KEY,
            username TEXT,
            ip_address TEXT,
            action TEXT,
            timestamp TIMESTAMPTZ
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Logging actions
def log_action(username, action):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    ip_address = request.remote_addr
    timestamp = datetime.datetime.now()
    cur.execute('''
        INSERT INTO logs (username, ip_address, action, timestamp)
        VALUES (%s, %s, %s, %s)
    ''', (username, ip_address, action, timestamp))
    conn.commit()
    cur.close()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/log_action', methods=['POST'])
def log_user_action():
    username = request.form['username']
    action = request.form['action']
    log_action(username, action)
    return redirect(url_for('index'))

@app.route('/view_logs')
def view_logs():
    if 'username' in session:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Fetch logs with optional date filters
        log_query = 'SELECT * FROM logs WHERE 1=1'
        log_params = []
        if start_date:
            log_query += ' AND timestamp >= %s'
            log_params.append(start_date)
        if end_date:
            log_query += ' AND timestamp <= %s'
            log_params.append(end_date)
        
        cur.execute(log_query, log_params)
        logs = cur.fetchall()
        
        # Fetch statistics with optional date filters
        stats_query = '''
            SELECT action, COUNT(*) as count
            FROM logs
            WHERE action LIKE '%% to %%'
        '''
        stats_params = []
        if start_date:
            stats_query += ' AND timestamp >= %s'
            stats_params.append(start_date)
        if end_date:
            stats_query += ' AND timestamp <= %s'
            stats_params.append(end_date)
        stats_query += ' GROUP BY action ORDER BY count DESC'
        
        cur.execute(stats_query, stats_params)
        search_stats = cur.fetchall()
        
        least_stats_query = '''
            SELECT action, COUNT(*) as count
            FROM logs
            WHERE action LIKE '%% to %%'
        '''
        least_stats_params = []
        if start_date:
            least_stats_query += ' AND timestamp >= %s'
            least_stats_params.append(start_date)
        if end_date:
            least_stats_query += ' AND timestamp <= %s'
            least_stats_params.append(end_date)
        least_stats_query += ' GROUP BY action ORDER BY count ASC'
        
        cur.execute(least_stats_query, least_stats_params)
        least_search_stats = cur.fetchall()
        
        avg_users_query = '''
            SELECT 
                substring(action from '^(.*) to') as from_location, 
                substring(action from 'to (.*)$') as to_location,
                COUNT(*) / 2.0 as avg_users
            FROM logs
            WHERE action LIKE '%% to %%'
        '''
        avg_users_params = []
        if start_date:
            avg_users_query += ' AND timestamp >= %s'
            avg_users_params.append(start_date)
        if end_date:
            avg_users_query += ' AND timestamp <= %s'
            avg_users_params.append(end_date)
        avg_users_query += ' GROUP BY from_location, to_location'
        
        cur.execute(avg_users_query, avg_users_params)
        avg_users_stats = cur.fetchall()

        cur.close()
        conn.close()
        
        return render_template('view_logs.html', logs=logs, search_stats=search_stats, least_search_stats=least_search_stats, avg_users_stats=avg_users_stats)
    
    return redirect(url_for('login'))



@app.route('/book_ticket_page')
def book_ticket_page():
    if 'username' in session:
        return render_template('book_ticket_page.html')
    return redirect(url_for('login'))

@app.route('/view_bookings')
def view_bookings():
    if 'username' in session:
        return render_template('view_bookings.html')
    return redirect(url_for('login'))

@app.route('/search', methods=['POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure the user is logged in

    username = session['username']  # Get the username from the session
    from_location = request.form.get('from')
    to_location = request.form.get('to')
    travel_date = request.form.get('date')
    
    action = f"{from_location} to {to_location}"
    log_action(username, action)

    buses = get_buses(from_location, to_location, travel_date)

    return render_template('search_result.html', buses=buses, from_location=from_location, to_location=to_location, username=username)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        log_action(username, 'login')
        return redirect(url_for('index'))
    # GET request (show login form)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route to view seats
@app.route('/view_seats')
def view_seats():
    bus_id = request.args.get('bus_id')
    bus_details = {'bus_name': 'Demo Bus', 'from_location': 'City A', 'to_location': 'City B'}
    return render_template('view_seats.html', bus_details=bus_details)

# Route to confirm booking
@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    bus_details = {
        'bus_name': 'Demo Bus', 
        'from_location': 'City A', 
        'to_location': 'City B',
        'date': '2024-05-20'
    }
    
    # Extract passenger details from the form
    passengers = {}
    for key in request.form.keys():
        if key.startswith('name_'):
            seat_id = key.split('_')[1]
            passengers[seat_id] = {
                'name': request.form.get(f'name_{seat_id}'),
                'email': request.form.get(f'email_{seat_id}'),
                'age': request.form.get(f'age_{seat_id}'),
                'gender': request.form.get(f'gender_{seat_id}')
            }
    
    # Calculate total price
    total_price = len(passengers) * 1800  # Assuming each ticket costs 1800

    return render_template('confirm_booking.html', bus_details=bus_details, passengers=passengers, total_price=total_price)

# Route to add passenger details
@app.route('/add-passenger', methods=['GET', 'POST'])
def add_passenger():
    if request.method == 'POST':
        # Assuming you process and validate the form data here
        # Redirect to confirm booking after adding passenger details
        return redirect(url_for('confirm_booking'))
    else:
        seats = request.args.get('seats')
        if seats:
            seat_ids = seats.split(',')
            return render_template('add_passenger.html', seat_ids=seat_ids)
        else:
            return "No seats selected", 400
        
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
