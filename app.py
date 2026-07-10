import os
from flask import Flask, render_template, request, send_file
from pdf2docx import Converter
from docx2pdf import convert
import zipfile
import pythoncom  # <--- AGGIUNTO QUESTO PER SBLOCCARE WINDOWS

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return "Nessun file", 400
    file = request.files['file']
    azione = request.form.get('azione')
    
    path_originale = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path_originale)
    
    path_finale = ""
    
    if azione == 'PDF a Word':
        path_finale = path_originale.replace('.pdf', '.docx')
        cv = Converter(path_originale)
        cv.convert(path_finale)
        cv.close()
    elif azione == 'Word a PDF':
        path_finale = path_originale.replace('.docx', '.pdf')
        pythoncom.CoInitialize()  # <--- AGGIUNTO QUESTO: Sblocca la conversione Word
        convert(path_originale, path_finale)
    elif azione == 'comprimere':
        path_finale = path_originale + ".zip"
        with zipfile.ZipFile(path_finale, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(path_originale, file.filename)
            
    return send_file(path_finale, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
