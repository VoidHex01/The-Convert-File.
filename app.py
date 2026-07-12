import os
import json
from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import zipfile
from pdf2docx import Converter
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def elimina_file_sicuro(*file_paths):
    @after_this_request
    def remove_file(response):
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Errore rimozione: {e}")
        return response

# NUOVA FUNZIONE: Estrae il testo da un file Word per mandarlo all'editor del browser
@app.route('/leggi-word', methods=['POST'])
def leggi_word():
    if 'file' not in request.files: return jsonify({"error": "Nessun file"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "Nessun file selezionato"}), 400
    
    path_temp = os.path.join(UPLOAD_FOLDER, "temp_" + file.filename)
    file.save(path_temp)
    
    try:
        doc = Document(path_temp)
        testo_paragrafi = [p.text for p in doc.paragraphs]
        os.remove(path_temp)
        return jsonify({"filename": file.filename, "paragrafi": testo_paragrafi})
    except Exception as e:
        if os.path.exists(path_temp): os.remove(path_temp)
        return jsonify({"error": str(e)}), 500

# NUOVA FUNZIONE: Genera un PDF partendo dal testo modificato nell'editor web
@app.route('/converti-testo-editor', methods=['POST'])
def converti_testo_editor():
    dati = request.json
    filename = dati.get('filename', 'documento.docx')
    paragrafi = dati.get('paragrafi', [])
    nome_base, _ = os.path.splitext(filename)
    
    path_finale = os.path.join(UPLOAD_FOLDER, nome_base + "_modificato.pdf")
    
    c = canvas.Canvas(path_finale, pagesize=letter)
    width, height = letter
    y = height - 40
    
    for testo in paragrafi:
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, testo)
        y -= 20
    c.save()
    
    elimina_file_sicuro(path_finale)
    return send_file(path_finale, as_attachment=True, download_name=f"{nome_base}_modificato.pdf")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    azione = request.form.get('azione')
    
    # GESTIONE MULTI-FILE PER LO ZIP (FEATURE 1)
    if azione == 'comprimere':
        files = request.files.getlist('file')
        if not files or files[0].filename == '': return "Nessun file selezionato", 400
        
        # Se è un solo file, fa lo zip singolo
        if len(files) == 1:
            file = files[0]
            path_orig = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path_orig)
            path_zip = path_orig + ".zip"
            with zipfile.ZipFile(path_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(path_orig, file.filename)
            elimina_file_sicuro(path_orig, path_zip)
            return send_file(path_zip, as_attachment=True, download_name=f"{file.filename}.zip")
        
        # Se sono file multipli, li unisce in un unico archivio collettivo
        else:
            path_zip_multiplo = os.path.join(UPLOAD_FOLDER, "archivio_compresso.zip")
            file_salvati = []
            with zipfile.ZipFile(path_zip_multiplo, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    if file.filename != '':
                        p = os.path.join(UPLOAD_FOLDER, file.filename)
                        file.save(p)
                        file_salvati.append(p)
                        zipf.write(p, file.filename)
            
            elimina_file_sicuro(path_zip_multiplo, *file_salvati)
            return send_file(path_zip_multiplo, as_attachment=True, download_name="archivio_compresso.zip")

    # GESTIONE PDF A WORD STANDARD
    elif azione == 'PDF a Word':
        if 'file' not in request.files: return "Nessun file", 400
        file = request.files['file']
        path_originale = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path_originale)
        nome_base, _ = os.path.splitext(file.filename)
        path_finale = os.path.join(UPLOAD_FOLDER, nome_base + ".docx")
        
        cv = Converter(path_originale)
        cv.convert(path_finale, start=0, end=None)
        cv.close()
        
        elimina_file_sicuro(path_originale, path_finale)
        return send_file(path_finale, as_attachment=True)
        
    return "Azione non valida", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
