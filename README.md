# Little Flix - Movie Recommendation App

## Overview
Little Flix is a movie recommendation web application built with FastAPI. It allows users to enter a movie title and receive personalized movie recommendations.

## Features
- **Search for Movie Recommendations**: Users can input a movie title to get similar movie recommendations.
- **Detailed Movie Information**: Each recommended movie includes an external link to its overview providing details such as its poster, synopsis, director, cast, genres, and rating.
- **Dark Mode Toggle**: Users can switch between light and dark mode for a better viewing experience.

## Tech Stack
- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript

## Setup Instructions

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation
1. **Clone the Repository**:
    ```sh
    git clone https://github.com/kedinaimoke/little-flix.git
    cd little-flix
    ```

2. **Create a Virtual Environment**:
    ```sh
    python -m venv flixenv
    flixenv\Scripts\activate   # On Linux use `source flixenv/bin/activate`
    ```

3. **Install the Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Run the Application**:
    ```sh
    uvicorn main:app --reload
    ```

5. **Access the Application**:
    - Open your web browser and navigate to `http://127.0.0.1:8000`.

## Project Structure
- little-flix/
    - README.md: Application overview 
    - main.py: FastAPI application code
    - render.yaml: Render build components
    - requirements.txt: Python dependencies
    - start.sh: Shell script to start application
    - static/
        - index.html: HTML template for the search page
        - results.html: HTML template for the results page
        - styles.css: CSS styles


## Main Files

### main.py
- The core FastAPI application containing routes, data loading, and recommendation logic.
- Fetches movie details with external links from Google's overview and renders HTML templates with recommendations.

### HTML Templates
- `index.html`: Displays the search form and allows users to input movie titles.
- `results.html`: Shows the recommended movies with detailed information.

### CSS Styles
- `styles.css`: Contains styles for light and dark mode, and movie recommendation cards.

## Usage
- **Search for Movies**: Enter a movie title in the search bar and click "Get Recommendations".
- **Dark Mode Toggle**: Click the "Toggle Dark Mode" button to switch between light and dark themes.
- **View Details**: Click on a recommended movie title to search for more details on Google.

## Contributions
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License.

---

Enjoy using Little Flix! Happy movie watching! 🍿🎬
