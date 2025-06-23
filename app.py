from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import random
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话加密

# 定义基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 音频刺激路径
stimuli_path = os.path.join(BASE_DIR, 'static', 'Noise Vocoded Stimuli')
test_audio_path = os.path.join(BASE_DIR, 'static', 'Recording_test_vocoded_nB4.wav')

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/audio_test')
def audio_test():
    return render_template('audio_test.html', test_audio='Recording_test_vocoded_nB4.wav')

@app.route('/pre_instruction')
def pre_instruction():
    return render_template('pre-instruction.html')

@app.route('/experiment')
def experiment():
    file_list = [f for f in os.listdir(stimuli_path) if f.endswith('.wav')]
    random.shuffle(file_list)
    session['stimuli_list'] = file_list
    session['responses'] = []
    session['start_time'] = datetime.now().isoformat()
    return redirect(url_for('next_trial'))

@app.route('/next_trial', methods=['GET', 'POST'])
def next_trial():
    if request.method == 'POST':
        response = {
            'stimulus': session['current_stimulus'],
            'response': request.form['response'],
            'timestamp': datetime.now().isoformat()
        }
        session['responses'].append(response)

    stimuli_list = session.get('stimuli_list', [])
    if not stimuli_list:
        return redirect(url_for('finish'))

    current_stimulus = stimuli_list.pop()
    session['current_stimulus'] = current_stimulus
    session['stimuli_list'] = stimuli_list
    return render_template('experiment.html', stimulus=current_stimulus)

@app.route('/finish')
def finish():
    # 导出 CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['stimulus', 'response', 'timestamp'])
    writer.writeheader()
    for row in session.get('responses', []):
        writer.writerow(row)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='responses.csv'
    )

# 本地测试入口
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # 默认为5000，Render部署时会自动提供PORT
    app.run(host='0.0.0.0', port=port)