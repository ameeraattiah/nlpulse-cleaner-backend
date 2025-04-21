from flask import Flask, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

def clean_text(text):
    text = re.sub(r'<.*?>', '', text)  # remove HTML
    text = re.sub(r'[^ء-يa-zA-Z0-9\s]', '', text)  # keep Arabic, English, numbers
    return text.strip()

@app.route('/clean', methods=['POST'])
def clean():
    file = request.files['file']
    selected = request.form.getlist('options[]')
    df = pd.read_csv(file)

    if 'Deduplication' in selected:
        df.drop_duplicates(subset='text', inplace=True)

    if 'HTML Cleaning' in selected or 'Noise Removal' in selected:
        df['text'] = df['text'].apply(clean_text)

    response = {
        'rows': len(df),
        'columns': list(df.columns)
    }

    return jsonify(response)
