import streamlit as st
import pandas as pd
import random
import string
import gspread
import altair as alt
# from streamlit_gsheets import GSheetsConnection


import scraper
import analysis


def generate_session_id(length=10):
    """Generate a random session ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_chart_data(sentiment_df):
    scores = {}
    # get overall positive
    sentiment_count = sentiment_df.groupby(["sentiment"])["sentiment"].count()
    overall_score = sentiment_count.get("positive",0)+sentiment_count.get("neutral",0)/len(sentiment_df)
    scores["overall_score"]=overall_score

    #get category sentiment count
    category_count = sentiment_df.groupby(["context","sentiment"])["sentiment"].count().reset_index(name="count")
    print(category_count) #debug
    scores["category_count"]=category_count.to_dict("records")

    return scores


with st.sidebar:
    keyword = st.text_input("Enter the keyword you want to monitor:")
    period = st.selectbox(
        "Select your prefer monitoring period:",
        (1, 7, 30, 90, 180),
            )
    st.caption("If '7' has been selected, the scraper will get posts from the last 7 days.")
    start_scrapping = st.button("Start Analyse")

st.header("Specialise in tracking :rainbow[TikTok] data :chart_with_upwards_trend:", divider="gray")

# workflow logic for the order of scrap & upload to gsheet -> read gsheet
# Initialize placeholder for results
if 'scraped_id' not in st.session_state:
    st.session_state.scraped_id = None
    total_view = 0
    total_posts = 0
    total_likes = 0

# first start scrapping and upload to gsheet
if start_scrapping:
    with st.spinner("Scraping TikTok data..."):
        try:
            # tiktok scraping
            ws = scraper.tiktok_scraping(keyword, int(period)) #todo: take userinput from st
            df = pd.DataFrame(ws.get_all_records())
            indicator_stats = scraper.sum_indicator(df=df)        
            st.success('Scraping completed!')

            total_view = indicator_stats["total_view"]
            total_posts = indicator_stats["total_posts"]
            total_likes = indicator_stats["total_likes"]

            st.session_state.scraped_id = generate_session_id()

        except Exception as e:
                st.error(f"Error during scraping: {str(e)}")
                st.session_state.scraped_id = None


    # page layout
    st.header(f"You're looking at '{keyword}' in last {period} day(s) trend")
    col1, col2, col3 = st.columns(3, vertical_alignment="bottom")

    # fist indicator for total views
    tt_views = col1.container(height=200, border=True)
    tt_views.subheader(":camera: Total Views")

    # second indicator for total posts
    tt_posts = col2.container(height=200, border=True)
    tt_posts.subheader(":chart_with_upwards_trend: Total Posts")

    # third indicator for total likes
    tt_likes = col3.container(height=200, border=True)
    tt_likes.subheader(":heart: Total Likes")

    # then streamlit read sheet for analysis
    if st.session_state.scraped_id is not None:

        tt_views.title(total_view)
        tt_posts.title(total_posts)
        tt_likes.title(total_likes)

        with st.spinner("Analysing sentiment trend..."):
            try:
                # google sheet client
                gc = gspread.service_account(filename="tiktokanalysis-451510-6d471ad5314b.json")
                # read from google public sheet
                gsh = gc.open_by_key("1Eg64Lvr5an6jtF2vgtTqwjGEFgPFe2qOERi6Slr55pI")
                worksheet1 = gsh.get_worksheet(0)
                gsheet_df = pd.DataFrame(worksheet1.get_all_records())


                # call sentiment analysis with new data
                try:
                    analysis.text_analyse(gsheet_df)
                    # get data for graphic chart
                    worksheet2 = gsh.get_worksheet(1)
                    sentiment_df = pd.DataFrame(worksheet2.get_all_records())
                    print("Original sentiment_df", sentiment_df) #debug
                    scores = get_chart_data(sentiment_df)

                    # sentiment analysis chart 
                    with st.container():
                        st.header("Sentiment Analysis Trend")
                        category_df = pd.DataFrame(scores["category_count"])
                        print("Category counts: ", category_df) #debug

                        # st.bar_chart(category_df, x="context", y="count", color="sentiment")
                        #create an Altair chart
                        chart = alt.Chart(category_df).mark_bar().encode(
                            x="context",
                            y="count",
                            color="sentiment"
                        ).properties(
                            title = "Sentiment Analysis by Categories"
                        )

                        st.altair_chart(chart, use_container_width=True)
                        

                except Exception as e:
                    st.error(f"Error reading Google Sheets: {str(e)}")

            except Exception as e:
                st.error(f"Error reading Google Sheets: {str(e)}")

