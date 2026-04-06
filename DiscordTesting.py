import requests
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import logging

load_dotenv()

API_ENDPOINT = 'https://discord.com/api/v10'
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'

logging.basicConfig(level=logging.INFO)

def get_auth_url():
    return f'https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify'


def exchange_code(code):
    try:
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(f'{API_ENDPOINT}/oauth2/token', data=data, headers=headers)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during token exchange: {e}")
        return None


def authorize():
    auth_url = get_auth_url()
    options = Options()
    # Remove the headless option to see the browser window
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(auth_url)

    try:
        logging.info("Navigating to authorization URL...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(os.getenv('DISCORD_EMAIL'))
        logging.info("Entered email.")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(os.getenv('DISCORD_PASSWORD'))
        logging.info("Entered password.")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))).click()
        logging.info("Clicked login button.")
        
        # Wait for the authorization page to load and click the authorize button
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@type='button' and contains(@class, 'button__201d5') and contains(@class, 'lookFilled__201d5') and contains(@class, 'colorBrand__201d5') and contains(@class, 'sizeMedium__201d5') and contains(@class, 'grow__201d5')]"))).click()
        logging.info("Clicked authorize button.")

        # Extract the authorization code from the redirected URL
        WebDriverWait(driver, 10).until(EC.url_contains("code="))
        redirected_url = driver.current_url
        parsed_url = urlparse(redirected_url)
        auth_code = parse_qs(parsed_url.query).get('code', [None])[0]

        if not auth_code:
            raise Exception("Authorization code not found in the redirected URL")

        return auth_code
    except Exception as e:
        logging.error(f"Authorization failed: {e}")
        return None
    finally:
        driver.quit()


def main():
    try:
        auth_code = authorize()
        if not auth_code:
            print("Authorization failed.")
            return

        response = exchange_code(auth_code)
        if response:
            print("Token exchange successful:", response)
        else:
            print("Token exchange failed.")
    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    main()