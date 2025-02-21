from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd
import gspread


def text_analyse(gsheet_df):

    # google sheet client
    gc = gspread.service_account(filename="tiktokanalysis-451510-6d471ad5314b.json")

    #load context classification model
    context_model = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli")
    context_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli", max_length=514, truncation=True)
    context_classifier = pipeline("zero-shot-classification", model=context_model, tokenizer=context_tokenizer, device=0)

    #load sentiment analysis model
    sentiment_model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")
    sentiment_tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest", max_length=514, truncation=True)
    sentiment_analyser = pipeline("sentiment-analysis", model=sentiment_model, tokenizer=sentiment_tokenizer, device=0)

    # if a dataframe is passed
    # preprocess the dataframe, extract only the post content for analysis
    texts = [x for x in gsheet_df["post"]]

    # step 1: classify context
    candidate_labels = ["brand", "product", "customer support", "community engagement", "promotions"]
    context_result = context_classifier(texts, candidate_labels, truncation=True, max_length=514)
    # print("Context Result Structure:", context_result) # Debug print to see the structure
    # append context category result to df
    gsheet_df["context"] = [ x["labels"][0] for x in context_result]

    # step 2: analyse sentiment meaning
    sentiment_result = sentiment_analyser(texts, truncation=True, max_length=514)
    # print("Sentiment Result Structure:", sentiment_result) # Debug print to see the structure
    # append sentiment result to df
    gsheet_df["sentiment"] = [x["label"] for x in sentiment_result]

    # write to google public sheet
    gsheet = gc.open_by_key("1Eg64Lvr5an6jtF2vgtTqwjGEFgPFe2qOERi6Slr55pI")
    worksheet = gsheet.get_worksheet(1)
    worksheet.update([gsheet_df.columns.values.tolist()] + gsheet_df.values.tolist())

    return

