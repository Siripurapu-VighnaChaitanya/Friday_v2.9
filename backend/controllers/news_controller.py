import requests
from utils.config import NEWS_API_KEY

def get_news(category="general"):
    """
    Fetches the top 3 headlines from NewsAPI.org for the given category.
    Valid categories: business, entertainment, general, health, science, sports, technology.
    """
    if not NEWS_API_KEY:
        return "I cannot fetch the news because the News API Key is missing from your configuration file."
        
    url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            if not articles:
                return f"I couldn't find any recent {category} news."
            
            # Grab top 3 headlines
            headlines = [article['title'].split(' - ')[0] for article in articles[:3]]
            
            spoken_news = f"Here are the top 3 headlines in {category}. "
            for i, headline in enumerate(headlines, 1):
                spoken_news += f"Number {i}: {headline}. "
                
            return spoken_news
        else:
            return "There was an issue retrieving the news right now."
            
    except Exception as e:
        print(f"❌ News API Error: {e}")
        return "I couldn't connect to the news server."

if __name__ == "__main__":
    print(get_news("technology"))
