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

The application calculates calories using both fixed values and formulas that
depend on your weight and preferred speeds. You can adjust your weight, walking
speed and running speed in the **Settings** page.

- Pull-ups: 1 calorie per rep
- Push-ups: 0.5 calories per rep
- Sit-ups: 0.3 calories per rep
- Squats: 0.5 calories per rep
- Running: `1.036 × weight × (running speed / 8)` calories per kilometer
- Walking: `0.53 × weight × (walking speed / 5)` calories per kilometer

If you haven't provided values in the settings, the calculation defaults to a
weight of 70&nbsp;kg, running speed of 8&nbsp;km/h and walking speed of
5&nbsp;km/h.
