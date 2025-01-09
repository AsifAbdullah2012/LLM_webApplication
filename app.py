from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
# imports for colpali
import torch
from PIL import Image
from colpali_engine.models import ColPali, ColPaliProcessor


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_dynamic_folder(file_path):
    # Extract the file name without extension
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    # Create a folder with the file name
    folder_path = os.path.join(os.getcwd(), file_name)
    os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist

    return folder_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_documents():
    question = request.form.get('question')
    files = request.files.getlist('files')
    results = []

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # TODO convert pdf to images
        output_folder = create_dynamic_folder(file_path)
        os.makedirs(output_folder, exist_ok=True)


        images = convert_from_path(file_path, dpi=300)


        image_files = []
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f"page_{i + 1}.png")
            image.save(image_path, "PNG")
            image_files.append(image_path)

        print(f"PDF converted to images and saved in {output_folder}")

        # TODO use the colpali model 

        model_name = "vidore/colpali-v1.2"
        model = ColPali.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="mps"  # Use "mps" if on Apple Silicon
        ).eval()

        processor = ColPaliProcessor.from_pretrained(model_name)

        # Dynamically load all images in the directory
        images = []
        for file_name in sorted(os.listdir(output_folder)):  # Sort for consistent order
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):  # Filter image files
                file_path = os.path.join(output_folder, file_name)
                images.append(Image.open(file_path))


        # Process dynamically loaded images and queries
        batch_images = processor.process_images(images).to(model.device)
        batch_queries = processor.process_queries(question).to(model.device)

        with torch.no_grad():
            image_embeddings = model(**batch_images)
            query_embeddings = model(**batch_queries)

        scores = processor.score_multi_vector(query_embeddings, image_embeddings)



        # Read and process the document
        reader = PdfReader(file_path)
        pages = [page.extract_text() for page in reader.pages]

        # Find the most relevant page (dummy logic)
        relevant_page = pages[0] if pages else "No content found in the document."
        results.append(f"Relevant Page from {filename}:\n\n{relevant_page[:500]}...")

    return jsonify(scores)

if __name__ == "__main__":
    app.run(debug=True)
