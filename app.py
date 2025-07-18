from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from datetime import datetime
import os
import json
import shutil

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workouts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BACKUP_FOLDER = 'backups'
MAX_BACKUPS = 3

class WorkoutEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    pull_ups = db.Column(db.Integer, default=0)
    push_ups = db.Column(db.Integer, default=0)
    sit_ups = db.Column(db.Integer, default=0)
    squats = db.Column(db.Integer, default=0)
    km_ran = db.Column(db.Float, default=0)
    km_walked = db.Column(db.Float, default=0)
    weight = db.Column(db.Float, default=0)

    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'pull_ups': self.pull_ups,
            'push_ups': self.push_ups,
            'sit_ups': self.sit_ups,
            'squats': self.squats,
            'km_ran': self.km_ran,
            'km_walked': self.km_walked,
            'weight': self.weight,
        }
        data['calories'] = calculate_calories(self)
        return data


class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    walk_speed = db.Column(db.Float, default=5)
    run_speed = db.Column(db.Float, default=8)

def ensure_columns():
    """Ensure new columns exist in the workout_entry table."""
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('workout_entry')]
    with db.engine.begin() as conn:
        if 'weight' not in columns:
            conn.execute(text('ALTER TABLE workout_entry ADD COLUMN weight FLOAT DEFAULT 0'))
        if 'km_walked' not in columns:
            conn.execute(text('ALTER TABLE workout_entry ADD COLUMN km_walked FLOAT DEFAULT 0'))

def create_backup():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    
    # Get all entries and save them to a JSON file
    entries = WorkoutEntry.query.all()
    backup_data = [
        {
            'date': entry.date.strftime('%Y-%m-%d'),
            'pull_ups': entry.pull_ups,
            'push_ups': entry.push_ups,
            'sit_ups': entry.sit_ups,
            'squats': entry.squats,
            'km_ran': entry.km_ran,
            'km_walked': entry.km_walked,
            'weight': entry.weight
        }
        for entry in entries
    ]
    
    # Shift existing backups
    for i in range(MAX_BACKUPS - 2, -1, -1):
        old_file = os.path.join(BACKUP_FOLDER, f'backup_{i}.json')
        new_file = os.path.join(BACKUP_FOLDER, f'backup_{i + 1}.json')
        if os.path.exists(old_file):
            if os.path.exists(new_file):
                os.remove(new_file)
            os.rename(old_file, new_file)
    
    # Save new backup
    with open(os.path.join(BACKUP_FOLDER, 'backup_0.json'), 'w') as f:
        json.dump(backup_data, f)

def restore_latest_backup():
    for i in range(MAX_BACKUPS):
        backup_file = os.path.join(BACKUP_FOLDER, f'backup_{i}.json')
        if os.path.exists(backup_file):
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Clear current data
            WorkoutEntry.query.delete()
            
            # Restore from backup
            for entry_data in backup_data:
                entry = WorkoutEntry(
                    date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date(),
                    pull_ups=entry_data['pull_ups'],
                    push_ups=entry_data['push_ups'],
                    sit_ups=entry_data['sit_ups'],
                    squats=entry_data['squats'],
                    km_ran=entry_data['km_ran'],
                    km_walked=entry_data.get('km_walked', 0),
                    weight=entry_data.get('weight', 0)
                )
                db.session.add(entry)
            
            db.session.commit()
            return True
    return False

def calculate_calories(entry):
    prefs = UserSettings.query.first()
    weight = entry.weight if entry.weight else 70
    run_speed = prefs.run_speed if prefs else 8
    walk_speed = prefs.walk_speed if prefs else 5

    running_per_km = 1.036 * weight * (run_speed / 8)
    walking_per_km = 0.53 * weight * (walk_speed / 5)

    calories = {
        'pull_ups': entry.pull_ups * 1,
        'push_ups': entry.push_ups * 0.5,
        'sit_ups': entry.sit_ups * 0.3,
        'squats': entry.squats * 0.5,
        'running': entry.km_ran * running_per_km,
        'walking': entry.km_walked * walking_per_km
    }
    return sum(calories.values())

def get_backup_info(backup_data):
    total_calories = sum(
        calculate_calories(WorkoutEntry(
            date=datetime.strptime(entry['date'], '%Y-%m-%d').date(),
            pull_ups=entry['pull_ups'],
            push_ups=entry['push_ups'],
            sit_ups=entry['sit_ups'],
            squats=entry['squats'],
            km_ran=entry['km_ran'],
            km_walked=entry.get('km_walked', 0),
            weight=entry.get('weight', 0)
        )) for entry in backup_data
    )
    
    latest_date = max(entry['date'] for entry in backup_data)
    return {
        'total_calories': total_calories,
        'latest_date': latest_date
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats_page():
    return render_template('stats.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/api/workout', methods=['GET'])
def get_workout():
    today = datetime.now().date()
    entry = WorkoutEntry.query.filter_by(date=today).first()
    
    if not entry:
        entry = WorkoutEntry(date=today)
        db.session.add(entry)
        db.session.commit()
    
    return jsonify(entry.to_dict())

@app.route('/api/workout/update', methods=['POST'])
def update_workout():
    today = datetime.now().date()
    entry = WorkoutEntry.query.filter_by(date=today).first()
    if not entry:
        entry = WorkoutEntry(date=today)
        db.session.add(entry)
    
    data = request.json
    exercise = data.get('exercise')
    value = data.get('value', 0)
    
    if hasattr(entry, exercise):
        setattr(entry, exercise, value)
        db.session.commit()
        return jsonify(entry.to_dict())

    return jsonify({'error': 'Invalid exercise'}), 400

@app.route('/api/settings', methods=['GET'])
def get_settings():
    prefs = UserSettings.query.first()
    today = datetime.now().date()
    entry = WorkoutEntry.query.filter_by(date=today).first()
    weight = entry.weight if entry else 0
    return jsonify({
        'weight': weight,
        'walk_speed': prefs.walk_speed if prefs else 5,
        'run_speed': prefs.run_speed if prefs else 8
    })

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    data = request.json
    prefs = UserSettings.query.first()
    if not prefs:
        prefs = UserSettings()
        db.session.add(prefs)
    prefs.walk_speed = data.get('walk_speed', prefs.walk_speed)
    prefs.run_speed = data.get('run_speed', prefs.run_speed)
    today = datetime.now().date()
    entry = WorkoutEntry.query.filter_by(date=today).first()
    if not entry:
        entry = WorkoutEntry(date=today)
        db.session.add(entry)
    if 'weight' in data:
        entry.weight = data['weight']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    all_entries = WorkoutEntry.query.all()
    total_stats = {
        'total_pull_ups': sum(entry.pull_ups for entry in all_entries),
        'total_push_ups': sum(entry.push_ups for entry in all_entries),
        'total_sit_ups': sum(entry.sit_ups for entry in all_entries),
        'total_squats': sum(entry.squats for entry in all_entries),
        'total_km_ran': sum(entry.km_ran for entry in all_entries),
        'total_km_walked': sum(entry.km_walked for entry in all_entries),
        'total_calories': sum(calculate_calories(entry) for entry in all_entries)
    }
    return jsonify(total_stats)

@app.route('/api/daily_stats', methods=['GET'])
def get_daily_stats():
    entries = WorkoutEntry.query.order_by(WorkoutEntry.date).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/reset', methods=['POST'])
def reset_data():
    # Create backup before resetting
    create_backup()
    
    # Delete all entries
    WorkoutEntry.query.delete()
    db.session.commit()
    
    # Create new entry for today
    today = datetime.now().date()
    entry = WorkoutEntry(date=today)
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/api/restore', methods=['POST'])
def restore_data():
    if restore_latest_backup():
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'No backup available'}), 404

@app.route('/api/backups', methods=['GET'])
def get_backups():
    backups = []
    for i in range(MAX_BACKUPS):
        backup_file = os.path.join(BACKUP_FOLDER, f'backup_{i}.json')
        if os.path.exists(backup_file):
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
                info = get_backup_info(backup_data)
                backups.append({
                    'id': i,
                    'total_calories': info['total_calories'],
                    'latest_date': info['latest_date']
                })
        else:
            backups.append(None)
    return jsonify(backups)

@app.route('/api/restore/<int:backup_id>', methods=['POST'])
def restore_specific_backup(backup_id):
    if backup_id < 0 or backup_id >= MAX_BACKUPS:
        return jsonify({'status': 'error', 'message': 'Invalid backup ID'}), 400
        
    backup_file = os.path.join(BACKUP_FOLDER, f'backup_{backup_id}.json')
    if not os.path.exists(backup_file):
        return jsonify({'status': 'error', 'message': 'Backup not found'}), 404
        
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    # Clear current data
    WorkoutEntry.query.delete()
    
    # Restore from backup
    for entry_data in backup_data:
        entry = WorkoutEntry(
            date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date(),
            pull_ups=entry_data['pull_ups'],
            push_ups=entry_data['push_ups'],
            sit_ups=entry_data['sit_ups'],
            squats=entry_data['squats'],
            km_ran=entry_data['km_ran'],
            km_walked=entry_data.get('km_walked', 0),
            weight=entry_data.get('weight', 0)
        )
        db.session.add(entry)
    
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_columns()
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
