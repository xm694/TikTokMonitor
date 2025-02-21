import streamlit as st
from ensembledata.api import EDClient
import pandas as pd
import gspread


def tiktok_scraping(keyword, period):

    client = EDClient(st.secrets["ED_TOKEN"])
    gc = gspread.service_account(filename="tiktokanalysis-451510-6d471ad5314b.json")
    # gc = gspread.api_key(st.secrets["GSHEET_API_KEY"]) # use api_key method for OAuth Client

    result = client.tiktok.full_keyword_search(
        keyword=keyword,  
        period= period,
        country= "AU")

    # get important indicator out from scraped data
    post_ids = [x["aweme_info"]["aweme_id"] for x in result.data] 

    posts = [x["aweme_info"].get("desc","") or "No description" for x in result.data]

    views = [x["aweme_info"]["statistics"]["play_count"] for x in result.data]

    likes = [x["aweme_info"]["statistics"]["digg_count"] for x in result.data]

    # create dataframe from retrieved data
    lists_of_indicators = list(zip(post_ids, posts, views, likes))
    df = pd.DataFrame(lists_of_indicators, 
                      columns=["post_id", "post", "view", "likes"])
    
    # write to google public sheet
    gsheet = gc.open_by_key("1Eg64Lvr5an6jtF2vgtTqwjGEFgPFe2qOERi6Slr55pI")
    worksheet = gsheet.get_worksheet(0)
    values = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.update(values)

    return worksheet


def sum_indicator(df):
    stats = {}
    stats["total_posts"] = df.shape[0]
    stats["total_view"] = df["view"].astype(int).sum()
    stats["total_likes"] = df["likes"].astype(int).sum()

    return stats


# output = tiktok_scraping("pinkdiamon", 1)
# output.to_csv('demo.csv', index=False)
# json_output = json.dumps(output, indent=4)
