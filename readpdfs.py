import pdf2image
import pytesseract


def get_info(page):
    for j in range(len(page)):
        indicators = ["v. ", "S. ", " / ", " ; "]
        indicators = [page[j].count(indicator) for indicator in indicators]
        if sum(indicators) > 1:
            info = page[j]
            page.pop(j)
            break
    return info, page


def remove_artifacts(page):
    # Remove unnecessary elements
    for word in ["Pressedokumentation", "Bergedorfer Zeitung",
                 "Hamburger Abendblatt", "Hamburger", "Hamburger:",
                 "Hamburger’", "Abendblatt", "~Abendblatt",
                 "cru", "rue?)", "Fortsetzung...", "..Fortsetzung"]:
        if word in page:
            page.remove(word)
    j = 0
    while not (j == len(page)):
        if ("[" in page[j]) or ("]" in page[j]) or ("Rathaus-Medienspiegel" in page[j]) or ("Seite " in page[j]):
            page.pop(j)
        else:
            j += 1
    return page


def usable_text(page):
    page = [p.replace("-\n", "").replace("\n", " ").replace("- ", "")
            for p in page]
    j = 1
    while not (j == len(page)):
        # if first item is lower case, join with previous
        if page[j][0].islower():
            page[j-1] += " "+page[j]
            page.pop(j)
        else:
            j += 1
    return page


def get_list_of_sentences(page):
    text = " ".join(page)
    text = text.split(". ")
    text = [t+"." for t in text]
    return text


def find_buzzwords(articles, buzzwords):
    relevant = {}
    for k in articles.keys():
        text = " ".join(articles[k]["Text"])
        if any(buzzword.lower() in text.lower() for buzzword in buzzwords):
            relevant[k] = articles[k]
    return relevant


def get_post(articles):
    fdp = find_buzzwords(articles, ["fdp"])
    bildung = find_buzzwords(articles, ["schul", "bildung"])
    print("*FDP*")
    for k in fdp.keys():
        print(f"S. {fdp[k]['Seite']} {k.split(' v.')[0]}: _{fdp[k]['Text'][0]}_")
    print("*Bildung*")
    for k in bildung.keys():
        print(f"S. {bildung[k]['Seite']} {k.split(' v.')[0]}: _{bildung[k]['Text'][0]}_")


# Read PDF
images = pdf2image.convert_from_path("Frühausgabe.pdf")

articles = {}
info = None
for i, image in enumerate(images, start=1):
    print(f"Processing page {i}")
    if (i == 1):
        continue
    # Convert image to text
    page = pytesseract.image_to_string(image, lang="deu")
    # Split into useful pieces
    page = page.split("\n\n")
    # Extract topic
    topic = page[0]
    page.pop(0)
    # Remove unnecessary elements
    page = remove_artifacts(page)
    if "Fortsetzung" in topic:
        page = usable_text(page)
        articles[info]["Text"] += page
    else:
        info, page = get_info(page)
        info = info.replace("\n", " ")
        info = usable_text([info])[0]
        page = usable_text(page)
        page = get_list_of_sentences(page)
        articles[info] = {"Topic": topic, "Seite": i, "Text": page}

get_post(articles)
