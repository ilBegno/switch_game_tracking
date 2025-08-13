import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from urllib.parse import quote_plus
import argparse
import re
import warnings

# Suppress TensorFlow warnings and other ML-related warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['AUTOGRAPH_VERBOSITY'] = '0'
os.environ['TF_GPU_THREAD_MODE'] = 'gpu_private'
os.environ['TF_GPU_THREAD_COUNT'] = '2'

# Suppress absl logging
try:
    import absl.logging
    absl.logging.set_verbosity(absl.logging.ERROR)
except ImportError:
    pass

# Additional environment variables to suppress warnings
os.environ['KMP_AFFINITY'] = 'disabled'
os.environ['KMP_WARNINGS'] = '0'
os.environ['KMP_SETTING'] = 'disabled'

def setup_driver():
    """Set up Chrome driver with options for headless browsing"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--log-level=3")  # Suppress Chrome logging
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")
    # Suppress logging
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Make sure you have ChromeDriver installed and in PATH")
        return None

def handle_age_verification(driver, debug=False):
    """Handle age verification page if present"""
    try:
        # Check if we're on an age verification page
        if "age verification" in driver.title.lower() or "age verification" in driver.page_source.lower():
            if debug:
                print("Age verification page detected. Attempting to bypass...")
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Try to find the input fields
            try:
                # Try different selectors for the input fields
                month_inputs = driver.find_elements(By.XPATH, "//input[@placeholder='MM']")
                day_inputs = driver.find_elements(By.XPATH, "//input[@placeholder='DD']")
                year_inputs = driver.find_elements(By.XPATH, "//input[@placeholder='YYYY']")
                
                if not month_inputs:
                    month_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'MM')]")
                if not day_inputs:
                    day_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'DD')]")
                if not year_inputs:
                    year_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'YYYY')]")
                
                if month_inputs and day_inputs and year_inputs:
                    # Fill in dummy values (we'll use a date that would make the user 18+)
                    # Using January 1, 1990 as an example
                    month_inputs[0].send_keys("01")
                    day_inputs[0].send_keys("01")
                    year_inputs[0].send_keys("1990")
                    
                    if debug:
                        print("Filled age verification form with dummy values")
                elif debug:
                    print("Could not find all age verification input fields")
            except Exception as e:
                if debug:
                    print(f"Could not find or fill age verification inputs: {e}")
            
            # Try to find and click the continue button
            try:
                # Try multiple selectors for the continue button
                continue_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')]")
                if not continue_buttons:
                    continue_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'continue')]")
                if not continue_buttons:
                    continue_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")
                if not continue_buttons:
                    continue_buttons = driver.find_elements(By.CSS_SELECTOR, "button")
                
                if continue_buttons:
                    # Try to click the button normally first
                    try:
                        continue_buttons[0].click()
                        if debug:
                            print("Clicked Continue button")
                    except Exception as click_error:
                        # If normal click fails, try JavaScript click
                        if debug:
                            print(f"Normal click failed: {click_error}")
                            print("Trying JavaScript click...")
                        driver.execute_script("arguments[0].click();", continue_buttons[0])
                        if debug:
                            print("Clicked Continue button with JavaScript")
                    
                    # Wait for page to load after clicking continue
                    time.sleep(3)
                    return True
                elif debug:
                    print("Could not find Continue button")
                    return False
            except Exception as e:
                if debug:
                    print(f"Could not find or click Continue button: {e}")
                return False
        return False
    except Exception as e:
        if debug:
            print(f"Error handling age verification: {e}")
        return False

def search_nintendo_store(driver, game_name, max_results=20, debug=False):
    """Search for a game on Nintendo store and return search results"""
    # Format the search URL
    search_query = quote_plus(game_name)
    search_url = f"https://www.nintendo.com/us/search/#q={search_query}&p=1&cat=gme&sort=df"
    
    if debug:
        print(f"Searching for: {game_name}")
        print(f"Search URL: {search_url}")
    
    driver.get(search_url)
    
    # Wait for search results to load
    time.sleep(5)
    
    # Check for age verification page after search
    if handle_age_verification(driver, debug=debug):
        # If we handled age verification, wait a bit for the redirect
        time.sleep(3)
    
    # Debug: Print page title and part of page source
    if debug:
        print(f"Page title: {driver.title}")
        page_source_snippet = driver.page_source[:1000] if len(driver.page_source) > 1000 else driver.page_source
        print(f"Page source snippet: {page_source_snippet}")
    
    # Try multiple approaches to find search results
    # Approach 1: Look for search result items
    search_items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/store/products/']")
    if debug:
        print(f"Found {len(search_items)} search items with CSS selector 'a[href*='/store/products/']'")
    
    # Let's also try a more general search for product links
    if not search_items:
        search_items = driver.find_elements(By.CSS_SELECTOR, "a[href*='store/products']")
        if debug:
            print(f"Found {len(search_items)} search items with CSS selector 'a[href*='store/products']'")
        
    # Let's also try looking for elements with product-related classes
    if not search_items:
        search_items = driver.find_elements(By.CSS_SELECTOR, "[class*='product']")
        if debug:
            print(f"Found {len(search_items)} elements with class containing 'product'")
    
    if not search_items:
        # Approach 2: Look for any elements that might contain search results
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='search'], [class*='result']"))
            )
            time.sleep(2)
            search_items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/store/products/']")
        except TimeoutException:
            pass
    
    # If still no search items, return empty
    if not search_items:
        print("No search results found")
        return []
        
    # Extract information from search results
    results = []
    for i, item in enumerate(search_items[:max_results]):
        try:
            # Get the game link
            game_link = item.get_attribute("href")
            
            # Try to get the game title
            title_element = item.find_element(By.CSS_SELECTOR, "[class*='title'], h3, h4, h5")
            game_title = title_element.text if title_element else "Unknown Title"
            
            # If no title element found, try to get from aria-label or title attribute
            if not game_title or game_title == "Unknown Title":
                game_title = item.get_attribute("aria-label") or item.get_attribute("title") or "Unknown Title"
            
            # Try to get the square image
            img_elements = item.find_elements(By.TAG_NAME, "img")
            square_image_url = None
            if img_elements:
                square_image_url = img_elements[0].get_attribute("src")
            
            # Try to extract main image URL from data attributes if available
            main_image_url = None
            # Look for data attributes that might contain the main image
            data_attrs = ["data-image", "data-src", "data-main-image", "data-hero-image"]
            for attr in data_attrs:
                data_image = item.get_attribute(attr)
                if data_image and ("nintendo.com" in data_image or "atum-img" in data_image):
                    main_image_url = data_image
                    if debug:
                        print(f"Found main image in data attribute '{attr}': {data_image}")
                    break
            
            # Debug: Print all attributes of the search item
            if debug:
                print(f"Debug attributes for search result {i+1}:")
                attrs = item.get_attribute("outerHTML")
                if attrs and len(attrs) > 1000:
                    attrs = attrs[:1000] + "..."
                print(f"  Outer HTML snippet: {attrs}")
            
            results.append({
                'index': i + 1,
                'title': game_title,
                'link': game_link,
                'image_url': square_image_url,
                'main_image_url': main_image_url  # This might contain the main image URL
            })
        except Exception as e:
            if debug:
                print(f"Error processing search result {i+1}: {e}")
            continue
    
    return results


def display_search_results(results):
    """Display search results and let user choose"""
    if not results:
        print("No search results to display")
        return None
    
    print("\nSearch Results:")
    print("-" * 50)
    for result in results:
        print(f"{result['index']}. {result['title']}")
        #print(f"   Link: {result['link']}")
        #if result['image_url']:
        #    print(f"   Image: {result['image_url']}")
        #print()
    print()
    
    while True:
        try:
            choice = input(f"Select a result (1-{len(results)}) or 0 to cancel: ")
            choice = int(choice)
            if choice == 0:
                return None
            elif 1 <= choice <= len(results):
                return results[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(results)}, or 0 to cancel.")
        except ValueError:
            print("Please enter a valid number.")

def get_game_page_images(driver, game_url, debug=False):
    """Navigate to game page and extract main image"""
    try:
        if debug:
            print(f"Navigating to game page: {game_url}")
        driver.get(game_url)
        
        # Wait for the page to load
        time.sleep(5)
        
        # Check for age verification page
        if handle_age_verification(driver, debug=debug):
            # If we handled age verification, wait a bit for the redirect
            time.sleep(3)
        
        # Wait longer for images to load and scroll to trigger lazy loading
        if debug:
            print("Waiting for images to load and scrolling to trigger lazy loading...")
        time.sleep(5)
        
        # Scroll to bottom and back to top to trigger lazy loading of images
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # Try to find the main game image
        main_image_url = None
        
        # Debug: Print all image URLs on the page
        if debug:
            print("Debug: All image URLs on page:")
        all_images = driver.find_elements(By.TAG_NAME, "img")
        nintendo_images = []
        for i, img in enumerate(all_images[:30]):  # Show first 30 images
            src = img.get_attribute("src") or img.get_attribute("data-src")
            alt = img.get_attribute("alt") or ""
            if src:
                if debug:
                    print(f"  {i+1}. {src} (alt: {alt})")
                # Collect Nintendo images for later filtering
                if src and ("nintendo.com" in src or "atum-img" in src or "ncom/" in src):
                    if "t.co" not in src and "twitter.com" not in src and "facebook.com" not in src:
                        nintendo_images.append((src, alt))
        
        # Filter out small images and look for the largest Nintendo image
        if nintendo_images:
            if debug:
                print(f"Found {len(nintendo_images)} Nintendo images. Looking for the largest one...")
            largest_image = None
            largest_size = 0
            
            for src, alt in nintendo_images:
                # Look for size indicators in the URL
                size_match = re.search(r'[w,h]_(\d+)', src)
                if size_match:
                    size = int(size_match.group(1))
                    if size > largest_size and size > 100:  # Ignore very small images
                        largest_size = size
                        largest_image = src
                        if debug:
                            print(f"  Found larger image: {src} (size: {size})")
            
            # If we found a large image, use it
            if largest_image:
                main_image_url = largest_image
                if debug:
                    print(f"Selected largest image: {main_image_url}")
        
        # If we still haven't found a good image, look for specific patterns
        if not main_image_url:
            # Approach 1: Look for common image selectors with strict Nintendo URL filtering
            img_selectors = [
                "img[src*='ncom/software']",
                "img[data-src*='ncom/software']",
                "img[src*='atum-img']",
                "img[data-src*='atum-img']",
                "img[class*='product'][class*='image']",
                "img[class*='hero']",
                ".product-gallery img",
                ".product-image img",
                ".image-container img"
            ]
            
            for selector in img_selectors:
                try:
                    img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if img_elements:
                        # Get the first valid Nintendo image (avoid tracking URLs)
                        for img in img_elements:
                            src = img.get_attribute("src") or img.get_attribute("data-src")
                            if src and ("nintendo.com" in src or "ncom/software" in src or "atum-img" in src):
                                # Make sure it's not a tracking URL
                                if "t.co" not in src and "twitter.com" not in src and "facebook.com" not in src:
                                    main_image_url = src
                                    if debug:
                                        print(f"Found main image URL with selector '{selector}': {main_image_url}")
                                    break
                    if main_image_url:
                        break
                except:
                    continue
        
        # Approach 2: If still not found, look for any large Nintendo image
        if not main_image_url:
            img_elements = driver.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src and ("nintendo.com" in src or "ncom/software" in src or "atum-img" in src):
                    # Make sure it's not a tracking URL
                    if "t.co" not in src and "twitter.com" not in src and "facebook.com" not in src:
                        # Check if it looks like a main product image
                        if "656" in src or "1024" in src or "product" in src.lower() or "hero" in src.lower():
                            main_image_url = src
                            if debug:
                                print(f"Found main image URL: {main_image_url}")
                            break
        
        # If we still haven't found an image, try to get any product image with stricter filtering
        if not main_image_url:
            if debug:
                print("Trying alternative approach to find product image...")
            # Look for any image in product-related containers
            container_selectors = [
                "[class*='product']",
                "[class*='game']",
                "[data-testid*='product']",
                ".product-detail",
                ".game-detail"
            ]
            
            for selector in container_selectors:
                try:
                    containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    for container in containers:
                        img_elements = container.find_elements(By.TAG_NAME, "img")
                        for img in img_elements:
                            src = img.get_attribute("src") or img.get_attribute("data-src")
                            if src and ("nintendo" in src.lower() or "atum-img" in src):
                                # Make sure it's not a tracking URL
                                if "t.co" not in src and "twitter.com" not in src and "facebook.com" not in src:
                                    main_image_url = src
                                    if debug:
                                        print(f"Found main image in container '{selector}': {main_image_url}")
                                    break
                        if main_image_url:
                            break
                    if main_image_url:
                        break
                except:
                    continue
        
        # If we still haven't found an image, try to find the hero image specifically
        if not main_image_url:
            if debug:
                print("Trying to find hero image...")
            # Look for hero images specifically
            hero_selectors = [
                "[class*='hero'] img",
                "[data-testid*='hero'] img",
                ".hero-image img",
                ".primary-image img"
            ]
            
            for selector in hero_selectors:
                try:
                    img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in img_elements:
                        src = img.get_attribute("src") or img.get_attribute("data-src")
                        if src and ("nintendo" in src.lower() or "atum-img" in src):
                            # Make sure it's not a tracking URL
                            if "t.co" not in src and "twitter.com" not in src and "facebook.com" not in src:
                                main_image_url = src
                                if debug:
                                    print(f"Found hero image with selector '{selector}': {main_image_url}")
                                break
                    if main_image_url:
                        break
                except:
                    continue
        
        # If we still haven't found an image, try to get the first large Nintendo image
        if not main_image_url:
            if debug:
                print("Trying to find any large Nintendo image...")
            for src, alt in nintendo_images:
                # Look for images that are likely to be the main product image
                if "1024" in src or "656" in src or "hero" in src.lower() or "product" in src.lower():
                    main_image_url = src
                    if debug:
                        print(f"Found large Nintendo image: {main_image_url}")
                    break
        
        # If we still haven't found an image, try to get the first Nintendo image that's not a tiny icon
        if not main_image_url and nintendo_images:
            if debug:
                print("Selecting first non-icon Nintendo image...")
            for src, alt in nintendo_images:
                # Skip tiny icons
                if "24" not in src and "16" not in src:
                    main_image_url = src
                    if debug:
                        print(f"Selected non-icon Nintendo image: {main_image_url}")
                    break
        
        return main_image_url
        
    except Exception as e:
        print(f"Error extracting main image: {e}")
        return None

def get_high_res_url(image_url, width=1920):
    """Convert image URL to higher resolution version"""
    # For Nintendo images, we can often increase the width parameter
    if "w_" in image_url:
        # Replace width parameter with higher value
        high_res_url = re.sub(r'w_\d+', f'w_{width}', image_url)
        return high_res_url
    elif "c_scale" in image_url:
        # Add or modify width parameter for Cloudinary images
        if "w_" not in image_url:
            # Insert width parameter
            high_res_url = re.sub(r'(c_scale)', rf'c_scale,w_{width}', image_url)
            return high_res_url
        else:
            # Replace existing width parameter
            high_res_url = re.sub(r'w_\d+', f'w_{width}', image_url)
            return high_res_url
    else:
        # For other URLs, try appending width parameter
        return image_url

def download_image(image_url, filename, debug=False):
    """Download an image from URL and save to file"""
    try:
        if debug:
            print(f"Downloading image: {image_url}")
        # Clean up the URL if needed
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        elif image_url.startswith("/"):
            image_url = "https://www.nintendo.com" + image_url
            
        response = requests.get(image_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        if debug:
            print(f"Saved image to: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def main(game_name, output_dir="images", auto_select=False, debug=False):
    """Main function to scrape images for a game"""
    # Create output directories
    square_dir = os.path.join(output_dir, "square")
    main_dir = os.path.join(output_dir, "main")
    
    for directory in [square_dir, main_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Set up the driver
    driver = setup_driver()
    if not driver:
        return None
    
    try:
        # Search for the game
        results = search_nintendo_store(driver, game_name, debug=debug)
        
        if not results:
            print("No search results found")
            return None
        
        # Choose result
        if auto_select or len(results) == 1:
            selected_result = results[0]
            print(f"Selected: {selected_result['title']}")
        else:
            selected_result = display_search_results(results)
            if not selected_result:
                print("No result selected, exiting.")
                return None
        
        game_link = selected_result['link']
        square_image_url = selected_result['image_url']
        
        # Clean filename
        clean_name = re.sub(r'[^\w\s-]', '', game_name).strip().lower().replace(' ', '_')
        
        # Save square image
        if square_image_url:
            square_filename = os.path.join(square_dir, f"{clean_name}_square.jpg")
            download_image(square_image_url, square_filename, debug=debug)
        else:
            print("No square image found")
        
        # Try to get main image URL from search results first
        main_image_url = selected_result.get('main_image_url')
        
        # If not available in search results, get from game page
        if not main_image_url:
            main_image_url = get_game_page_images(driver, game_link, debug=debug)
        
        if main_image_url:
            clean_name = re.sub(r'[^\w\s-]', '', game_name).strip().lower().replace(' ', '_')
            main_filename = os.path.join(main_dir, f"{clean_name}_main.jpg")
            
            # Try to get higher resolution version
            high_res_url = get_high_res_url(main_image_url, 1920)
            if debug:
                print(f"Attempting to download high-res image: {high_res_url}")
            
            # Try high-res version first
            if download_image(high_res_url, main_filename, debug=debug):
                if debug:
                    print("Successfully downloaded high-res image")
            else:
                # Fall back to original resolution
                if debug:
                    print("Failed to download high-res image, trying original resolution")
                download_image(main_image_url, main_filename, debug=debug)
        else:
            print("No main image found")
        
        print("Scraping completed!")
        return clean_name
        
    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape images from Nintendo US store")
    parser.add_argument("game_name", help="Name of the game to search for")
    parser.add_argument("--output", "-o", default="images", help="Output directory for images")
    parser.add_argument("--auto", "-a", action="store_true", help="Automatically select first result without prompting")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    main(args.game_name, args.output, args.auto, args.debug)