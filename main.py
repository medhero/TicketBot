import time
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, 
                                      NoSuchElementException,
                                      WebDriverException)

# --- CONFIGURATION ---
URL = "https://webook.com/en/events/fez-morocco-v-benin-friendlies-46674282-tickets/book"
TELEGRAM_BOT_TOKEN = "8103713477:AAGmX6tub09ZyJKKJan18Djr-FF8y2tRRAc"
TELEGRAM_CHAT_ID = "5736780477"

# Login credentials (replace with your actual credentials)
LOGIN_EMAIL = "manyfestoamine1@gmail.com"
LOGIN_PASSWORD = "Pass123@"

# Status tracking to avoid duplicate messages
last_status = None

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=10)
        print(f"✅ Telegram sent: {message}")
    except Exception as e:
        print(f"⚠️ Telegram error: {str(e)}")

def human_like_delay(min_sec=1, max_sec=3):
    """Add random delays to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))

def setup_driver():
    """Configure the browser to appear more human-like"""
    print("🚀 Starting undetected Chrome...")
    
    try:
        options = uc.ChromeOptions()

        # ✅ Enable headless mode for Render or server environments
        options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")

        # Set a common user agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')

        driver = uc.Chrome(options=options)

        # Remove navigator.webdriver flag
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver
    except Exception as e:
        print(f"⚠️ Failed to setup driver: {str(e)}")
        send_telegram_alert("⚠️ Failed to setup Chrome driver! Check dependencies.")
        raise


def handle_cookie_consent(driver):
    """Try to decline cookies using a robust approach."""
    try:
        print("🍪 Searching for cookie consent...")

        # Wait until a button with 'Decline' appears (more generic search)
        decline_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[.//p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'decline all')] or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'decline')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", decline_button)
        human_like_delay(0.5, 1.2)

        try:
            decline_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", decline_button)

        print("✅ Declined cookies.")
        human_like_delay(1, 2)
        return True

    except TimeoutException:
        print("ℹ️ No cookie popup detected.")
        return False
    except Exception as e:
        print(f"⚠️ Cookie consent handling failed: {str(e)}")
        return False


def login(driver):
    """Perform login with provided credentials"""
    try:
        print("🔐 Attempting login...")
        
        # Email field with multiple fallbacks
        try:
            email_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
        except TimeoutException:
            email_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
        
        email_field.clear()
        for char in LOGIN_EMAIL:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        print("📧 Filled email")
        human_like_delay(0.5, 1.5)
        
        # Password field
        password_field = driver.find_element(By.XPATH, "//input[@type='password']")
        password_field.clear()
        for char in LOGIN_PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        print("🔑 Filled password")
        human_like_delay(0.5, 1.5)
        
        # Login button
        login_button = driver.find_element(By.ID, "email-login-button")
        driver.execute_script("arguments[0].style.border='2px solid red';", login_button)
        human_like_delay(0.3, 0.7)
        driver.execute_script("arguments[0].click();", login_button)
        print("🔐 Submitted login form")
        
        # Verify login success
        WebDriverWait(driver, 20).until(
            lambda d: "login" not in d.current_url.lower() or 
                     d.find_elements(By.XPATH, "//*[contains(text(), 'Welcome')]")
        )
        print("✅ Login successful")
        return True
            
    except Exception as e:
        print(f"⚠️ Login error: {str(e)}")
        driver.save_screenshot("login_error.png")
        send_telegram_alert(f"⚠️ Login failed: {str(e)}")
        return False
def load_last_status():
    try:
        with open("status.txt", "r") as f:
            return f.read().strip()
    except:
        return None

def save_last_status(status):
    try:
        with open("status.txt", "w") as f:
            f.write(status)
    except Exception as e:
        print(f"⚠️ Couldn't save status: {e}")

def check_availability(driver):
    global last_status

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        with open("snapshot.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        page_content = driver.page_source.lower()
        sold_out = "sold out" in page_content or "officially sold out" in page_content

        current_status = "sold_out" if sold_out else "available"
        print(f"🔍 Current ticket status: {current_status}")

        # Save the current status (optional, in case you want to restore in future runs)
        save_last_status(current_status)
        last_status = current_status

        if current_status == "sold_out":
            print("❌ Tickets are sold out")
            send_telegram_alert("🚫 All tickets are currently sold out. Still watching...")
        else:
            print("🎯 Tickets may be available!")
            driver.save_screenshot("available.png")
            send_telegram_alert(f"🎟️ TICKETS MAY BE AVAILABLE!\n{URL}\nCheck attached screenshot!")

        return True

    except Exception as e:
        print(f"⚠️ Availability check error: {str(e)}")
        driver.save_screenshot("availability_error.png")
        send_telegram_alert(f"⚠️ Failed to check availability: {str(e)}")
        return False


def check_ticket():
    global last_status
    
    try:
        driver = setup_driver()
        
        # Initial page load
        print("🌐 Visiting homepage...")
        driver.get("https://webook.com")
        human_like_delay(2, 4)
        
        # Handle cookies
        handle_cookie_consent(driver)
        
        # Navigate to login
        print("🔍 Going to login page...")
        driver.get("https://webook.com/login")
        human_like_delay(2, 3)
        
        # Perform login
        if not login(driver):
            return
            
        # Check tickets
        print(f"🎟️ Loading ticket page: {URL}")
        driver.get(URL)
        human_like_delay(3, 5)
        
        # Check for security blocks
        if any(text in driver.page_source.lower() for text in ["cloudflare", "security check", "blocked"]):
            print("⚠️ Security challenge detected")
            time.sleep(15)
            if "blocked" in driver.page_source.lower():
                driver.save_screenshot("blocked.png")
                send_telegram_alert("🛑 BLOCKED by security! Check screenshot.")
                return
        
        # Check availability
        check_availability(driver)
            
    except Exception as e:
        print(f"⚠️ Critical error: {str(e)}")
        send_telegram_alert(f"🆘 Script crashed: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

# --- MAIN LOOP ---
if __name__ == "__main__":
    print("Starting ticket monitoring...")
    send_telegram_alert("🔔 Ticket monitor started running!")

    last_status = load_last_status()  # ✅ Load once globally

    while True:
        check_ticket()
        delay = random.randint(120, 300)
        print(f"⏳ Next check in {delay//60}m {delay%60}s...")
        time.sleep(delay)
        print("🔄 Restarting check loop...")
