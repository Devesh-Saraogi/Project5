from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import time
import random
import requests
import os

class MyntraScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Firefox driver"""
        firefox_options = Options()
        if headless:
            firefox_options.add_argument('--headless')
        firefox_options.add_argument('--no-sandbox')
        firefox_options.add_argument('--disable-dev-shm-usage')
        firefox_options.set_preference('general.useragent.override', 
                                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0')
        
        # Auto-download and setup GeckoDriver
        service = Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=firefox_options)
        self.driver.maximize_window()
        
    def scroll_page(self, scroll_step=500, scroll_pause=1.5, max_scrolls=20):
        """Scroll page gradually to load dynamic content - only scrolls incrementally"""
        print(f"Starting scrolling (step={scroll_step}px, pause={scroll_pause}s, max={max_scrolls})...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls:
            # Current position
            current_pos = self.driver.execute_script("return window.pageYOffset")
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down by specified pixels
            self.driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            time.sleep(scroll_pause)
            
            # Check if we've reached near the bottom (within scroll_step pixels)
            new_pos = self.driver.execute_script("return window.pageYOffset")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height > last_height:
                print(f"  Scroll {scroll_count + 1}: New content loaded (height: {new_height}px)")
                last_height = new_height
                no_change_count = 0
            else:
                no_change_count += 1
            
            # Stop if we're at the bottom and no new content for 3 checks
            if (new_pos + viewport_height >= new_height - 100) and no_change_count >= 3:
                print("  Reached end of page - no more content loading")
                break
            
            scroll_count += 1
        
        print(f"Scrolling complete! Total scrolls: {scroll_count}")
            
    def scrape_images(self, url, max_items=50, scroll_step=500, scroll_pause=1.5, max_scrolls=20):
        """Scrape product images from Myntra
        
        Args:
            url: URL to scrape
            max_items: Maximum number of products to extract
            scroll_step: Pixels to scroll per step (default: 500)
            scroll_pause: Seconds to wait between scrolls (default: 1.5)
            max_scrolls: Maximum number of scroll attempts (default: 20)
        """
        print(f"Navigating to: {url}")
        self.driver.get(url)
        
        # Wait for initial page load
        time.sleep(random.uniform(3, 5))
        
        # Scroll to load more products
        print("Scrolling to load products...")
        self.scroll_page(scroll_step=scroll_step, scroll_pause=scroll_pause, max_scrolls=max_scrolls)
        
        # Find all product images
        print("Extracting image URLs...")
        images = []
        
        try:
            # Wait for product list to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-base"))
            )
            
            # Find all product containers
            products = self.driver.find_elements(By.CLASS_NAME, "product-base")
            print(f"Found {len(products)} products")
            
            for idx, product in enumerate(products[:max_items]):
                try:
                    # Find image within product
                    img_element = product.find_element(By.TAG_NAME, "img")
                    img_url = img_element.get_attribute("src")
                    
                    # Get product details
                    try:
                        brand = product.find_element(By.CLASS_NAME, "product-brand").text
                        product_name = product.find_element(By.CLASS_NAME, "product-product").text
                    except:
                        brand = f"product_{idx}"
                        product_name = ""
                    
                    if img_url:
                        images.append({
                            'url': img_url,
                            'brand': brand,
                            'name': product_name,
                            'index': idx
                        })
                        print(f"[{idx+1}] {brand} - {img_url[:60]}...")
                    
                    # Random delay between processing items
                    time.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    print(f"Error extracting image from product {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error finding products: {e}")
        
        return images
    
    def download_images(self, images, output_dir="myntra_images"):
        """Download images to local directory"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"\nDownloading {len(images)} images to {output_dir}/")
        
        for img_data in images:
            try:
                # Clean filename
                filename = f"{img_data['index']}_{img_data['brand'].replace(' ', '_')}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                # Download with delay
                time.sleep(random.uniform(1, 2))
                
                response = requests.get(img_data['url'], stream=True)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    print(f"Downloaded: {filename}")
                else:
                    print(f"Failed to download {filename}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"Error downloading {img_data['url']}: {e}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()


# Usage example
if __name__ == "__main__":
    #url = "https://www.myntra.com/men-casual-shirts"
    url = "https://www.myntra.com/men-sweatshirts"
    
    # Scrolling parameters - ADJUST THESE FOR TRIAL AND ERROR
    SCROLL_STEP = 500       # Pixels to scroll each time (300-800 works well)
    SCROLL_PAUSE = 2.0      # Seconds between scrolls (1-3 recommended)
    MAX_SCROLLS = 25        # Maximum scroll attempts (increase for more products)
    MAX_ITEMS = 100         # Maximum products to extract
    
    scraper = MyntraScraper(headless=False)  # Set to True for headless mode
    
    try:
        # Scrape images with custom scroll settings
        images = scraper.scrape_images(
            url, 
            max_items=MAX_ITEMS,
            scroll_step=SCROLL_STEP,
            scroll_pause=SCROLL_PAUSE,
            max_scrolls=MAX_SCROLLS
        )
        
        print(f"\n{'='*60}")
        print(f"Successfully scraped {len(images)} images")
        print(f"{'='*60}")
        
        # Show sample of scraped URLs
        if images:
            print("\nSample image URLs:")
            for img in images[:3]:
                print(f"  - {img['brand']}: {img['url'][:70]}...")
        
        # Download images (optional)
        if images:
            download = input("\nDo you want to download the images? (y/n): ").strip().lower()
            if download == 'y':
                output_dir = "myntra_images"
                scraper.download_images(images, output_dir=output_dir)
                print(f"\n✓ Images saved to: {os.path.abspath(output_dir)}")
            else:
                print("\nDownload skipped. Image URLs have been scraped only.")
        else:
            print("\nNo images found to download.")
            
    finally:
        scraper.close()
        print("\nScraper closed successfully")