from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # You can change this

# Load data
df = pd.read_excel("verbs.xlsx")
df = df.drop(columns=["#"]).reset_index(drop=True)
languages = df.columns.tolist()

# Divide into groups
verbs_per_group = 15
groups = [(i * verbs_per_group, min((i + 1) * verbs_per_group, len(df))) for i in range((len(df) + verbs_per_group - 1) // verbs_per_group)]


@app.route('/')
def index():
    return render_template("index.html", languages=languages, groups=enumerate(groups, start=1))


@app.route('/quiz/start', methods=['POST'])
def start_quiz():
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    group_number = int(request.form['group'])
    start, end = groups[group_number - 1]
    group_df = df.iloc[start:end].copy()

    questions = []
    all_options = df[target_lang].dropna().unique().tolist()

    for _, row in group_df.iterrows():
        question = row[source_lang]
        correct = row[target_lang]
        options = random.sample([opt for opt in all_options if opt != correct], 3)
        options.append(correct)
        random.shuffle(options)

        questions.append({
            'question': question,
            'correct': correct,
            'options': options
        })

    session['questions'] = questions
    session['source_lang'] = source_lang
    session['target_lang'] = target_lang
    session['answers'] = ['' for _ in questions]

    return redirect(url_for('show_question', qid=0))


@app.route('/quiz/question/<int:qid>', methods=['GET', 'POST'])
def show_question(qid):
    questions = session.get('questions')
    answers = session.get('answers')

    if request.method == 'POST':
        selected = request.form.get('answer')
        if selected:
            answers[qid - 1] = selected
            session['answers'] = answers

    if qid < 0 or qid >= len(questions):
        return redirect(url_for('show_results'))

    return render_template('question.html',
                           qid=qid,
                           question=questions[qid],
                           total=len(questions),
                           selected=answers[qid],
                           source_lang=session.get('source_lang'),
                           target_lang=session.get('target_lang'))


@app.route('/quiz/submit', methods=['POST'])
def show_results():
    questions = session.get('questions')
    answers = session.get('answers')

    score = 0
    results = []

    for i, q in enumerate(questions):
        selected = answers[i]
        correct = q['correct']
        is_correct = selected == correct
        if is_correct:
            score += 1
        results.append({
            'question': q['question'],
            'selected': selected,
            'correct_answer': correct,
            'correct': is_correct
        })

    return render_template('results.html', score=score, total=len(questions), results=results)


if __name__ == '__main__':
    app.run(debug=True)
