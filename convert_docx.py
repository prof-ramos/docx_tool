import os
import sys
import glob
from docling.document_converter import DocumentConverter

def convert_docx_to_md(file_path, output_dir):
    try:
        print(f"Converting {file_path}...")
        converter = DocumentConverter()
        result = converter.convert(file_path)

        base_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_dir, f"{file_name_without_ext}.md")

        result.document.export_to_markdown()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.document.export_to_markdown())

        print(f"Conversion successful! Output saved to: {output_file}")
    except Exception as e:
        print(f"Error converting file: {e}")

if __name__ == "__main__":
    input_path = "Input"
    output_path = "Output"

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if os.path.isdir(input_path):
        print(f"Processing directory: {input_path}")
        print(f"Output directory: {output_path}")
        docx_files = glob.glob(os.path.join(input_path, "*.docx"))
        if not docx_files:
            print(f"No .docx files found in {input_path}.")

        for file_path in docx_files:
            convert_docx_to_md(file_path, output_path)
    elif os.path.isfile(input_path):
        convert_docx_to_md(input_path, output_path)
    else:
        print(f"Error: Input path '{input_path}' not found.")
        sys.exit(1)
