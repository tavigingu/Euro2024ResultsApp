import tkinter as tk
from tkinter import ttk, messagebox, Scrollbar, Text
import requests
from datetime import datetime, timedelta
import pytz
from ttkthemes import ThemedStyle
from tkinter.font import Font
from tkinter import scrolledtext
import webbrowser


api_key = '7ce672abfe0d407eb5383e4468081b27'
base_url = 'https://api.football-data.org/v4/'
competition_code = 'EC'
endpoint = f'competitions/{competition_code}/matches'

params_finished = {
    'season': '2024',
    'status': 'FINISHED',
}

params_upcoming = {
    'season': '2024',
    'status': 'SCHEDULED'
}

headers = {
    'X-Auth-Token': api_key
}

enable_notifications = False
upcoming_matches_global = []
root = tk.Tk()


def get_top_scorers():
    try:
        endpoint = f"competitions/{competition_code}/scorers"
        url = f"{base_url}{endpoint}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        scorers = data['scorers']

        return scorers

    except requests.exceptions.RequestException as e:
        print(f"Eroare la cererea API: {e}")
        return []
    
def display_top_scorers(tab):
    top_scorers = get_top_scorers()

    if not top_scorers:
        messagebox.showerror("Eroare", "Nu s-au putut obține datele despre top scorers.")
        return

    top_scorers_frame = ttk.Frame(tab)
    top_scorers_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(top_scorers_frame, text="Top Marcatori Euro 2024", font=('Helvetica', 16, 'bold')).pack(pady=10)

    for idx, scorer in enumerate(top_scorers, start=1): 
        player_name = scorer['player']['name']
        team_name = scorer['team']['name']
        goals = scorer['goals']

        if goals == 1:
            goals_text = "gol"
        else:
            goals_text = "goluri"

        scorer_text = f"{idx}. {player_name} ({team_name}): {goals} {goals_text}"
        ttk.Label(top_scorers_frame, text=scorer_text, font=('Helvetica', 12)).pack(pady=5, padx=10)

def get_team_id(team_name):
    url = f'{base_url}competitions/{competition_code}/teams'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        teams = data['teams']
        for team in teams:
            if team['name'] == team_name:
                return team['id']
        return None
    else:
        print(f"Error fetching teams: {response.status_code}")
        return None

def get_team_details(team_id):
    try:
        response = requests.get(f"{base_url}/teams/{team_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Eroare la cererea API pentru detalii echipă: {e}")
        return None
    
def show_team_details(team_name):
    team_id = get_team_id(team_name)
    if team_id:
        team_data = get_team_details(team_id)
        if team_data:
            details_window = tk.Toplevel()
            details_window.title(f"Detalii despre {team_name}")

            window_width = 500
            window_height = 400
            screen_width = details_window.winfo_screenwidth()
            screen_height = details_window.winfo_screenheight()
            x = int((screen_width / 2) - (window_width / 2))
            y = int((screen_height / 2) - (window_height / 2))
            details_window.geometry(f'{window_width}x{window_height}+{x}+{y}')

            ttk.Label(details_window, text=f"{team_data['name']}", font=('Arial', 16, 'bold')).pack(pady=10)
            ttk.Label(details_window, text=f"Stadion: {team_data['venue']}", font=('Arial', 12)).pack(pady=5)
            ttk.Label(details_window, text=f"Anul de înființare: {team_data['founded']}", font=('Arial', 12)).pack(pady=5)
            ttk.Label(details_window, text=f"Antrenor: {team_data['coach']['name']}", font=('Arial', 12)).pack(pady=5)

            players_frame = ttk.Frame(details_window)
            players_frame.pack(pady=10)

            scrollbar = Scrollbar(players_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            text_font = Font(family="Helvetica", size=12)

            players_text = Text(players_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=10, width=60, font=text_font)
            players_text.pack()

            scrollbar.config(command=players_text.yview)

            players_text.insert(tk.END, "Lotul de jucători:\n\n")
            for player in team_data['squad']:
                player_info = f"{player['name']} ({player['position']})\n"
                players_text.insert(tk.END, player_info)

            ttk.Button(details_window, text="Închide", command=details_window.destroy).pack(pady=10)

            details_window.mainloop()
        else:
            messagebox.showerror("Eroare", f"Nu am putut obține detalii pentru {team_name}.")
    else:
        messagebox.showerror("Eroare", f"Nu am putut găsi echipa {team_name} în lista de echipe.")


def get_matches():
    try:
        response = requests.get(f"{base_url}{endpoint}", params=params_finished, headers=headers)
        response.raise_for_status()
        data = response.json()

        #print(data)

        matches = data.get('matches', [])
        formatted_matches = []

        for match in matches:
            match_id = match.get('id')
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            match_date = match['utcDate']
            stage = match['stage']
            group = match.get('group', '')

            utc_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
            formatted_date = utc_datetime.strftime('%Y-%m-%d %H:%M:%S')

            formatted_match = {
                'id': match_id,
                'homeTeam': home_team,
                'awayTeam': away_team,
                'scoreHome': score_home,
                'scoreAway': score_away,
                'matchDate': formatted_date,
                'stage': stage,
                'group': group
            }
            formatted_matches.append(formatted_match)

        return formatted_matches

    except requests.exceptions.RequestException as e:
        print(f"Eroare la cererea API: {e}")
        return []

def get_upcoming_matches():
    try:
        response = requests.get(f"{base_url}{endpoint}", params=params_upcoming, headers=headers)
        response.raise_for_status()
        data = response.json()
        matches = data['matches']
        formatted_matches = []

        for match in matches:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            match_datetime = match['utcDate']
            stage = match['stage']
            group = match.get('group', '')
            
            utc_datetime = datetime.fromisoformat(match_datetime.replace('Z', '+00:00'))
            formatted_date = utc_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            formatted_match = {
                'homeTeam': home_team,
                'awayTeam': away_team,
                'matchDateTime': formatted_date,
                'stage': stage,
                'group': group
            }
            formatted_matches.append(formatted_match)

        return formatted_matches
    
    except requests.exceptions.RequestException as e:
        print(f"Eroare la cererea API pentru meciurile viitoare: {e}")
        return []

##############################################################

def display_finished_matches(tab):
    finished_matches = get_matches()

    canvas = tk.Canvas(tab, width=980, height=560)
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    ttk.Label(scrollable_frame, text="Rezultatele Meciurilor Euro 2024:", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=6, pady=10)

    for idx, match in enumerate(finished_matches, start=1):
        ttk.Button(scrollable_frame, text=match['homeTeam'], command=lambda team=match['homeTeam']: show_team_details(team)).grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(scrollable_frame, text=f"{match['scoreHome']} - {match['scoreAway']}", font=('Helvetica', 12)).grid(row=idx, column=2, padx=5, pady=5)
        ttk.Button(scrollable_frame, text=match['awayTeam'], command=lambda team=match['awayTeam']: show_team_details(team)).grid(row=idx, column=3, padx=5, pady=5, sticky=tk.E)
        ttk.Label(scrollable_frame, text=match['matchDate'], font=('Helvetica', 12)).grid(row=idx, column=0, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=match['stage'], font=('Helvetica', 12)).grid(row=idx, column=4, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=match['group'], font=('Helvetica', 12)).grid(row=idx, column=5, padx=5, pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


def notify_before_match(match, minutes_before=60):
    #calculeaza cand trebuie sa dea notificarea
    notify_time = match['utcDateTime'] - timedelta(minutes=minutes_before)
    current_time = datetime.utcnow()

    if current_time >= notify_time:
        if enable_notifications:
            message = f"Meciul {match['homeTeam']} vs {match['awayTeam']} începe în curând!"
            messagebox.showinfo("Notificare", message)


def check_for_notifications():
    now = datetime.now(pytz.utc)
    notify_time = timedelta(minutes=5)

    for match in upcoming_matches_global:
        match_time = datetime.fromisoformat(match['matchDateTime'].replace('Z', '+00:00'))
        time_diff = match_time - now

        if timedelta(0) < time_diff <= notify_time:
            messagebox.showinfo("Notificare meci", f"Meciul dintre {match['homeTeam']} și {match['awayTeam']} începe în mai puțin de 5 minute!")

    # Verifică notificările din nou în 1 minut
    root.after(60000, check_for_notifications)

def display_upcoming_matches(tab):
    global enable_notifications 
    upcoming_matches = get_upcoming_matches()

    canvas = tk.Canvas(tab, width=980, height=560)
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    ttk.Label(scrollable_frame, text="Meciuri Viitoare Euro 2024:", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=6, pady=10)

    def toggle_notifications():
        global enable_notifications
        enable_notifications = not enable_notifications

    ttk.Checkbutton(scrollable_frame, text="Activare notificări", command=toggle_notifications).grid(row=0, column=5, padx=10, pady=10, sticky=tk.E)

    for idx, match in enumerate(upcoming_matches, start=1):
        ttk.Button(scrollable_frame, text=match['homeTeam'], command=lambda team=match['homeTeam']: show_team_details(team)).grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(scrollable_frame, text=match['awayTeam'], command=lambda team=match['awayTeam']: show_team_details(team)).grid(row=idx, column=2, padx=5, pady=5, sticky=tk.E)
        ttk.Label(scrollable_frame, text=match['matchDateTime'], font=('Helvetica', 12)).grid(row=idx, column=0, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=match['stage'], font=('Helvetica', 12)).grid(row=idx, column=3, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=match['group'], font=('Helvetica', 12)).grid(row=idx, column=4, padx=5, pady=5)

        if enable_notifications:
            notify_before_match(match)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    if enable_notifications:
        check_for_notifications()


def get_competition_groups(competition_code):
    """
    Preia informațiile despre grupele campionatului utilizând endpoint-ul standings.
    """
    try:
        url = f"{base_url}competitions/{competition_code}/standings"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data['standings']
    
    except requests.exceptions.RequestException as e:
        print(f"Eroare la cererea API pentru grupele campionatului: {e}")
        return None


def draw_colored_square(canvas, text, color, x, y):
    square_size = 20
    padding = 5
    text_x = x + padding + square_size / 2
    text_y = y + padding + square_size / 2

    canvas.create_rectangle(x, y, x + square_size + padding * 2, y + square_size + padding * 2, fill=color, outline=color)
    canvas.create_text(text_x, text_y, text=text, fill='white', font=('Helvetica', 12, 'bold'))

def display_groups(tab):
    groups = get_competition_groups(competition_code)
    third_place_teams = []

    if not groups:
        messagebox.showerror("Eroare", "Nu s-au putut obține datele despre grupe.")
        return

    canvas = tk.Canvas(tab, width=980, height=560)
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    row_idx = 0
    for group in groups:
        group_label = ttk.Label(scrollable_frame, text=f"Grupa {group['group']}:", font=('Helvetica', 14, 'bold'))
        group_label.grid(row=row_idx, column=0, columnspan=5, pady=10, sticky='w')
        row_idx += 1

        headers = ["# Echipa", "   MJ", "G", "P"]
        for col_idx, header in enumerate(headers):
            header_label = ttk.Label(scrollable_frame, text=header, font=('Helvetica', 12, 'bold'))
            header_label.grid(row=row_idx, column=col_idx, padx=5, sticky='w')
        row_idx += 1

        for team in group['table']:
            position = team['position']
            color = 'black'
            if position in [1, 2]:
                color = 'blue'
            elif position == 3:
                color = 'green'

            position_canvas = tk.Canvas(scrollable_frame, width=30, height=30)
            draw_colored_square(position_canvas, position, color, 5, 5)
            position_canvas.grid(row=row_idx, column=0, padx=5, pady=5, sticky='w')

            team_name_button = ttk.Button(scrollable_frame, text=team['team']['name'], command=lambda name=team['team']['name']: show_team_details(name))
            team_name_button.grid(row=row_idx, column=1, padx=5, pady=5, sticky='w')

            team_info = [
                team['playedGames'],
                f"{team['goalsFor']}:{team['goalsAgainst']}",
                team['points']
            ]

            for col_idx, info in enumerate(team_info):
                info_label = ttk.Label(scrollable_frame, text=info, font=('Helvetica', 12))
                info_label.grid(row=row_idx, column=col_idx + 2, padx=5, sticky='w')

            if position == 3:
                goal_difference = team['goalsFor'] - team['goalsAgainst']
                third_place_teams.append({
                    'name': team['team']['name'],
                    'points': team['points'],
                    'goal_difference': goal_difference,
                    'goals_for': team['goalsFor'],
                    'played_games': team['playedGames'],
                    'goals_against': team['goalsAgainst']
                })

            row_idx += 1

        row_idx += 1  

    # sortare echipe de pe locul 3
    third_place_teams.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)

    third_place_label = ttk.Label(scrollable_frame, text="Clasamentul echipelor de pe locul 3:", font=('Helvetica', 14, 'bold'))
    third_place_label.grid(row=row_idx, column=0, columnspan=5, pady=10, sticky='w')
    row_idx += 1

    headers = ["# Echipa", "MJ", "G", "P"]
    for col_idx, header in enumerate(headers):
        header_label = ttk.Label(scrollable_frame, text=header, font=('Helvetica', 12, 'bold'))
        header_label.grid(row=row_idx, column=col_idx, padx=5, sticky='w')
    row_idx += 1

    for idx, team in enumerate(third_place_teams, start=1):
        color = 'black'
        if idx <= 4:
            color = 'blue'

        position_canvas = tk.Canvas(scrollable_frame, width=30, height=30)
        draw_colored_square(position_canvas, idx, color, 5, 5)
        position_canvas.grid(row=row_idx, column=0, padx=5, pady=5, sticky='w')

        team_name_button = ttk.Button(scrollable_frame, text=team['name'], command=lambda name=team['name']: show_team_details(name))
        team_name_button.grid(row=row_idx, column=1, padx=5, pady=5, sticky='w')

        team_info = [
            team['played_games'],
            f"{team['goals_for']}:{team['goals_against']}",
            team['points']
        ]

        for col_idx, info in enumerate(team_info):
            info_label = ttk.Label(scrollable_frame, text=info, font=('Helvetica', 12))
            info_label.grid(row=row_idx, column=col_idx + 2, padx=5, sticky='w')

        row_idx += 1

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def fetch_news_about_euro2024(api_key, keyword=''):
    base_keyword = 'Euro 2024'
    full_keyword = f"{base_keyword} {keyword}"
    url = 'https://newsapi.org/v2/everything'
    params = {
        'qInTitle': full_keyword,
        'apiKey': api_key,
        'sortBy': 'publishedAt',
        'language': 'ro'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == 'ok':
            return data['articles']
        else:
            print(f"Error fetching news: {data['message']}")
            return []
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def display_news(tab, api_key):
    def search_news():
        keyword = search_entry.get()
        news = fetch_news_about_euro2024(api_key, keyword)
        update_news_text(news)

    search_frame = ttk.Frame(tab)
    search_frame.pack(fill="x", padx=10, pady=5)

    search_label = ttk.Label(search_frame, text="Caută știri:")
    search_label.pack(side="left", padx=(0, 5))

    search_entry = ttk.Entry(search_frame, width=50)
    search_entry.pack(side="left", padx=(0, 5))

    search_button = ttk.Button(search_frame, text="Caută", command=search_news)
    search_button.pack(side="left")

    # facem un frame în tabul dat pentru a incadra textul și scrollbar-ul
    news_frame = ttk.Frame(tab)
    news_frame.pack(fill="both", expand=True)

    # facem un text widget pentru afisare texte
    text_widget = tk.Text(news_frame, wrap="word", font=('Helvetica', 12))
    text_widget.pack(side="left", fill="both", expand=True)

    #punem scrollbar
    scrollbar = ttk.Scrollbar(news_frame, orient="vertical", command=text_widget.yview)
    scrollbar.pack(side="right", fill="y")
    text_widget.config(yscrollcommand=scrollbar.set)

    def update_news_text(news):
        text_widget.delete(1.0, tk.END)
        for article in news:
            title = article.get('title', '[Title not available]')
            source = article['source'].get('name', '[Source not available]')
            url = article['url']
            published_at = article.get('publishedAt', 'Data not available')

            if title != '[Title not available]' and source != '[Source not available]':
                text_widget.insert("end", f"{title}\n", 'title')
                text_widget.insert("end", f"Source: {source}\n")
                
                cleaned_date = published_at.replace('T', ' ').replace('Z', '')
                text_widget.insert("end", f"Published At: {cleaned_date}\n")
                
                text_widget.insert("end", "URL: ")
                text_widget.insert("end", f"{url}\n", ('link', url))
                text_widget.tag_configure('link', foreground='blue', underline=True)
                text_widget.tag_bind('link', '<Button-1>', lambda event, link=url: webbrowser.open_new(link))

                text_widget.insert("end", "\n\n")

        text_widget.tag_configure('title', font=('Helvetica', 12, 'bold'))

    
    update_news_text(fetch_news_about_euro2024(api_key))


def create_window():
    
    root.title("Rezultatele Meciurilor Euro 2024")

    window_width = 1000
    window_height = 600

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    position_top = int(screen_height/2 - window_height/2)
    position_right = int(screen_width/2 - window_width/2)

    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    style = ThemedStyle(root)
    style.set_theme("plastik")

    notebook = ttk.Notebook(root)

    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Rezultatele Meciurilor")
    display_finished_matches(tab1)

    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Meciurile Viitoare")
    display_upcoming_matches(tab2)

    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Top Marcatori")
    display_top_scorers(tab3)

    tab4 = ttk.Frame(notebook)
    notebook.add(tab4, text="Grupe")
    display_groups(tab4)

   

    tab5 = ttk.Frame(notebook)
    notebook.add(tab5, text="News")
    display_news(tab5, '5b4d67a95f6f40b28b6fc6462a624461')

    notebook.pack(expand=True, fill="both")

    root.mainloop()

create_window()
