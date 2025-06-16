from docling.document_converter import DocumentConverter
import json

source = r"/home/ubuntu/Desktop/OmniPDF/sample-files/o_level_paper_2.pdf"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
data = result.document.export_to_dict()
print(dict(data))  # output: "## Docling Technical Report[...]"

with open('result.json', 'w') as fp:
    json.dump(data, fp)
