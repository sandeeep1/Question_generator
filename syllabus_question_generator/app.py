from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
from docx import Document
import PyPDF2
import random
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def extract_topics(text):
    modules = {}
    lines = text.split("\n")
    current_module = None
    for line in lines:
        if "module" in line.lower():
            current_module = line.strip()
            modules[current_module] = []
        elif current_module:
            modules[current_module].append(line.strip())
    return modules

def generate_questions(topics):
    questions = []
    for topic in topics:
        if topic:
            questions.append(f"Explain the concept of {topic} in detail.")
            questions.append(f"Discuss the applications of {topic}.")
            questions.append(f"Write short notes on {topic}.")
    return questions

def generate_question_sets(modules, num_sets):
    sets = []
    for _ in range(num_sets):
        question_set = {}
        for module, topics in modules.items():
            all_questions = generate_questions(topics)
            question_set[module] = random.sample(all_questions, min(5, len(all_questions)))
        sets.append(question_set)
    return sets

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def generate_pdf(question_sets):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []
    for i, qset in enumerate(question_sets):
        story.append(Paragraph(f"<b>Question Paper Set {i+1}</b>", styles['Title']))
        for module, questions in qset.items():
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>{module}</b>", styles['Heading2']))
            for q in questions:
                story.append(Paragraph(q, styles['Normal']))
        story.append(Spacer(1, 24))
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['syllabus']
        num_sets = int(request.form['num_sets'])
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            if filename.endswith('.docx'):
                text = extract_text_from_docx(filepath)
            elif filename.endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            else:
                return "Unsupported file format"
            modules = extract_topics(text)
            question_sets = generate_question_sets(modules, num_sets)
            pdf = generate_pdf(question_sets)
            return send_file(pdf, as_attachment=True, download_name="question_sets.pdf")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
