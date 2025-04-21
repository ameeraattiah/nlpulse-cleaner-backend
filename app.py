from flask import Flask, request, jsonify
import pandas as pd
import io
import os
from flask_cors import CORS  # ✅ Add this line

app = Flask(__name__)
CORS(app)  # ✅ Add this line


@app.route('/clean', methods=['POST'])
def clean_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    options = request.form.getlist('options[]')

    df = pd.read_csv(file)

    if 'deduplication' in options:
        df = df.drop_duplicates()

    if 'normalization' in options:
        df.columns = [col.strip().lower() for col in df.columns]

    if 'html-cleaning' in options:
        df = df.applymap(lambda x: x.replace('<br>', ' ').replace('<div>', '') if isinstance(x, str) else x)

    # Add more processing steps...

    return jsonify({
        "rows": df.shape[0],
        "columns": df.columns.tolist()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
