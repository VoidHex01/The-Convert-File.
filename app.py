import os
from flask import Flask, render_template, request, send_file
import zipfile

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
    
    if azione == 'comprimere':
        path_finale = path_originale + ".zip"
        with zipfile.ZipFile(path_finale, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(path_originale, file.filename)
        return send_file(path_finale, as_attachment=True)
        
    elif azione == 'PDF a Word' or azione == 'Word a PDF':
        return f"File '{file.filename}' ricevuto correttamente sul server! Le conversioni PDF/Word richiedono software di sistema non presente sul piano gratuito. Funzione di compressione ZIP attiva!"
        
    return "Azione non valida", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
