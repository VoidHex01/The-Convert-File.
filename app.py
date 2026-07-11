import os
from flask import Flask, render_template, request, send_file
import zipfile
from pdf2docx import Converter
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def converti_word_in_pdf(docx_path, pdf_path):
    # Legge il file Word ed estrae il testo riga per riga
    doc = Document(docx_path)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 40  # Margine superiore
    
    for para in doc.paragraphs:
        if y < 40:  # Se la pagina è piena, creane una nuova
            c.showPage()
            y = height - 40
        c.drawString(40, y, para.text)
        y -= 20  # Spazio tra le righe
    c.save()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return "Nessun file", 400
    file = request.files['file']
    azione = request.form.get('azione')
    
    if file.filename == '': return "Nessun file selezionato", 400
    
    path_originale = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path_originale)
    
    # 1. FUNZIONE COMPRIMERE (ZIP)
    if azione == 'comprimere':
        path_finale = path_originale + ".zip"
        with zipfile.ZipFile(path_finale, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(path_originale, file.filename)
        return send_file(path_finale, as_attachment=True)
        
    # 2. FUNZIONE PDF A WORD
    elif azione == 'PDF a Word':
        nome_base, _ = os.path.splitext(file.filename)
        path_finale = os.path.join(UPLOAD_FOLDER, nome_base + ".docx")
        
        cv = Converter(path_originale)
        cv.convert(path_finale, start=0, end=None)
        cv.close()
        
        return send_file(path_finale, as_attachment=True)
        
    # 3. FUNZIONE WORD A PDF
    elif azione == 'Word a PDF':
        nome_base, _ = os.path.splitext(file.filename)
        path_finale = os.path.join(UPLOAD_FOLDER, nome_base + ".pdf")
        
        converti_word_in_pdf(path_originale, path_finale)
        
        return send_file(path_finale, as_attachment=True)
        
    return "Azione non valida", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
