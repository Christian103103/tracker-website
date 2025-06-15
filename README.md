# Workout Tracker

A simple web application to track your daily workouts and calculate calories burned.

## Features

- Track daily exercises:
  - Pull-ups
  - Push-ups
  - Sit-ups
  - Squats
  - Kilometers ran
  - Kilometers walked
- Increment counts by 1, 5, 10, or 20
- Decrement counts if needed
- Calculate calories burned (daily and total)
- Persistent storage using SQLite database

## Setup

1. Make sure you have Python 3.7+ installed on your system.

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

- Click the increment buttons (+1, +5, +10, +20) to add exercises
- Use the -1 button to correct any mistakes
- The calories burned will automatically update
- Data is saved automatically and persists between sessions
- View both today's calories and total calories burned at the bottom of the page

## Calorie Calculations

The application uses the following approximate calorie calculations:
- Pull-ups: 1 calorie per rep
- Push-ups: 0.5 calories per rep
- Sit-ups: 0.3 calories per rep
- Squats: 0.5 calories per rep
- Running: 60 calories per kilometer
- Walking: 50 calories per kilometer
