import io
import os
import re
import json
import pandas as pd
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from nltk.tokenize import word_tokenize
from unidecode import unidecode

app = Flask(__name__)
CORS(app)


# Util: identify best text column if not 'text'
def get_text_column(df):
    for col in df.columns:
        if 'text' in col.lower():
            return col
    return df.columns[0]  # fallback


@app.route('/process', methods=['POST'])
def process():
    try:
        file = request.files['file']
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        options = request.form.getlist('options[]')
        output_format = request.form.get('format', 'csv')

        # Load dataset based on format
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext == '.tsv':
            df = pd.read_csv(file, sep='\t')
        elif ext == '.json':
            df = pd.read_json(file)
        elif ext == '.xlsx':
            df = pd.read_excel(file)
        elif ext == '.txt':
            df = pd.DataFrame({'text': file.read().decode('utf-8').splitlines()})
        else:
            return jsonify({'error': f"Unsupported file type: {ext}"}), 400

        # Ensure we have a text column
        text_col = get_text_column(df)
        df[text_col] = df[text_col].astype(str)

        # Processing options
        if 'deduplication' in options:
            df.drop_duplicates(subset=[text_col], inplace=True)

        if 'html' in options:
            df[text_col] = df[text_col].str.replace(r'<[^>]+>', '', regex=True)

        if 'noise' in options:
            df[text_col] = df[text_col].str.replace(r'[^\w\s]', '', regex=True)

        if 'normalization' in options:
            df[text_col] = df[text_col].str.normalize('NFKD')

        if 'tokenization' in options:
            df[text_col] = df[text_col].apply(lambda x: ' '.join(word_tokenize(x)))

        if 'blocklist' in options:
            blocklist = ['http', 'www', '.com', '.org']
            df = df[~df[text_col].str.contains('|'.join(blocklist), na=False)]

        if 'language' in options:
            # simple Arabic detection (for example purpose)
            df = df[df[text_col].str.contains(r'[\u0600-\u06FF]', regex=True)]

        if 'diacritics' in options:
            df[text_col] = df[text_col].str.replace(r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]', '', regex=True)

        # Prepare output
        filename = f"processed.{output_format}"
        if output_format == 'json':
            output = io.StringIO()
            df.to_json(output, orient='records', force_ascii=False)
            mimetype = 'application/json'
        elif output_format == 'tsv':
            output = io.StringIO()
            df.to_csv(output, sep='\t', index=False)
            mimetype = 'text/tab-separated-values'
        elif output_format == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
        else:  # CSV default
            output = io.StringIO()
            df.to_csv(output, index=False)
            mimetype = 'text/csv'

        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype=mimetype, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
