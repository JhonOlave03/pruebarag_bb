from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
import os

def generate_project_pdf(project_path, output_file="project.pdf"):
    doc = SimpleDocTemplate(output_file)
    styles = getSampleStyleSheet()
    content = []

    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py") or file.endswith(".md"):
                file_path = os.path.join(root, file)

                # Título del archivo
                content.append(Paragraph(f"<b>{file_path}</b>", styles["Heading3"]))
                content.append(Spacer(1, 10))

                # Leer código
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                except:
                    code = "Error reading file"

                # Agregar código formateado
                content.append(Preformatted(code, styles["Code"]))
                content.append(Spacer(1, 20))

    doc.build(content)
    print(f"PDF generado: {output_file}")

# USO
generate_project_pdf(r"C:\Users\jhono\OneDrive\Documents\learning_py\pruebaRag_bb")

