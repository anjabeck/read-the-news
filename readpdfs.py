import pdf2image
import pytesseract
import pandas as pd
import numpy as np


def find_buzzwords(articles, buzzwords):
    relevant = {}
    for k in articles.keys():
        if any(buzzword.lower() in articles[k]["Text"].lower() for buzzword in buzzwords):
            relevant[k] = articles[k]
    return relevant


def get_post(articles):
    fdp = find_buzzwords(articles, ["fdp"])
    bildung = find_buzzwords(articles, ["schul", "bildung"])
    print("*FDP*")
    for k in fdp.keys():
        print(f"S. {fdp[k]['Seite']} {fdp[k]['Info'].split(' v.')[0]}: _{fdp[k]['Titel']}_")
    print("*Bildung*")
    for k in bildung.keys():
        print(f"S. {bildung[k]['Seite']} {bildung[k]['Info'].split(' v.')[0]}: _{bildung[k]['Titel']}_")


def data_frame_sentences(page, df=pd.DataFrame(columns=["block", "height", "top_mi", "top_ma", "left", "text"])):
    for i in np.unique(page["block_num"]):
        block = page[page.block_num == i]
        text = " ".join(block["text"])
        df = pd.concat([df, pd.DataFrame({"block": [i], "height": [block["height"].max()], "text": [text], "top_mi": [block["top"].min()], "top_ma": [block["top"].max()], "left": [block["left"].min()]})], ignore_index=True)
    return df


def join_blocks(df):
    # join two blocks if their height is identical
    j = 1
    ref = 0
    while len(df) > j:
        if df["height"].iloc[ref] == df["height"].iloc[j]:
            df.at[ref, "text"] = df["text"].iloc[ref] + " " + df["text"].iloc[j]
            df.at[ref, "top_mi"] = min(df["top_mi"].iloc[ref], df["top_mi"].iloc[j])
            df.at[ref, "top_ma"] = max(df["top_ma"].iloc[ref], df["top_ma"].iloc[j])
            df.at[ref, "left"] = min(df["left"].iloc[ref], df["left"].iloc[j])
            df.at[j, "text"] = ""
            df.at[j, "top_mi"] = np.nan
            df.at[j, "top_ma"] = np.nan
            df.at[j, "left"] = np.nan
            df.at[j, "height"] = np.nan
            df.at[j, "block"] = np.nan
        else:
            ref = j
        j += 1
    return df.dropna().reset_index(drop=True)


def find_structures(df):
    top = 0
    info = None
    for i in range(len(df)):
        indicators = ["v. ", "S. ", " / ", " ; "]
        indicators = [df["text"].iloc[i].count(indicator) for indicator in indicators]
        if sum(indicators) > 1:
            top = df.iloc[i]["top_mi"]-5
            info = df.iloc[i]["text"]
            df.drop(i, inplace=True)
            break
    df.query("top_mi > @top", inplace=True)
    title = df[df.height==df["height"].max()]
    df.query("top_mi > @title['top_mi'].values[0]", inplace=True)
    for i in range(len(df)):
        if df["height"].iloc[i] > 20:
            text = " ".join(df["text"].iloc[i:])
            preamble = " ".join(df["text"].iloc[:i])
            break
    return info, title["text"].values[0], preamble, text


# Read PDF
images = pdf2image.convert_from_path("Frühausgabe.pdf")

articles = {}
info = None
iscontinuation = False
for i, image in enumerate(images, start=1):
    print(f"Processing page {i}")
    if (i == 1):
        continue
    # Convert image to text
    page = pytesseract.image_to_data(image, lang="deu", output_type=pytesseract.Output.DATAFRAME).dropna()
    page["text"] = page["text"].str.strip()
    page.query("not (text=='')", inplace=True)
    page.query("height > 5", inplace=True)
    page.query("top < 2200", inplace=True)
    # If this is a Fortsetzung, the text may be closer to the top
    if iscontinuation:
        page.query("top > 40", inplace=True)
    else:
        page.query("top > 100", inplace=True)
    # page.query("top > 100", inplace=True)
    if iscontinuation:
        df = data_frame_sentences(page, df=df)
    else:
        df = data_frame_sentences(page)
    if "Fortsetzung" in df.iloc[-1]["text"]:
        iscontinuation = True
        df = df.iloc[:-1]
    else:
        iscontinuation = False
        df = join_blocks(df)
        # print(df)
        # print("="*50)
        info, title, preamble, text = find_structures(df)
        articles[i] = {"Seite": i, "Info": info, "Titel": title, "Vorwort": preamble, "Text": text}

get_post(articles)
