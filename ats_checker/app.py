from flask import Flask, render_template, request, jsonify, send_file
from pdfminer.high_level import extract_text
import docx2txt
import os
from fpdf import FPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORT_FOLDER'] = 'reports'

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

def extract_text_from_resume(file_path):
    if file_path.endswith('.pdf'):
        return extract_text(file_path).lower()
    elif file_path.endswith('.docx'):
        return docx2txt.process(file_path).lower()
    else:
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    job_desc = request.form.get('jobDesc', '')
    role = request.form.get('role', '')

    # Save uploaded resume
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    resume_text = extract_text_from_resume(file_path)

    # Keyword analysis
    keywords = list(set(job_desc.lower().split()))
    matched = [k for k in keywords if k in resume_text]
    missing = [k for k in keywords if k not in resume_text]
    ats_score = round((len(matched) / len(keywords)) * 100 if keywords else 0)

    # Generate PDF report
    report_name = f"{file.filename.split('.')[0]}_ATS_Report.pdf"
    report_path = os.path.join(app.config['REPORT_FOLDER'], report_name)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"ATS Resume Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    # Removed the Name field
    pdf.cell(0, 10, f"Role: {role}", ln=True)
    pdf.cell(0, 10, f"ATS Score: {ats_score}%", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Matched Keywords:", ln=True)
    for k in matched:
        pdf.cell(0, 10, f"- {k}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Missing Keywords:", ln=True)
    for k in missing:
        pdf.cell(0, 10, f"- {k}", ln=True)
    pdf.output(report_path)

    return jsonify({
        'atsScore': ats_score,
        'matched': matched,
        'missing': missing,
        'report': report_name
    })

@app.route('/download/<report_name>')
def download(report_name):
    path = os.path.join(app.config['REPORT_FOLDER'], report_name)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
