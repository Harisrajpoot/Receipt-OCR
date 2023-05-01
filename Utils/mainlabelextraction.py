import pytesseract
import cv2
import os
import re
import json
from spellchecker import SpellChecker

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

path = 'Victra Dataset\\Image'

for filename in os.listdir(path):
    # Read and resize the image
    img_path = os.path.join(path, filename)
    image = cv2.imread(img_path)
    resized_image = cv2.resize(image, (750, 938))

    # Save the resized image, replacing the original image
    cv2.imwrite(img_path, resized_image)
    print({filename}, 'is resized')

    # Extract information from the resized image
    text = pytesseract.image_to_string(resized_image)
    data = pytesseract.image_to_data(resized_image, output_type=pytesseract.Output.DICT)

    store_name_box = []
    keyword = 'VICTRA'
    spell = SpellChecker()
    candidate_names = ['Victra', 'victra', 'VICTRA']
    if keyword in candidate_names:
        pass
    else:
        corrected_keyword = spell.correction(keyword)
        if corrected_keyword in candidate_names:
            keyword = corrected_keyword

    found_keyword = False
    for i, word in enumerate(data['text']):
        if word.lower() == keyword.lower():
            # Get the box coordinates for the word
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            store_name_box = [x, y, x+w, y+h]
            print("Store Name:", keyword)
            found_keyword = True
            break

    if not found_keyword:
        print("No match found for Store Name.")
        store_name_box = []
        keyword = ""

    date_box = []
    date = re.search(r'\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}', text)
    if date:
        groupD = date.group(0)
        for i in range(len(data['level'])):
            if data['text'][i] in groupD and data['level'][i] == 5:
                date_box = ([data['left'][i], data['top'][i], data['width'][i], data['height'][i]])
                break
    else:
        groupD = ""

    invoice_box = []
    invoice = re.search(r'Invoice\s*:\s*[A-Z0-9]+', text)
    if invoice:
        groupI = invoice.group(0)
        words = []
        for i, word in enumerate(data['text']):
            if word in groupI:
                words.append({
                    'text': word,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                })

        if words:
            invoice_box = [
                min([word['left'] for word in words]),
                min([word['top'] for word in words]),
                max([word['left'] + word['width'] for word in words]),
                max([word['top'] + word['height'] for word in words])
            ]
    else:
        groupI = ""

    store_branch_box = []
    groupB = None
    store_branch = re.search(r'(?P<address>\d{4}\s\w+\s\w+)', text)
    if store_branch:
        groupB = store_branch.group(0)
        address_lines = groupB.split('\n')
        for address_line in address_lines:
            for i in range(len(data['level'])):
                if data['text'][i] in address_line and data['level'][i] == 5:
                    store_branch_box = ([data['left'][i], data['top'][i], data['width'][i], data['height'][i]])

                    break
                else:
                    groupB = ""
                    store_branch_box = []

    form = [
        {"box": store_name_box, "text": keyword, "label": "Store Name", "id": 0},
        {"box": date_box, "text": groupD, "label": "Date", "id": 2},
        {"box": invoice_box, "text": groupI, "label": "Receipt Number", "id": 1},
        {"box": store_branch_box, "text": groupB, "label": "Store Branch", "id": 3}
    ]

    # Create JSON object
    data = {"form": form}

    # Write JSON object to file
    output_filename = os.path.splitext(filename)[0] + '.json'
    outpath = 'Victra Dataset\\Json'
    output_path = os.path.join(outpath, output_filename)
    with open(output_path, 'w') as f:
        json.dump(data, f)
