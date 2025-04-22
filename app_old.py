import io
import os
import pandas as pd
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/process', methods=['POST'])
def process():
    try:
        file = request.files['file']
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        options = request.form.getlist('options[]')
        output_format = request.form.get('format', 'csv')

        # Read different file types
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext == '.tsv':
            df = pd.read_csv(file, sep='\t')
        elif ext == '.json':
            df = pd.read_json(file)
        elif ext == '.xlsx':
            df = pd.read_excel(file)
        else:
            return jsonify({'error': f"Unsupported file type: {ext}"}), 400

        # Basic processing
        if 'deduplication' in options:
            df.drop_duplicates(inplace=True)
        if 'html' in options:
            df['text'] = df['text'].str.replace(r'<[^>]+>', '', regex=True)
        if 'noise' in options:
            df['text'] = df['text'].str.replace(r'[^\w\s]', '', regex=True)

        # Prepare file for download
        output = io.StringIO()
        filename = f'processed.{output_format}'

        if output_format == 'json':
            df.to_json(output, orient='records', force_ascii=False)
            mimetype = 'application/json'
        elif output_format == 'tsv':
            df.to_csv(output, sep='\t', index=False)
            mimetype = 'text/tab-separated-values'
        else:  # default: CSV
            df.to_csv(output, index=False)
            mimetype = 'text/csv'

        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()),
                         mimetype=mimetype,
                         as_attachment=True,
                         download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

