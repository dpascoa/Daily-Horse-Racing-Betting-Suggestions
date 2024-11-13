import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
from lxml import etree
import re


app = Flask(__name__)

def scrape_racecards():
    time_pattern = r'\b\d{2}:\d{2}\b'

    url = "https://www.timeform.com/horse-racing/racecards"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        #print(soup)

        # Find all elements with the specified outer class
        race_elements = soup.find_all(class_=["w-racecard-grid-race-inactive", "w-racecard-grid-race-active", "w-racecard-grid-race-soon", "w-racecard-grid-race-result"])
        races_today = []

        # Iterate over each found element
        for race in race_elements:
            title_text = race.get("title", "")

            # Check if the text contains "C4", "C5", or "C3"
            if any(c in title_text for c in ["(3)", "(4)", "(5)"]):
                hour_element = race.find_next(["b", "strong"])
                if hour_element:
                    races_today.append({
                        "hour": hour_element.text,
                        "bet": "🐎 All SP < 10 🐎"
                    })

            elif "(2)" in title_text:
                hour_element = race.find_next(["b", "strong"])
                if hour_element:
                    races_today.append({
                        "hour": hour_element.text,
                        "bet": "🐎🐎 All SP >= 10 🐎🐎"
                    })

        race_results_elements = [
            result for result in soup.find_all(class_="w-racecard-grid-race-result")
            if result.get("title") and any(c in result["title"] for c in ["(3)", "(4)", "(5)", "(2)"])
        ]

        race_results = []

        for race in race_results_elements:
            href = race.find_next("a")
            href = href.get("href")
            response = requests.get(f"https://www.timeform.com/{href}", headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                
                # Parse the HTML content with
                tree = etree.HTML(response.text)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                winning_odd = tree.xpath('//*[@id="ReportBody"]/table/tbody[1]/tr[1]/td[15]/span[2]')
                race_time = soup.find(class_="rp-racetimes-mobile").text
                race_time = re.findall(time_pattern, race_time)
                #print(race_time[0], winning_odd[0].text)
                
                race_results.append({
                        "hour": race_time[0],
                        "odd": float(winning_odd[0].text)
                    })
    
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
                return []
            
        races_today_sorted = sorted(races_today, key=lambda x: x["hour"])
        race_results_sorted = sorted(race_results, key=lambda x: x["hour"])
        
        return races_today_sorted, race_results_sorted
        #return races_today_sorted
   
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

@app.route("/")
def home():
    # Call the scraping function to get the race data
    races_today, results_today = scrape_racecards()

    return render_template("index.html", races=races_today, results=results_today)

if __name__ == "__main__":
    app.run(debug=True)
