import requests
import pymupdf
import json
import time

system_prompt = "Translate the following from english to chinese"

#################### Qwen setup ####################
LLM_URL = "http://192.168.1.108:80/v1/chat/completions" #chat/completions

TOKEN = "token-abc123"

def translate(prompt):
    r = requests.post(
        LLM_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        },
        json={
            "model": "qwen2.5",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    return r.json()["choices"][0]["message"]["content"]

#################### PDF Editor ####################
start_time = time.time()

with open('./result.json', 'r') as f:
    data = json.load(f)

doc = pymupdf.open("/home/ubuntu/Desktop/OmniPDF/sample-files/o_level_paper_2.pdf")
for page in doc:
    print(f"{page.number}\n") 
    blocks = page.get_text("blocks")  # list of tuples: (x0, y0, x1, y1, "text", block_no, block_type)
    for block in blocks:
        rect = block[:4]  # (x0, y0, x1, y1)
        text = block[4]

        page.add_redact_annot(rect)

    page.apply_redactions()
    page.clean_contents()
    try:
        page_lst = data[page.number + 1]
        for i in page_lst:
            new_text = i["text"]
            bbox = i["prov"][0]['bbox']
            coords = (bbox["l"], (page.rect[3]- bbox["t"]), bbox["r"], page.rect[3]- bbox["b"])
            translation = translate(new_text)
            print(f"Text: {new_text}")
            print(f"Translation: {translation}")
            print(f"Bbox: {coords}")

            page.draw_rect(coords, color=(1, 0, 1))
            status = page.insert_htmlbox(coords, translation) # fontsize=font_size, fontname=font_name, color=text_color, align=0
            print(f"Status: {status}")
    except KeyError:
        pass
doc.save("./output_white_boxed.pdf", garbage=3, deflate=True)

print(f"Translation complete in {time.time() - start_time}")