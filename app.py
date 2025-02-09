import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Saudi Market News Sentiment", layout="wide")

api_token = st.secrets["MARKETAUX_API_TOKEN"]

def get_sentiment_color(score):
    if score >= 0.2:
        return "🟢 Positive"
    elif score <= -0.2:
        return "🔴 Negative"
    else:
        return "🟡 Neutral"

def fetch_news():
    base_url = "https://api.marketaux.com/v1/news/all"
    published_after = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
    
    params = {
        "countries": "sa",
        "filter_entities": True,
        "limit": 100,
        "published_after": published_after,
        "api_token": api_token
    }
    
    try:
        response = requests.get(base_url, params=params)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def create_sentiment_summary(entities_data):
    df = pd.DataFrame(entities_data)
    sentiment_summary = df.groupby('symbol').agg({
        'sentiment_score': ['mean', 'count'],
        'name': 'first'
    }).reset_index()
    
    sentiment_summary.columns = ['symbol', 'avg_sentiment', 'mention_count', 'company_name']
    return sentiment_summary

def main():
    st.title("🇸🇦 Saudi Market News Sentiment Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Market Sentiment Overview")
    
    if st.button("Analyze Latest News"):
        with st.spinner("Analyzing market sentiment..."):
            news_data = fetch_news()
            
            if news_data and "data" in news_data:
                # Collect all entities
                all_entities = []
                for article in news_data["data"]:
                    if article.get("entities"):
                        all_entities.extend(article["entities"])
                
                if all_entities:
                    # Create sentiment summary
                    sentiment_df = create_sentiment_summary(all_entities)
                    
                    # Sentiment Distribution Plot
                    fig = px.bar(sentiment_df,
                                x='symbol',
                                y='avg_sentiment',
                                color='avg_sentiment',
                                color_continuous_scale='RdYlGn',
                                title='Average Sentiment by Company',
                                hover_data=['company_name', 'mention_count'])
                    st.plotly_chart(fig)
                    
                    # Detailed Company Analysis
                    st.subheader("Detailed Company Sentiment Analysis")
                    for _, row in sentiment_df.iterrows():
                        with st.expander(f"{row['company_name']} ({row['symbol']})"):
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Average Sentiment", f"{row['avg_sentiment']:.3f}")
                            col2.metric("Sentiment Status", get_sentiment_color(row['avg_sentiment']))
                            col3.metric("News Mentions", row['mention_count'])
                
                # Display Recent News with Sentiment
                st.subheader("Recent News Analysis")
                for article in news_data["data"]:
                    if article.get("entities"):
                        avg_sentiment = sum(e['sentiment_score'] for e in article['entities']) / len(article['entities'])
                        sentiment_color = get_sentiment_color(avg_sentiment)
                        
                        with st.expander(f"{sentiment_color} | {article['title']}"):
                            st.write(f"**Published:** {article['published_at']}")
                            st.write(f"**Description:** {article['description']}")
                            
                            # Create entities dataframe
                            entities_df = pd.DataFrame(article["entities"])
                            if not entities_df.empty:
                                entities_df['sentiment_status'] = entities_df['sentiment_score'].apply(get_sentiment_color)
                                st.dataframe(
                                    entities_df[['symbol', 'name', 'sentiment_score', 'sentiment_status']]
                                )
                            
                            st.markdown(f"[Read Full Article]({article['url']})")

if __name__ == "__main__":
    main()
