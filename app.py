import streamlit as st
import os
import glob
import shutil
from docx import Document
from docling.document_converter import DocumentConverter
import unicodedata
import re

# Configuração da página
st.set_page_config(page_title="DOCX Processor Tool", page_icon="📄", layout="wide")

st.title("🛠️ DOCX Processor Tool")
st.markdown("---")

# Sidebar para configurações
st.sidebar.header("Configurações")
input_dir = st.sidebar.text_input("Diretório de Entrada", value="Administrativo")
output_dir = st.sidebar.text_input("Diretório de Saída", value="Output")

rename_option = st.sidebar.checkbox("Renomear arquivos (snake_case)")
remove_colors_option = st.sidebar.checkbox("Remover cores")
convert_md_option = st.sidebar.checkbox("Converter para Markdown")

if st.sidebar.button("Processar Arquivos", type="primary"):
    if not os.path.exists(input_dir):
        st.error(f"Diretório de entrada '{input_dir}' não encontrado!")
        st.stop()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Listar arquivos DOCX e RTF
    docx_files = glob.glob(os.path.join(input_dir, "*.docx")) + glob.glob(os.path.join(input_dir, "*.rtf"))
    if not docx_files:
        st.warning("Nenhum arquivo .docx ou .rtf encontrado no diretório de entrada.")
        st.stop()

    st.info(f"Encontrados {len(docx_files)} arquivos para processar.")

    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []

    for i, file_path in enumerate(docx_files):
        filename = os.path.basename(file_path)
        status_text.text(f"Processando: {filename}...")

        try:
            # 1. Renomear (gerar novo nome)
            if rename_option:
                name, ext = os.path.splitext(filename)
                new_name = to_snake_case(name)
                new_filename = f"{new_name}{ext}"
            else:
                new_filename = filename

            # Copiar para output com novo nome se rename
            temp_output_path = os.path.join(output_dir, new_filename)
            shutil.copy2(file_path, temp_output_path)

            # 2. Remover cores (apenas para DOCX)
            if remove_colors_option and temp_output_path.lower().endswith('.docx'):
                clean_path = temp_output_path.replace('.docx', '_clean.docx')
                remove_colors(temp_output_path, clean_path)
                temp_output_path = clean_path  # Usar versão limpa para conversão

            # 3. Converter para MD
            if convert_md_option:
                convert_docx_to_md(temp_output_path, output_dir)

            # Listar arquivos de saída
            output_files = [os.path.basename(temp_output_path)]
            if convert_md_option:
                base_name_no_ext = os.path.splitext(os.path.basename(temp_output_path))[0]
                md_file = f"{base_name_no_ext}.md"
                output_files.append(md_file)
            results.append(f"✅ {filename} -> {', '.join(output_files)}")
        except Exception as e:
            results.append(f"❌ {filename}: {str(e)}")

        progress_bar.progress((i + 1) / len(docx_files))

    # Resultados
    st.success("Processamento concluído!")
    for result in results:
        st.write(result)

# Funções auxiliares
@st.cache_data
def to_snake_case(name):
    """Converte nome para snake_case normalizado."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def remove_colors(input_path, output_path):
    """Remove cores de um arquivo DOCX."""
    doc = Document(input_path)

    def clear_shading(element):
        if element._element.xpath('.//w:shd'):
            for shd in element._element.xpath('.//w:shd'):
                shd.getparent().remove(shd)

    # Parágrafos
    for paragraph in doc.paragraphs:
        clear_shading(paragraph)
        for run in paragraph.runs:
            if run.font.color.rgb:
                run.font.color.rgb = None
            if run.font.highlight_color:
                run.font.highlight_color = None
            rPr = run._element.get_or_add_rPr()
            if rPr.xpath('./w:highlight'):
                for highlight in rPr.xpath('./w:highlight'):
                    highlight.getparent().remove(highlight)
            if rPr.xpath('./w:shd'):
                for shd in rPr.xpath('./w:shd'):
                    shd.getparent().remove(shd)

    # Tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                clear_shading(cell)
                for paragraph in cell.paragraphs:
                    clear_shading(paragraph)
                    for run in paragraph.runs:
                        if run.font.color.rgb:
                            run.font.color.rgb = None
                        if run.font.highlight_color:
                            run.font.highlight_color = None
                        rPr = run._element.get_or_add_rPr()
                        if rPr.xpath('./w:highlight'):
                            for highlight in rPr.xpath('./w:highlight'):
                                highlight.getparent().remove(highlight)
                        if rPr.xpath('./w:shd'):
                            for shd in rPr.xpath('./w:shd'):
                                shd.getparent().remove(shd)

    doc.save(output_path)

def convert_docx_to_md(file_path, output_dir):
    """Converte DOCX/RTF para MD."""
    converter = DocumentConverter()
    result = converter.convert(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.document.export_to_markdown())

# Footer
st.markdown("---")
st.markdown("Desenvolvido com ❤️ usando Streamlit para processar documentos jurídicos.")
