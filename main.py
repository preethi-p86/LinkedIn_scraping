from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import getpass
import time

options = Options()

options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--allow-running-insecure-content')
options.add_experimental_option("detach", True)

# LinkedIn login
username = input('Enter your LinkedIn email: ')
password = getpass.getpass('Enter your password: ')
search_keyword = input('Enter keyword to search: ')

import warnings
warnings.filterwarnings('ignore')

driver = webdriver.Chrome(options=options)

driver.get("https://www.linkedin.com/login")

driver.find_element(By.ID, "username").send_keys(username)
driver.find_element(By.ID, 'password').send_keys(password)

driver.find_element(By.XPATH, "//button[@type='submit']").click()

time.sleep(3)


# username = driver.find_element(By.ID, "username")
# password = driver.find_element(By.ID, "password")
# username.send_keys("preethi8abi@gmail.com")  # Replace with your LinkedIn email
# password.send_keys("123Hello!@")             # Replace with your LinkedIn password
# driver.find_element(By.XPATH, "//button[@type='submit']").click()

# time.sleep(5)

# Search keyword
# search_keyword = "Arun A"
encoded_keyword = search_keyword.replace(' ', '%20')
search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}"

driver.get(search_url)
time.sleep(5)

# Scroll to load more posts
scroll_pause_time = 5
last_height = driver.execute_script("return document.body.scrollHeight")
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Find post elements
li_elements = driver.find_elements(By.XPATH, "//li[contains(@class, 'artdeco-card mb2')]")

data = []

for li in li_elements:
    
    html = li.get_attribute("innerHTML")
    soup = BeautifulSoup(html, 'html.parser')
    raw_text = soup.get_text(separator="\n").strip()

    if raw_text:
        lines = raw_text.split("\n")
        seen = set()
        cleaned_lines = [
                line for line in lines 
                if (line.strip() != '' and (line != '#' and line not in seen and not seen.add(line)) or line == '#')
            ]

        if len(cleaned_lines) > 3:
            if 'followers' in cleaned_lines[2]:
                post = {
                    "author": cleaned_lines[1] if len(cleaned_lines) > 1 else "",
                    "reposted by" : "Not a Repost",
                    "tagline": "No Tagline",
                    "date": " ".join(cleaned_lines[4].split()[:3]) if len(cleaned_lines) > 6 else "",
                    "description": ""
                }
                i=6
            
            elif 'reposted' in cleaned_lines[2] and 'followers' in cleaned_lines[4]:
                post = {
                    "reposted by" : cleaned_lines[1] if len(cleaned_lines) > 1 else "",
                    "author": cleaned_lines[3] if len(cleaned_lines) > 1 else "",
                    "tagline": "No Tagline",
                    "date": " ".join(cleaned_lines[6].split()[:3]) if len(cleaned_lines) > 6 else "",
                    "description": ""
                }
                i=8

            elif 'reposted' in cleaned_lines[2]:
                post = {
                    "reposted by" : cleaned_lines[1] if len(cleaned_lines) > 1 else "",
                    "author": cleaned_lines[3] if len(cleaned_lines) > 1 else "",
                    "tagline": cleaned_lines[6] if len(cleaned_lines) > 4 else "",
                    "date": " ".join(cleaned_lines[8].split()[:3]) if len(cleaned_lines) > 6 else "",
                    "description": ""
                }
                i=10

            else:
                post = {
                    "author": cleaned_lines[1] if len(cleaned_lines) > 1 else "",
                    "reposted by" : "Not a Repost",
                    "tagline": cleaned_lines[4] if len(cleaned_lines) > 4 else "",
                    "date": " ".join(cleaned_lines[6].split()[:3]) if len(cleaned_lines) > 6 else "",
                    "description": ""
                }
                i = 11


            skip_words = {'like', 'comment', 'repost', 'send', 'hashtag'}
            post_content = []
            
            while i< len(cleaned_lines):
                line = cleaned_lines[i].strip()
                lower_line = line.lower()
                if lower_line.isdigit() or lower_line in skip_words: # or stripped.endswith("comments") or stripped.endswith("reposts")
                    i+=1
                if "...more" in lower_line:
                    break
                if lower_line == "#" and i+1 < len(cleaned_lines):
                    hashtag = '#' + cleaned_lines[i+1].strip()
                    post_content.append(hashtag)
                    i+=2
                    continue
                if lower_line == 'hashtag' or lower_line.strip() == '':
                    i+=1
                    continue
                post_content.append(lower_line)
                i+=1

            post["description"] = ' '.join(post_content)
            data.append(post)
    

driver.quit()

df = pd.DataFrame(data)
df.to_excel("LinkedIn.xlsx", index=False)
print("Data saved successfully!")
