from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)  # allow all origins

@app.route('/process', methods=['POST'])
def process():
    try:
        # Get file and options
        file = request.files['file']
        options = request.form.getlist('options[]')
        df = pd.read_csv(file)

        # Apply processing
        if 'Deduplication' in options:
            df.drop_duplicates(inplace=True)
        if 'HTML Cleaning' in options:
            df['text'] = df['text'].str.replace(r'<[^>]*>', '', regex=True)
        if 'Noise Removal' in options:
            df['text'] = df['text'].str.replace(r'[^؀-ۿ\s]', '', regex=True)

        # Save to buffer
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(io.BytesIO(output.getvalue().encode()),
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name='processed.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=10000)
