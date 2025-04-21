import os
import io
import re
import pickle
import numpy as np
from PIL import Image
from flask import Flask, request, render_template, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# Initialize Flask
app = Flask(__name__, template_folder="templates")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load models
model = pickle.load(open('model.pkl', 'rb'))
model1 = pickle.load(open('model1.pkl', 'rb'))

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/download_format')
def download_format():
    return send_from_directory('static/files', 'sample_resume.pdf', as_attachment=True)

def extract_info(text):
    data = {
        "name": "", "cgpa": "", "skills": "", "internship": "0",
        "hackathon": "0", "projects": "", "workshops": "",
        "mini_projects": "", "communication_skills": "", "tw_percentage": "",
        "te_percentage": "", "backlogs": ""
    }
    try:
        lines = text.strip().split('\n')
        data["name"] = lines[0].strip() if lines else ""
        fields = {
            "cgpa": r"CGPA[:\s]*([\d.]+)",
            "skills": r"Skills[:\s]*(.*)",
            "projects": r"Projects[:\s]*(\d+)",
            "workshops": r"Certifications[:\s]*(\d+)",
            "mini_projects": r"Mini Projects[:\s]*(\d+)",
            "communication_skills": r"Communication[:\s]*(\d+)",
            "tw_percentage": r"12th Percentage[:\s]*([\d.]+)",
            "te_percentage": r"10th Percentage[:\s]*([\d.]+)",
            "backlogs": r"Backlogs[:\s]*(\d+)"
        }
        for key, regex in fields.items():
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                data[key] = match.group(1)

        data["internship"] = "1" if "Internship Yes" in text else "0"
        data["hackathon"] = "1" if "Hackathon Yes" in text else "0"
    except Exception as e:
        print("Error extracting info:", e)
    return data

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return render_template('index.html', error="No file uploaded")
    file = request.files['resume']
    if file.filename == '':
        return render_template('index.html', error="No selected file")
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        extracted_text = extract_text(filepath)
        os.remove(filepath)
        extracted_data = extract_info(extracted_text)
        return render_template('index.html', extracted_data=extracted_data)
    except Exception as e:
        return render_template('index.html', error=f"Resume processing failed: {str(e)}")

@app.route('/predict')
def predict():
    try:
        cgpa = float(request.args.get('cgpa', 0))
        projects = int(request.args.get('projects', 0))
        workshops = int(request.args.get('certifications', 0))
        mini_projects = int(request.args.get('mini_projects', 0))
        skills = request.args.get('skills', '')
        communication_skills = float(request.args.get('communication', 0))
        internship = int(request.args.get('internship', 0))
        hackathon = int(request.args.get('hackathon', 0))
        tw_percentage = float(request.args.get('tw_percentage', 0))
        te_percentage = float(request.args.get('te_percentage', 0))
        backlogs = int(request.args.get('backlogs', 0))
        name = request.args.get('name', 'User')
        skill_count = skills.count(',') + 1 if skills else 0

        input_features = np.array([[cgpa, projects, workshops, mini_projects, skill_count,
                                    communication_skills, internship, hackathon,
                                    tw_percentage, te_percentage, backlogs]])

        probability = model.predict_proba(input_features)[0][1]
        placement_percentage = round(probability * 100, 2)
        placement_status = model.predict(input_features)[0]
        placement_status = '1' if str(placement_status) == '1' else '0'

        salary_input = np.append(input_features[0], int(placement_status)).reshape(1, -1)
        salary = model1.predict(salary_input)
        formatted_salary = "{:,.0f}".format(salary[0])

        if placement_status == '1':
            placement_message = f"Congratulations {name}!! You have high chances of getting placed!"
            salary_message = f"Expected Salary: INR {formatted_salary} per annum"
        else:
            placement_message = f"Sorry {name}, placement chances are low. Best wishes!"
            salary_message = "Improve your skills..."

        return render_template('out.html',
                               output=placement_message,
                               output2=salary_message,
                               placement_percentage=placement_percentage,
                               name=name,
                               cgpa=cgpa,
                               skills=skills,
                               projects=projects,
                               salary=formatted_salary)
    except Exception as e:
        return f"Prediction error: {str(e)}"

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        name = request.form.get('name')
        cgpa = request.form.get('cgpa')
        skills = request.form.get('skills')
        projects = request.form.get('projects')
        placement_percentage = request.form.get('placement_percentage')
        salary = request.form.get('salary')

        # ✅ Load local background image
        bg_image_path = os.path.join("static", "images", "back.jpg")
        if not os.path.exists(bg_image_path):
            return "Background image not found", 404
        bg_image = ImageReader(bg_image_path)

        # ✅ Generate QR code
        cert_link = "https://your-app.com/static/certificates/verification_certificate.png"
        qr_img = qrcode.make(cert_link)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_reader = ImageReader(qr_buffer)

        # ✅ Generate report
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        c.drawImage(bg_image, 0, 0, width=width, height=height)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(180, 790, "Student Placement Report")

        c.setFont("Helvetica", 12)
        y = 740
        for line in [
            f"Name: {name}",
            f"CGPA: {cgpa}",
            f"Skills: {skills}",
            f"Projects: {projects}",
            f"Placement Prediction: {placement_percentage}%",
            f"Expected Salary: INR {salary} per annum"
        ]:
            c.drawString(70, y, line)
            y -= 25

        c.drawImage(qr_reader, 440, 90, width=100, height=100)
        c.setFont("Helvetica", 8)
        c.drawString(445, 85, "Scan to verify certificate")
        c.showPage()
        c.save()
        buffer.seek(0)

        # ✅ Merge with XYZ.pdf
        xyz_path = os.path.join("static", "files", "XYZ.pdf")
        if not os.path.exists(xyz_path):
            return "XYZ.pdf not found", 404

        output = io.BytesIO()
        writer = PdfWriter()
        writer.append(PdfReader(buffer))
        writer.append(PdfReader(xyz_path))
        writer.write(output)
        output.seek(0)

        return send_file(output, as_attachment=True,
                         download_name="placement_report.pdf",
                         mimetype='application/pdf')

    except Exception as e:
        return f"PDF generation failed: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
