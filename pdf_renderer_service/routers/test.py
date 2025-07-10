from collections import defaultdict
import json
import pymupdf

def pdf_render(json_data, doc_url):
    pagewise_data = defaultdict(list)

    texts = json_data.get("docling", {}).get("texts", [])
    for text_item in texts:
        translated = text_item.get("translated_text", "")
        for prov in text_item.get("prov", []):
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            if page_no is not None and bbox:
                pagewise_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })
    data = dict(pagewise_data)

    doc = pymupdf.open(doc_url)
    for page in doc:
        print(f"{page.number}\n") 
        blocks = page.get_text("blocks")  # list of tuples: (x0, y0, x1, y1, "text", block_no, block_type)
        for block in blocks:
            rect = block[:4]  # (x0, y0, x1, y1)

            page.add_redact_annot(rect)

        page.apply_redactions()
        page.clean_contents()

        data_lst = data[page.number + 1]
        for trans_data in data_lst:
            trans_text = trans_data["translated_text"]
            bbox = trans_data['bbox']
            coords = (bbox["l"], (page.rect[3]- bbox["t"]), bbox["r"], page.rect[3]- bbox["b"])
            print(f"Text: {trans_text}")
            print(f"Bbox: {coords}")

            page.draw_rect(coords, color=(1, 0, 1))
            status = page.insert_htmlbox(coords, trans_text) # fontsize=font_size, fontname=font_name, color=text_color, align=0
            print(f"Status: {status}")

    doc.save("./output.pdf", garbage=3, deflate=True)

    # Save as JSON file
    with open("./test.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with open("./sample-files/output.json", "r", encoding="utf-8") as f:
    data = json.load(f)
pdf_render(data, "./sample-files/o_level_paper_2.pdf")
