from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from fuzzywuzzy import process
import requests
import os

app = FastAPI()

templates = Jinja2Templates(directory="static")

API_KEY = os.getenv("TMDB_API_KEY")
URL = f"https://api.themoviedb.org/3/movie/550?api_key={API_KEY}" 

headers = { 
    "Authorization": f"Bearer {API_KEY}" 
    }

response = requests.get(URL, headers=headers) 
data = response.json() 
print(data)

def load_movie_data():
    movies_df = pd.read_csv("https://drive.google.com/file/d/1fFyrjeTwxUIN-NoKVMo-GIK3q1gKbLEJ/view?usp=drive_link")
    return movies_df

def load_ratings_data():
    ratings_df = pd.read_csv("https://drive.google.com/file/d/159nMONyTiqDVaEgzVda6kjoTkg4t5DnU/view?usp=drive_link")
    return ratings_df

movies_df = load_movie_data()
ratings_df = load_ratings_data()

def clean_title(title):
    return re.sub("[^a-zA-Z0-9 ]", "", title)

movies_df['genres_list'] = movies_df['genres'].str.replace('|', ' ')
movies_df['clean_title'] = movies_df['title'].apply(clean_title)
movies_data = movies_df[['movieId', 'clean_title', 'genres_list']]

ratings_data = ratings_df.drop(['timestamp'], axis=1)

merged_data = ratings_data.merge(movies_data, on='movieId')

vectorizer_title = TfidfVectorizer(ngram_range=(1, 2))
tfidf_title = vectorizer_title.fit_transform(movies_data['clean_title'])

def search_by_title(title):
    title = clean_title(title)
    query_vec = vectorizer_title.transform([title])
    similarity = cosine_similarity(query_vec, tfidf_title).flatten()
    indices = np.argpartition(similarity, -5)[-5:]
    results = movies_data.iloc[indices][::-1]
    return results

vectorizer_genres = TfidfVectorizer(ngram_range=(1, 2))
tfidf_genres = vectorizer_genres.fit_transform(movies_data['genres_list'])

def search_similar_genres(genres):
    query_vec = vectorizer_genres.transform([genres])
    similarity = cosine_similarity(query_vec, tfidf_genres).flatten()
    indices = np.argpartition(similarity, -10)[-10:]
    results = movies_data.iloc[indices][::-1]
    return results

def scores_calculator(movie_id):
    similar_users = merged_data[(merged_data['movieId'] == movie_id) & (merged_data['rating'] >= 4)]['userId'].unique()
    similar_user_recs = merged_data[(merged_data['userId'].isin(similar_users)) & (merged_data['rating'] >= 4)]['movieId']
    similar_user_recs = similar_user_recs.value_counts() / len(similar_users)

    all_users = merged_data[(merged_data['movieId'].isin(similar_user_recs.index)) & (merged_data['rating'] >= 4)]
    all_users_recs = all_users['movieId'].value_counts() / all_users['userId'].nunique()

    genres_of_selected_movie = merged_data[merged_data['movieId'] == movie_id]['genres_list'].unique()
    genres_of_selected_movie = np.array2string(genres_of_selected_movie)
    movies_with_similar_genres = search_similar_genres(genres_of_selected_movie)

    indices = []
    for index in movies_with_similar_genres[(movies_with_similar_genres['movieId'].isin(similar_user_recs.index))]['movieId']:
        indices.append(index)

    similar_user_recs.loc[indices] = similar_user_recs.loc[indices] * 1.5

    indices = []
    for index in movies_with_similar_genres[(movies_with_similar_genres['movieId'].isin(all_users_recs.index))]['movieId']:
        indices.append(index)
    all_users_recs.loc[indices] = all_users_recs.loc[indices] * 0.9

    rec_percentages = pd.concat([similar_user_recs, all_users_recs], axis=1)
    rec_percentages.columns = ['similar', 'all']
    rec_percentages['score'] = rec_percentages['similar'] / rec_percentages['all']

    rec_percentages = rec_percentages.sort_values('score', ascending=False)
    return rec_percentages

def fetch_movie_details(title):
    URL = f"https://api.themoviedb.org/3/search/movie?query={title}&api_key={API_KEY}"
    response = requests.get(URL)
    data = response.json()
    
    print(data)
    
    if 'results' not in data or not data['results']:
        return {
            'poster': 'https://via.placeholder.com/100',
            'synopsis': 'No synopsis available.',
            'director': 'Unknown',
            'cast': 'Unknown',
            'rating': 'N/A'
        }
    
    movie = data['results'][0]
    movie_id = movie['id']
    
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=credits"
    details_response = requests.get(details_url)
    details_data = details_response.json()
    
    director = next((member['name'] for member in details_data['credits']['crew'] if member['job'] == 'Director'), 'Unknown')
    cast = ', '.join([member['name'] for member in details_data['credits']['cast'][:5]])
    
    return {
        'poster': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else 'https://via.placeholder.com/100',
        'synopsis': movie['overview'],
        'director': director,
        'cast': cast,
        'rating': movie['vote_average']
    }

def recommendation_results(user_input, title=0):
    title_candidates = search_by_title(user_input)
    movie_id = title_candidates.iloc[title]['movieId']
    scores = scores_calculator(movie_id)
    results = scores.head(10).merge(movies_data, left_index=True, right_on='movieId')[['clean_title', 'score', 'genres_list']]
    results = results.rename(columns={'clean_title': 'title', 'genres_list': 'genres'})
    return results

def correct_title(user_input):
    titles = movies_df['title'].tolist()
    closest_match, score = process.extractOne(user_input, titles)
    return closest_match

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "searched_title": "", "recommendations": ""})

@app.post("/recommendations", response_class=HTMLResponse)
async def get_recommendations(request: Request):
    form = await request.form()
    user_input = form.get("title")
    
    corrected_title = correct_title(user_input)
    title_candidates = search_by_title(corrected_title)
    
    if title_candidates.empty:
        return templates.TemplateResponse("index.html", {"request": request, "searched_title": user_input, "recommendations": "<p>No movies found! Please try another title.</p>"})
    
    title_index = 0
    recommendations = recommendation_results(corrected_title, title_index)

    recommendations_html = f"<p>Showing results for: <strong>{corrected_title}</strong></p>"
    for _, row in recommendations.iterrows():
        movie_details = fetch_movie_details(row['title'])
        google_search_url = f"https://www.google.com/search?q={row['title'].replace(' ', '+')}+movie"
        recommendations_html += f"""
        <div class="recommendation-card">
            <img src="{movie_details['poster']}" alt="{row['title']} poster" class="movie-poster">
            <div class="movie-title"><a href="{google_search_url}" target="_blank">{row['title']}</a></div>
            <div class="movie-genres">Genres: {row['genres']}</div>
            <div class="movie-synopsis">Synopsis: {movie_details['synopsis']}</div>
            <div class="movie-director">Director: {movie_details['director']}</div>
            <div class="movie-cast">Cast: {movie_details['cast']}</div>
            <div class="movie-rating">Rating: {movie_details['rating']}</div>
        </div>
        """
    
    return templates.TemplateResponse("index.html", {"request": request, "searched_title": corrected_title, "recommendations": recommendations_html})
