import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for DOCX processing
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_details(resume_text):
    # Placeholder extraction logic (implement specific logic to extract CGPA, skills, etc.)
    details = {
        "name": "John Doe",
        "cgpa": "8.5",
        "projects": "Machine Learning, Web Development",
        "skills": "Python, Flask, React",
    }
    return details

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"})

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    if file.filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(file_path)
    elif file.filename.endswith('.docx'):
        resume_text = extract_text_from_docx(file_path)
    else:
        return jsonify({"error": "Unsupported file format"})

    # Step 1: Print extracted resume text in the terminal
    print("Extracted Text from Resume:\n", resume_text)  # Debugging step

    extracted_details = extract_details(resume_text)
    return jsonify(extracted_details)

if __name__ == '__main__':
    app.run(debug=True)
