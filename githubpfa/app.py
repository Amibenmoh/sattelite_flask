from flask import Flask, render_template, request, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
import numpy as np
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Charger le modèle (assure-toi que c'est bien le bon chemin)
MODEL_PATH = 'modelResnet50.h5'  
model = load_model(MODEL_PATH)

# Classes dans l'ordre exact de ton flow_from_directory
class_names_en = ['AnnualCrop', 'Forest', 'HerbaceousVegetation', 'Highway', 'Industrial', 'Pasture', 'PermanentCrop', 'Residential', 'River', 'SeaLake']  
class_names_fr = ['Cultures annuelles', 'Forêt', 'Végétation herbacée', 'Autoroute', 'Industriel', 'Pâturage', 'Cultures pérennes', 'Résidentiel', 'Rivière', 'Mer/Lac']

INPUT_SIZE = (128, 128)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return render_template('index.html', error="Aucun fichier reçu.")
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="Fichier non choisi.")
    
    # Sauvegarder le fichier uploadé
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # Chargement + prétraitement
    img = image.load_img(save_path, target_size=INPUT_SIZE)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)  # Important: même prétraitement qu'à l'entraînement

    # Prédiction
    preds = model.predict(img_array)
    pred_idx = int(np.argmax(preds, axis=1)[0])
    confidence = float(np.max(preds)) * 100.0

    # Nom en français et anglais
    predicted_class_fr = class_names_fr[pred_idx]
    predicted_class_en = class_names_en[pred_idx]

    # URL pour affichage
    img_url = url_for('static', filename=f'uploads/{filename}')

    return render_template('index.html',
                           prediction=predicted_class_fr,
                           confidence=round(confidence, 1),
                           image_url=img_url,
                           class_en=predicted_class_en)

if __name__ == '__main__':
    app.run(debug=True)
