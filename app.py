import os
import io
from flask import Flask, render_template, request, send_file, after_this_request
import zipfile
from pdf2docx import Converter
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

def converti_word_in_pdf_ram(docx_bytes):
    # Legge il file Word direttamente dalla RAM
    doc = Document(io.BytesIO(docx_bytes))
    
    # Crea un contenitore in RAM per il PDF finale
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    
    for para in doc.paragraphs:
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, para.text)
        y -= 20
    c.save()
    
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return "Nessun file", 400
    file = request.files['file']
    azione = request.form.get('azione')
    
    if file.filename == '': return "Nessun file selezionato", 400
    
    # Leggiamo il file direttamente in memoria RAM
    file_bytes = file.read()
    nome_base, _ = os.path.splitext(file.filename)
    
    # 1. COMPRIMERE (ZIP) IN RAM
    if azione == 'comprimere':
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(file.filename, file_bytes)
        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name=f"{file.filename}.zip", as_attachment=True)
        
    # 2. PDF A WORD (Usa file temporaneo solo perché richiesto dalla libreria esterna)
    elif azione == 'PDF a Word':
        # Creiamo al volo dei percorsi temporanei veloci
        path_in = os.path.join("/tmp", file.filename)
        path_out = os.path.join("/tmp", nome_base + ".docx")
        
        with open(path_in, "wb") as f:
            f.write(file_bytes)
            
        cv = Converter(path_in)
        cv.convert(path_out, start=0, end=None)
        cv.close()
        
        return_data = io.BytesIO()
        with open(path_out, "rb") as f:
            return_data.write(f.read())
        return_data.seek(0)
        
        # Pulizia immediata dei file temporanei
        try:
            os.remove(path_in)
            os.remove(path_out)
        except:
            pass
            
        return send_file(return_data, download_name=f"{nome_base}.docx", as_attachment=True)
        
    # 3. WORD A PDF IN RAM
    elif azione == 'Word a PDF':
        pdf_buffer = converti_word_in_pdf_ram(file_bytes)
        return send_file(pdf_buffer, download_name=f"{nome_base}.pdf", as_attachment=True)
        
    return "Azione non valida", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
