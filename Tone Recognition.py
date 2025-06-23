import os
import random
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

BASE_DIR = '/Users/lijiachen/Desktop/硕士/25 Spring/7.15 Experiments with Speech/Final Project'
TONE_STIMULI_DIR = os.path.join(BASE_DIR, 'Stimuli')
VOCODED_STIMULI_DIR = os.path.join(BASE_DIR, 'Noise Vocoded Stimuli')
TEST_SAMPLES = ['Recording_test.wav', 'Recording_test_vocoded_nB4.wav']

WELCOME_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Mandarin Tone Recognition in Natural and Noise-vocoded Speech</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial; }
        form { text-align: center; }
    </style>
</head>
<body>
    <form method="post">
        <h2>Mandarin Tone Recognition in Natural and Noise-vocoded Speech</h2>
        <p>Gender<br>
            <select name="gender" required>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Prefer not to say">Prefer not to say</option>
            </select>
        </p>
        <p>Age<br><input type="number" name="age" required></p>
        <p>Full Name<br><input type="text" name="name" required></p>
        <input type="submit" value="Continue">
    </form>
</body>
</html>
"""

TEST_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Audio Check</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial; text-align: center; flex-direction: column; }
    </style>
</head>
<body>
    <h2>Please listen to the following audio samples and adjust your volume accordingly.</h2>
    <p>This is a sample of natural Mandarin speech:</p>
    <audio controls>
        <source src="{{ url_for('static', filename='stimuli/' + test1) }}" type="audio/wav">
    </audio>
    <p>This is a sample of noise-vocoded Mandarin speech:</p>
    <audio controls>
        <source src="{{ url_for('static', filename='stimuli/' + test2) }}" type="audio/wav">
    </audio>
    <form method="post">
        <input type="submit" value="Next">
    </form>
</body>
</html>
"""

PHASE_INTRO_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Phase Start</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial; text-align: center; flex-direction: column; }
    </style>
</head>
<body>
    <h2>{{ message }}</h2>
    <form method="post">
        <input type="submit" value="Start">
    </form>
</body>
</html>
"""

EXPERIMENT_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Stimuli Test</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; text-align: center; font-family: Arial; flex-direction: column; }
        form { margin-top: 20px; }
        .option { margin: 10px 0; }
    </style>
</head>
<body>
    <audio autoplay>
        <source src="{{ url_for('static', filename='stimuli/' + filename) }}" type="audio/wav">
    </audio>
    <form method="post">
        {% for option in ['Tone 1', 'Tone 2', 'Tone 3', 'Tone 4'] %}
            <div class="option">
                <input type="radio" name="answer" value="{{ loop.index }}" required> {{ option }}
            </div>
        {% endfor %}
        <div style="margin-top: 20px;">
            <input type="submit" value="Next">
        </div>
    </form>
</body>
</html>
"""

FINISH_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Download Results</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; text-align: center; font-family: Arial; }
    </style>
</head>
<body>
    <div>
        <h2>Thank you for participating in the experiment.</h2>
        <p>Please click the button below to download your results.</p>
        <form action="{{ url_for('download') }}">
            <button type="submit">Download Results</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['gender'] = request.form['gender']
        session['age'] = request.form['age']
        session['name'] = request.form['name']
        session['results'] = []

        if not os.path.exists('static/stimuli'):
            os.makedirs('static/stimuli')
        for f in TEST_SAMPLES:
            os.system(f'cp "{os.path.join(BASE_DIR, f)}" "static/stimuli/{f}"')

        return redirect(url_for('audio_test'))
    return render_template_string(WELCOME_TEMPLATE)

@app.route('/audio_test', methods=['GET', 'POST'])
def audio_test():
    if request.method == 'POST':
        session['phase'] = 'tone'
        session['stimuli'] = random.sample(os.listdir(TONE_STIMULI_DIR), 100)
        session['current_index'] = 0
        return redirect(url_for('phase_start'))
    return render_template_string(TEST_TEMPLATE, test1=TEST_SAMPLES[0], test2=TEST_SAMPLES[1])

@app.route('/phase_start', methods=['GET', 'POST'])
def phase_start():
    if request.method == 'POST':
        return redirect(url_for('experiment'))
    message = "Please select the perceived tone in the stimuli of natural Mandarin speech." if session['phase'] == 'tone' else "Please select the perceived tone in the stimuli of noise-vocoded Mandarin speech."
    return render_template_string(PHASE_INTRO_TEMPLATE, message=message)

@app.route('/experiment', methods=['GET', 'POST'])
def experiment():
    if 'stimuli' not in session:
        return redirect(url_for('index'))

    stimuli_list = session['stimuli']
    idx = session['current_index']

    if request.method == 'POST' and idx > 0:
        user_answer = int(request.form['answer'])
        filename = stimuli_list[idx - 1]

        base_name = filename.split('_')[1]
        for ch in reversed(base_name):
            if ch.isdigit():
                correct = int(ch)
                break
        else:
            correct = 0

        session['results'].append((filename, user_answer, correct))

    if idx >= len(stimuli_list):
        if session['phase'] == 'tone':
            session['phase'] = 'vocoded'
            session['stimuli'] = random.sample(os.listdir(VOCODED_STIMULI_DIR), 40)
            session['current_index'] = 0
            return redirect(url_for('phase_start'))
        else:
            session['end_time'] = str(datetime.datetime.now())
            return redirect(url_for('finish'))

    filename = stimuli_list[idx]
    session['current_index'] += 1
    folder = 'Stimuli' if session['phase'] == 'tone' else 'Noise Vocoded Stimuli'
    full_path = os.path.join(BASE_DIR, folder, filename)
    static_path = os.path.join('static/stimuli', filename)
    os.system(f'cp "{full_path}" "{static_path}"')

    return render_template_string(EXPERIMENT_TEMPLATE, filename=filename)

@app.route('/finish')
def finish():
    return render_template_string(FINISH_TEMPLATE)

@app.route('/download')
def download():
    name = session['name']
    age = session['age']
    gender = session['gender']
    end_time = session.get('end_time', str(datetime.datetime.now()))
    results = session['results']

    output_path = f"{name.replace(' ', '_')}_results.txt"
    with open(output_path, 'w') as f:
        f.write(f"Participant: {name}\nAge: {age}\nGender: {gender}\nSubmission Time: {end_time}\n\n")
        f.write("Filename\tAnswer\tTone\n")
        for filename, answer, correct in results:
            f.write(f"{filename}\t{answer}\t{correct}\n")

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)