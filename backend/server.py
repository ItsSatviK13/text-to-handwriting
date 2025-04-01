import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.ttLib import newTable

# Flask setup
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'generated_fonts/'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    img = Image.open(image_path).convert('L')
    threshold = 128
    img = img.point(lambda p: p > threshold and 255)
    return img

def segment_characters(image):
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    characters = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 5 and h > 10:
            char_image = image.crop((x, y, x + w, y + h))
            characters.append(char_image)
    
    return characters

def create_ttf_from_images(images, font_name):
    font = TTFont()
    cmap = newTable('cmap')
    cmap.table = {}

    font['head'] = newTable('head')
    font['hhea'] = newTable('hhea')
    font['maxp'] = newTable('maxp')
    font['name'] = newTable('name')
    font['OS/2'] = newTable('OS/2')

    font['head'].unitsPerEm = 1000
    font['hhea'].ascender = 800
    font['hhea'].descender = -200
    font['maxp'].numGlyphs = len(images)

    kern = newTable('kern')
    kern.table = {0: {1: -50}}
    font['kern'] = kern

    glyph_index = 32
    for image in images:
        image = image.convert('1')
        bitmap = image.getdata()
        glyph = font.createGlyph(glyph_index)
        glyph.importOutlines(bitmap)
        cmap.table[glyph_index] = glyph_index
        glyph_index += 1

    font.save(f'{OUTPUT_FOLDER}/{font_name}.ttf')

@app.route('/generate-font', methods=['POST'])
def generate_font():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename):
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        processed_img = preprocess_image(file_path)
        characters = segment_characters(processed_img)
        
        font_name = 'CustomFont'
        create_ttf_from_images(characters, font_name)
        
        font_url = f'/generated_fonts/{font_name}.ttf'
        return jsonify({
            'fontName': font_name,
            'fontUrl': font_url
        })
    
    return jsonify({'error': 'Invalid file format. Only PNG, JPG, and JPEG allowed.'}), 400

@app.route('/generated_fonts/<filename>')
def download_font(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# FastAPI setup to wrap Flask
fastapi_app = FastAPI()

# Use FastAPI with Flask (this allows us to run Flask within FastAPI for integration)
fastapi_app.mount("/", WSGIMiddleware(app))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
