# Flask Habit Tracker Application
# Complete implementation with SQLite database

from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta
import calendar
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
BASE_DIR = Path(__file__).parent
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'habits.db'))
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database Models
class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    emoji = db.Column(db.String(10), default='⭐')
    color = db.Column(db.String(50), default='bg-blue-100')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completions = db.relationship('Completion', backref='habit', lazy=True, cascade='all, delete-orphan')

class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=True)
    
    __table_args__ = (db.Index('idx_habit_date', 'habit_id', 'date', unique=True),)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Habits Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .habit-checkbox {
            transition: all 0.2s;
        }
        .habit-checkbox:hover {
            transform: scale(1.1);
        }
        .chart-container {
            height: 200px;
        }
    </style>
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    <div class="container mx-auto p-4 md:p-8 max-w-7xl">
        <!-- Header -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 class="text-3xl md:text-4xl font-bold text-gray-800 mb-2" id="currentMonth"></h1>
                    <p class="text-gray-600">Track your daily habits</p>
                </div>
                <div class="flex gap-4">
                    <div class="bg-blue-50 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-blue-600" id="totalHabits">0</div>
                        <div class="text-xs text-gray-600">Number of habits</div>
                    </div>
                    <div class="bg-green-50 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-green-600" id="completedHabits">0</div>
                        <div class="text-xs text-gray-600">Completed today</div>
                    </div>
                    <div class="bg-purple-50 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-purple-600" id="progressPercent">0%</div>
                        <div class="text-xs text-gray-600">Progress</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Month Navigation -->
        <div class="bg-white rounded-2xl shadow-lg p-4 mb-6 flex items-center justify-between">
            <button onclick="changeMonth(-1)" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                ← Previous
            </button>
            <div class="text-lg font-semibold" id="monthDisplay"></div>
            <button onclick="changeMonth(1)" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                Next →
            </button>
        </div>

        <!-- Habits Table -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full" id="habitsTable" style="border-collapse: separate; border-spacing: 0;">
                    <thead class="bg-gray-50 border-b">
                        <tr>
                            <th class="px-4 py-3 text-left font-semibold text-gray-700 min-w-[200px]">My Habits</th>
                            <th colspan="7" class="px-2 py-3 text-center text-sm text-gray-600 border-r-2 border-gray-300">Week 1</th>
                            <th colspan="7" class="px-2 py-3 text-center text-sm text-gray-600 border-r-2 border-gray-300">Week 2</th>
                            <th colspan="7" class="px-2 py-3 text-center text-sm text-gray-600 border-r-2 border-gray-300">Week 3</th>
                            <th colspan="7" class="px-2 py-3 text-center text-sm text-gray-600">Week 4</th>
                        </tr>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2"></th>
                            <th class="px-2 py-2 text-xs text-center">Su</th>
                            <th class="px-2 py-2 text-xs text-center">Mo</th>
                            <th class="px-2 py-2 text-xs text-center">Tu</th>
                            <th class="px-2 py-2 text-xs text-center">We</th>
                            <th class="px-2 py-2 text-xs text-center">Th</th>
                            <th class="px-2 py-2 text-xs text-center">Fr</th>
                            <th class="px-2 py-2 text-xs text-center border-r-2 border-gray-300">Sa</th>
                            <th class="px-2 py-2 text-xs text-center">Su</th>
                            <th class="px-2 py-2 text-xs text-center">Mo</th>
                            <th class="px-2 py-2 text-xs text-center">Tu</th>
                            <th class="px-2 py-2 text-xs text-center">We</th>
                            <th class="px-2 py-2 text-xs text-center">Th</th>
                            <th class="px-2 py-2 text-xs text-center">Fr</th>
                            <th class="px-2 py-2 text-xs text-center border-r-2 border-gray-300">Sa</th>
                            <th class="px-2 py-2 text-xs text-center">Su</th>
                            <th class="px-2 py-2 text-xs text-center">Mo</th>
                            <th class="px-2 py-2 text-xs text-center">Tu</th>
                            <th class="px-2 py-2 text-xs text-center">We</th>
                            <th class="px-2 py-2 text-xs text-center">Th</th>
                            <th class="px-2 py-2 text-xs text-center">Fr</th>
                            <th class="px-2 py-2 text-xs text-center border-r-2 border-gray-300">Sa</th>
                            <th class="px-2 py-2 text-xs text-center">Su</th>
                            <th class="px-2 py-2 text-xs text-center">Mo</th>
                            <th class="px-2 py-2 text-xs text-center">Tu</th>
                            <th class="px-2 py-2 text-xs text-center">We</th>
                            <th class="px-2 py-2 text-xs text-center">Th</th>
                            <th class="px-2 py-2 text-xs text-center">Fr</th>
                            <th class="px-2 py-2 text-xs text-center">Sa</th>
                        </tr>
                        <!-- Horizontal line below week header row -->
                        <tr>
                            <th class="px-4 py-0"></th>
                            <th colspan="28" class="border-t-2 border-gray-400"></th>
                        </tr>
                    
                        </tr>
                        <!-- Day number row directly above checkboxes -->
                        <tr class="bg-gray-50" id="dayNumberRow">
                            <th class="px-4 py-2"></th>
                            <!-- Day numbers will be populated by JavaScript -->
                        </tr>
                        <!-- Line above day numbers -->
                        <tr>
                            <th class="px-4 py-0"></th>
                            <th colspan="28" class="border-t-2 border-gray-400"></th>
                        </tr>
                    </thead>
                    <tbody id="habitsBody">
                        <!-- Habits will be loaded here -->
                    </tbody>
                    <tbody id="addHabitRow" class="bg-gray-50 border-t-2 border-gray-200">
                        <tr>
                            <td class="px-4 py-3 min-w-[200px]">
                                <div class="flex flex-col gap-2">
                                    <div class="flex flex-col sm:flex-row gap-2 items-center">
                                        <input type="text" id="habitEmoji" placeholder="😊" maxlength="2" 
                                            class="w-14 px-2 py-2 border-2 border-gray-300 rounded-lg text-center text-lg focus:outline-none focus:border-blue-500 transition">
                                        <input type="text" id="habitName" placeholder="New habit..." 
                                            class="flex-1 px-3 py-2 border-2 border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:border-blue-500 transition">
                                        <button onclick="addHabit()" 
                                            class="px-5 py-2 bg-blue-500 text-white text-sm font-semibold rounded-lg hover:bg-blue-600 transition">
                                            + Add
                                        </button>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                    <tfoot id="progressSummary"></tfoot>
                </table>
            </div>
        </div>

        <!-- Progress Chart -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mt-6">
            <h2 class="text-xl font-bold mb-4">Monthly Progress</h2>
            <div class="chart-container">
                <canvas id="progressChart"></canvas>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let currentDate = new Date();
        let habits = [];
        let progressChart = null;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            updateMonthDisplay();
            loadHabits();
        });

        function updateMonthDisplay() {
            const monthNames = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"];
            document.getElementById('currentMonth').textContent = monthNames[currentDate.getMonth()];
            document.getElementById('monthDisplay').textContent = 
                monthNames[currentDate.getMonth()] + ' ' + currentDate.getFullYear();
            updateDayHeaders();
        }

        function updateDayHeaders() {
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            const daysInMonth = new Date(year, month + 1, 0).getDate();

            // Generate individual day numbers
            const dayNumberRow = document.getElementById('dayNumberRow');
            let dayHTML = '';
            
            for (let day = 1; day <= daysInMonth; day++) {
                dayHTML += `<th class="px-2 py-2 text-xs font-medium text-gray-600">${day}</th>`;
            }
            
            dayNumberRow.innerHTML = '<th class="px-4 py-2"></th>' + dayHTML;
        }

        function changeMonth(delta) {
            currentDate.setMonth(currentDate.getMonth() + delta);
            updateMonthDisplay();
            loadHabits();
        }

        async function loadHabits() {
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth() + 1;
            
            const response = await fetch(`/api/habits?year=${year}&month=${month}`);
            const data = await response.json();
            habits = data.habits;
            
            renderHabits(data.habits, data.completions);
            updateStats(data.habits, data.completions);
            updateChart(data.daily_stats);
        }

        function renderHabits(habits, completions) {
            const tbody = document.getElementById('habitsBody');
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            const daysInMonth = new Date(year, month + 1, 0).getDate();

            tbody.innerHTML = habits.map(habit => {
                let completedCount = 0;
                let weekCells = [];
                // Calculate how many weeks are needed for this month
                const firstDayOfWeek = new Date(year, month, 1).getDay();
                let weeks = Math.ceil((daysInMonth + firstDayOfWeek) / 7);
                weeks = Math.max(weeks, 4);
                for (let week = 0; week < weeks; week++) {
                    let weekHTML = '';
                    for (let dayOfWeek = 1; dayOfWeek <= 7; dayOfWeek++) {
                        let day = week * 7 + dayOfWeek;
                        if (day > daysInMonth) {
                            weekHTML += `<td class="px-2 py-2 text-center${dayOfWeek === 7 ? ' border-r-2 border-gray-300' : ''}"></td>`;
                        } else {
                            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                            const isCompleted = completions[`${habit.id}-${dateStr}`] || false;
                            if (isCompleted) completedCount++;
                            weekHTML += `
                                <td class="px-2 py-2 text-center${dayOfWeek === 7 ? ' border-r-2 border-gray-300' : ''} ${isCompleted ? 'bg-gray-200' : ''}">
                                    <input type="checkbox" ${isCompleted ? 'checked' : ''} 
                                        onchange="toggleCompletion(${habit.id}, '${dateStr}')"
                                        class="habit-checkbox w-5 h-5 cursor-pointer rounded border-gray-300 
                                        text-green-500 focus:ring-green-500">
                                </td>
                            `;
                        }
                    }
                    weekCells.push(weekHTML);
                }
                // Show streaks and best streaks next to habit name
                return `
                    <tr class="border-b hover:bg-gray-50 transition habit-row" data-habit-id="${habit.id}">
                        <td class="px-4 py-3">
                            <div class="${habit.color} rounded-lg px-3 py-2 flex flex-col gap-2">
                                <div class="flex items-center gap-2 justify-between">
                                    <div class="flex items-center gap-2">
                                        <span class="text-xl">${habit.emoji}</span>
                                        <span class="font-medium text-gray-800">${habit.name}</span>
                                    </div>
                                    <button onclick="deleteHabit(${habit.id})" class="delete-btn px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition opacity-0 hover:opacity-100 transition-opacity" title="Click to delete this habit">
                                        Delete
                                    </button>
                                </div>
                                <div class="flex gap-2 text-xs text-gray-600">
                                    <span>Streak: <span class="font-bold text-green-600">${habit.current_streak || 0}</span></span>
                                    <span>Best: <span class="font-bold text-blue-600">${habit.best_streak || 0}</span></span>
                                    <span>Done: <span class="font-bold">${completedCount}</span></span>
                                </div>
                            </div>
                        </td>
                        ${weekCells.join('')}
                    </tr>
                `;
            }).join('');

            // Progress summary row (like spreadsheet)
            const progressSummary = document.getElementById('progressSummary');
            let doneRow = '<tr class="bg-gray-50"><td class="px-4 py-2 font-semibold text-gray-700">Done</td>';
            let notDoneRow = '<tr class="bg-gray-50"><td class="px-4 py-2 font-semibold text-gray-700">Not Done</td>';
            let percentRow = '<tr class="bg-gray-50"><td class="px-4 py-2 font-semibold text-gray-700">Progress</td>';
            for (let day = 1; day <= daysInMonth; day++) {
                let done = 0;
                let notDone = 0;
                for (let habit of habits) {
                    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                    if (completions[`${habit.id}-${dateStr}`]) {
                        done++;
                    } else {
                        notDone++;
                    }
                }
                let percent = habits.length > 0 ? Math.round((done / habits.length) * 100) : 0;
                doneRow += `<td class="px-2 py-2 text-center text-xs">${done}</td>`;
                notDoneRow += `<td class="px-2 py-2 text-center text-xs">${notDone}</td>`;
                percentRow += `<td class="px-2 py-2 text-center text-xs">${percent}%</td>`;
            }
            doneRow += '</tr>';
            notDoneRow += '</tr>';
            percentRow += '</tr>';
            progressSummary.innerHTML = percentRow + doneRow + notDoneRow;
        }

        async function addHabit() {
            const name = document.getElementById('habitName').value.trim();
            const emoji = document.getElementById('habitEmoji').value.trim() || '⭐';
            
            if (!name) {
                alert('Please enter a habit name');
                return;
            }
            
            if (name.length > 100) {
                alert('Habit name must be less than 100 characters');
                return;
            }
            
            try {
                const response = await fetch('/api/habits', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, emoji})
                });
                
                if (!response.ok) {
                    throw new Error('Failed to add habit');
                }
                
                document.getElementById('habitName').value = '';
                document.getElementById('habitEmoji').value = '';
                await loadHabits();
            } catch (error) {
                console.error('Error adding habit:', error);
                alert('Error adding habit. Please try again.');
            }
        }

        async function deleteHabit(habitId) {
            if (confirm('Are you sure you want to delete this habit?')) {
                try {
                    const response = await fetch(`/api/habits/${habitId}`, {method: 'DELETE'});
                    if (!response.ok) {
                        throw new Error('Failed to delete habit');
                    }
                    await loadHabits();
                } catch (error) {
                    console.error('Error deleting habit:', error);
                    alert('Error deleting habit. Please try again.');
                }
            }
        }

        async function toggleCompletion(habitId, date) {
            try {
                const response = await fetch('/api/completions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({habit_id: habitId, date})
                });
                if (!response.ok) {
                    throw new Error('Failed to toggle completion');
                }
                await loadHabits();
            } catch (error) {
                console.error('Error toggling completion:', error);
            }
        }

        function updateStats(habits, completions) {
            const today = new Date().toISOString().split('T')[0];
            const todayCompletions = Object.entries(completions)
                .filter(([key, val]) => val && key.includes(today)).length;
            
            document.getElementById('totalHabits').textContent = habits.length;
            document.getElementById('completedHabits').textContent = todayCompletions;
            
            const totalPossible = habits.length;
            const percentage = totalPossible > 0 ? Math.round((todayCompletions / totalPossible) * 100) : 0;
            document.getElementById('progressPercent').textContent = percentage + '%';
        }

        function updateChart(dailyStats) {
            const ctx = document.getElementById('progressChart').getContext('2d');
            
            if (progressChart) {
                progressChart.destroy();
            }
            
            const labels = dailyStats.map(d => d.day);
            const data = dailyStats.map(d => d.percentage);
            
            progressChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Daily Progress %',
                        data: data,
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

# API Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/habits', methods=['GET'])
def get_habits():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    habits = Habit.query.all()

    # Get completions for the month
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

    completions_dict = {}
    habit_streaks = {}
    today = datetime.now().date()
    for habit in habits:
        # All completions for this habit
        all_comps = Completion.query.filter_by(habit_id=habit.id, completed=True).order_by(Completion.date.asc()).all()
        dates = [comp.date for comp in all_comps]

        # Month-wise streak calculation (counting from today backwards, within current month)
        streak = 0
        current_check_date = min(today, last_day)  # Don't count beyond the current month's end
        while current_check_date >= first_day and current_check_date in dates:
            streak += 1
            current_check_date -= timedelta(days=1)

        # Best streak calculation (month-wise only)
        best_streak = 0
        month_dates = [d for d in dates if first_day <= d <= last_day]
        if month_dates:
            sorted_dates = sorted(month_dates)
            temp_streak = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                    temp_streak += 1
                else:
                    best_streak = max(best_streak, temp_streak)
                    temp_streak = 1
            best_streak = max(best_streak, temp_streak)
        habit_streaks[habit.id] = {
            'current_streak': streak,
            'best_streak': best_streak
        }

        # Month completions
        comps = Completion.query.filter(
            Completion.habit_id == habit.id,
            Completion.date >= first_day,
            Completion.date <= last_day,
            Completion.completed == True
        ).all()
        for comp in comps:
            key = f"{habit.id}-{comp.date}"
            completions_dict[key] = True

    # Calculate daily stats for chart (month-wise)
    daily_stats = []
    current_date = first_day
    while current_date <= last_day:
        day_completions = sum(1 for k, v in completions_dict.items() 
                            if v and k.endswith(str(current_date)))
        percentage = (day_completions / len(habits) * 100) if habits else 0
        daily_stats.append({
            'day': current_date.day,
            'percentage': round(percentage, 1)
        })
        current_date += timedelta(days=1)

    return jsonify({
        'habits': [{
            'id': h.id,
            'name': h.name,
            'emoji': h.emoji,
            'color': h.color,
            'current_streak': habit_streaks.get(h.id, {}).get('current_streak', 0),
            'best_streak': habit_streaks.get(h.id, {}).get('best_streak', 0)
        } for h in habits],
        'completions': completions_dict,
        'daily_stats': daily_stats
    })

@app.route('/api/habits', methods=['POST'])
@csrf.exempt  # Enable CSRF protection; for production, remove @csrf.exempt and handle token properly
def create_habit():
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Habit name is required'}), 400
        
        name = str(data.get('name', '')).strip()
        emoji = str(data.get('emoji', '⭐')).strip()[:2]  # Limit to 2 chars
        
        if not name or len(name) > 100:
            return jsonify({'error': 'Habit name must be between 1-100 characters'}), 400
        
        colors = ['bg-orange-100', 'bg-blue-100', 'bg-purple-100', 'bg-green-100', 
                  'bg-yellow-100', 'bg-red-100', 'bg-pink-100', 'bg-indigo-100']
        
        habit = Habit(
            name=name,
            emoji=emoji or '⭐',
            color=colors[len(Habit.query.all()) % len(colors)]
        )
        db.session.add(habit)
        db.session.commit()
        logger.info(f'Created habit: {habit.id} - {name}')
        
        return jsonify({'id': habit.id}), 201
    except Exception as e:
        logger.error(f'Error creating habit: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to create habit'}), 500

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
@csrf.exempt
def delete_habit(habit_id):
    try:
        habit = Habit.query.get_or_404(habit_id)
        db.session.delete(habit)
        db.session.commit()
        logger.info(f'Deleted habit: {habit_id}')
        return '', 204
    except Exception as e:
        logger.error(f'Error deleting habit {habit_id}: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to delete habit'}), 500

@app.route('/api/completions', methods=['POST'])
@csrf.exempt
def toggle_completion():
    try:
        data = request.json
        if not data or 'habit_id' not in data or 'date' not in data:
            return jsonify({'error': 'habit_id and date are required'}), 400
        
        habit_id = int(data['habit_id'])
        
        # Validate date format
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Verify habit exists
        habit = Habit.query.get_or_404(habit_id)
        
        completion = Completion.query.filter_by(
            habit_id=habit_id,
            date=date
        ).first()
        
        if completion:
            db.session.delete(completion)
        else:
            completion = Completion(habit_id=habit_id, date=date)
            db.session.add(completion)
        
        db.session.commit()
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': 'Invalid input data'}), 400
    except Exception as e:
        logger.error(f'Error toggling completion: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle completion'}), 500

def init_db():
    """Initialize database with tables and sample data (one-time only)"""
    with app.app_context():
        db.create_all()
        logger.info('Database initialized')
        
        # Add sample habits only if database is completely empty
        if Habit.query.count() == 0:
            sample_habits = [
                {'name': 'Wake up at 6 AM', 'emoji': '☀️', 'color': 'bg-orange-100'},
                {'name': 'Gym', 'emoji': '💪', 'color': 'bg-blue-100'},
                {'name': 'Exam preparation', 'emoji': '📚', 'color': 'bg-purple-100'},
                {'name': 'Budget Tracking', 'emoji': '💰', 'color': 'bg-green-100'},
            ]
            
            try:
                for habit_data in sample_habits:
                    habit = Habit(**habit_data)
                    db.session.add(habit)
                db.session.commit()
                logger.info('Sample habits added')
            except Exception as e:
                logger.error(f'Error adding sample habits: {str(e)}')
                db.session.rollback()

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f'Server error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Get port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))
    
    # In production, set FLASK_ENV=production
    app.run(debug=DEBUG, port=port, host='0.0.0.0')