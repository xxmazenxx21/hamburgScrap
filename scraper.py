import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import os

# Configuration
BASE_URL = "https://homborg.nl/voorraad/generatoren-nieuw"
OUTPUT_FILE = "generators_data.json"
WAIT_TIME = 10

class GeneratorScraper:
    def __init__(self):
        self.driver = None
        self.products = []
        self.wait = None

    def setup_driver(self):
        """Initialize the Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        # Uncomment the line below if you want headless mode
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, WAIT_TIME)

    def extract_price(self, price_text):
        """Extract price from text"""
        if not price_text:
            return None
        # Remove € and clean up
        cleaned = price_text.replace('€', '').replace(',-', '').strip()
        return cleaned if cleaned else None

    def scrape_product_details(self, product_url):
        """Scrape details from individual product page"""
        try:
            self.driver.get(product_url)
            time.sleep(2)
            
            details = {}
            images = []
            pdf_url = None

            # Extract table data
            try:
                table_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in table_rows:
                    try:
                        th = row.find_element(By.TAG_NAME, "th").text
                        td = row.find_element(By.TAG_NAME, "td").text
                        if th and td:
                            details[th.strip()] = td.strip()
                    except NoSuchElementException:
                        continue
            except Exception as e:
                print(f"Error extracting table data: {e}")

            # Extract images
            try:
                image_links = self.driver.find_elements(By.CSS_SELECTOR, "div.main ul li a")
                for link in image_links:
                    try:
                        img = link.find_element(By.TAG_NAME, "img")
                        src = img.get_attribute("src")
                        if src and "customerimg" in src:
                            # Get the full resolution URL by replacing w parameter
                            full_url = src.split("?w=")[0] + "?w=1024"
                            images.append(full_url)
                    except NoSuchElementException:
                        continue
            except Exception as e:
                print(f"Error extracting images: {e}")

            # Extract PDF
            try:
                pdf_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
                pdf_url = pdf_link.get_attribute("href")
            except NoSuchElementException:
                pdf_url = None
            except Exception as e:
                print(f"Error extracting PDF: {e}")

            # Extract description
            description = None
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, "div.descriptions div.blob")
                description = desc_elem.text
            except NoSuchElementException:
                description = None
            except Exception as e:
                print(f"Error extracting description: {e}")

            # Extract video URL
            video_url = None
            try:
                video_div = self.driver.find_element(By.CSS_SELECTOR, "div.video")
                iframe = video_div.find_element(By.CSS_SELECTOR, "iframe.youtubeframe")
                video_url = iframe.get_attribute("src")
            except NoSuchElementException:
                video_url = None
            except Exception as e:
                print(f"Error extracting video: {e}")
            
            # Add video URL to details
            details["vediourl"] = video_url

            return {
                "details": details,
                "images": list(set(images)),  # Remove duplicates
                "pdf": pdf_url,
                "description": description
            }

        except Exception as e:
            print(f"Error scraping product details from {product_url}: {e}")
            return {
                "details": {},
                "images": [],
                "pdf": None,
                "description": None
            }

    def extract_all_urls_from_page(self):
        """Extract all product URLs from current listing page"""
        urls = []
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.vehicle")
            print(f"Found {len(product_cards)} products on current page")
            
            for card in product_cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a")
                    product_url = link.get_attribute("href")
                    if product_url:
                        urls.append(product_url)
                except NoSuchElementException:
                    continue
        except Exception as e:
            print(f"Error extracting URLs: {e}")
        
        return urls

    def scrape_listing_page(self):
        """Scrape all products from listing page"""
        try:
            current_url = BASE_URL
            page_num = 1
            
            while current_url:
                try:
                    print(f"\n=== Scraping Page {page_num}: {current_url} ===")
                    self.driver.get(current_url)
                    time.sleep(3)

                    # Wait for products to load
                    self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.vehicle")))
                    time.sleep(2)

                    # Extract all URLs from current page first (to avoid stale elements)
                    product_urls = self.extract_all_urls_from_page()
                    
                    # Now process each URL
                    for idx, product_url in enumerate(product_urls):
                        try:
                            print(f"\n[{idx + 1}/{len(product_urls)}] Processing: {product_url}")
                            detailed_data = self.scrape_product_details(product_url)
                            
                            # Extract basic info from detail page
                            details = detailed_data.get("details", {})
                            
                            # Try to get title from details or use URL
                            title = details.get("Title") or details.get("Titel")
                            if not title:
                                title = product_url.split("/")[-1].replace("-", " ").title()
                            
                            # Extract from details
                            stock_number = details.get("Stocknumber") or details.get("Stock number")
                            year = details.get("Bouwjaar") or details.get("Year")
                            
                            # Get price from details
                            price = None
                            for key in details.keys():
                                if "prijs" in key.lower() or "price" in key.lower():
                                    price = self.extract_price(details[key])
                                    break
                            
                            images = detailed_data.get("images", [])
                            pdf_url = detailed_data.get("pdf")
                            description = detailed_data.get("description")
                            
                            # Get thumbnail image from detail page
                            image_url = None
                            if images:
                                image_url = images[0]

                            # Compile product data
                            product_data = {
                                "name": title or None,
                                "stock": stock_number or None,
                                "price": price or None,
                                "year": year or None,
                                "image": image_url or None,
                                "url": product_url,
                                "details": details or {},
                                "images": images or [],
                                "pdf": pdf_url or None,
                                "description": description or None
                            }

                            self.products.append(product_data)
                            print(f"✓ Scraped product {len(self.products)}: {title}")
                            
                            # Save incrementally after each product to prevent data loss
                            self.save_to_json()

                        except Exception as e:
                            print(f"Error processing product {product_url}: {e}")
                            continue

                    # Check for next page - look for it on the current listing page
                    next_url = None
                    try:
                        # Go back to the listing page to find next button
                        self.driver.get(current_url)
                        time.sleep(3)
                        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.vehicle")))
                        time.sleep(1)
                        
                        # Try to find next button
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, "li.next a")
                            next_url = next_button.get_attribute("href")
                        except NoSuchElementException:
                            next_url = None
                        
                        if next_url:
                            print(f"\n>>> Moving to next page")
                            page_num += 1
                            current_url = next_url
                        else:
                            print("\n>>> No more pages to scrape")
                            current_url = None
                    except Exception as e:
                        print(f"Error checking for next page: {e}")
                        current_url = None

                except TimeoutException:
                    print("Timeout waiting for products to load")
                    break

        except Exception as e:
            print(f"Error scraping listing page: {e}")

    def save_to_json(self):
        """Save scraped data to JSON file"""
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            print(f"\n✓ Data saved to {OUTPUT_FILE}")
            print(f"Total products scraped: {len(self.products)}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def run(self):
        """Run the scraper"""
        try:
            print("Starting Generator Scraper...")
            self.setup_driver()
            self.scrape_listing_page()
            self.save_to_json()
            print(f"\n✓ Scraping completed! Total products: {len(self.products)}")
        except KeyboardInterrupt:
            print("\n\n!!! Scraping interrupted by user !!!")
            print(f"Saving {len(self.products)} products scraped so far...")
            self.save_to_json()
        except Exception as e:
            print(f"Fatal error: {e}")
            print(f"Saving {len(self.products)} products scraped so far...")
            self.save_to_json()
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")

if __name__ == "__main__":
    scraper = GeneratorScraper()
    scraper.run()
