# Generator Scraper

A Python Selenium-based web scraper for extracting generator product data from https://homborg.nl/voorraad/generatoren-nieuw

## Features

- Scrapes all 98+ generator products across multiple pages
- Extracts product card info: name, price, stock number, year, image
- Clicks into each product detail page to collect:
  - Detailed specifications (category, fuel, voltage, condition, etc.)
  - All product images (high resolution)
  - PDF brochure link
  - Product description
- Handles missing fields gracefully (null/empty values)
- Saves all data to `generators_data.json`
- Automatic pagination handling

## Installation

1. **Install Python** (3.7+)

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Download ChromeDriver:**
   - Download from: https://chromedriver.chromium.org/
   - Or use webdriver-manager (automatically handled by the script)

## Usage

```bash
python scraper.py
```

The script will:
1. Open a Chrome browser (you'll see it running)
2. Navigate to the generators page
3. Extract product info from cards
4. Click each product to get detailed info
5. Collect images, PDFs, and specifications
6. Save everything to `generators_data.json`

## Output Format

The output JSON file contains an array of products:

```json
[
  {
    "name": "Scania EU Stage 5 Silent generatorsets ! Stage V",
    "stock": "0005294",
    "price": "1250",
    "year": "2023",
    "image": "https://customerimg-ed24.kxcdn.com/...",
    "url": "https://homborg.nl/voorraad/...",
    "details": {
      "Categorie": "Aggregaat",
      "Bouwjaar": "2023",
      "Stocknumber": "0005294",
      "Brandstof": "Diesel",
      "Voedingsspanning": "400 V",
      "Algemene staat": "Zeer goed",
      "Technische staat": "Zeer goed",
      "Optische staat": "Zeer goed"
    },
    "images": [
      "https://customerimg-ed24.kxcdn.com/34637989-1-...?w=1024",
      "https://customerimg-ed24.kxcdn.com/34637989-2-...?w=1024"
    ],
    "pdf": "https://homborg.nl/voorraad/34637989/...pdf",
    "description": "Nu beschikbaar !..."
  }
]
```

## Configuration

You can modify these settings in `scraper.py`:

- `BASE_URL`: The starting URL to scrape
- `OUTPUT_FILE`: JSON output filename
- `WAIT_TIME`: Selenium wait timeout in seconds (currently 10)

## Notes

- The script includes delays to be respectful to the server
- Empty/missing fields will be `null` in JSON
- Images are automatically deduplicated
- The browser window will remain visible so you can monitor progress
- To run in headless mode, uncomment the line in `setup_driver()` method

## Troubleshooting

- **Chrome not found**: Install Chrome or download ChromeDriver matching your Chrome version
- **Timeout errors**: Increase `WAIT_TIME` variable
- **Stale element errors**: These are handled automatically and the scraper will skip and continue
- **Connection issues**: Check your internet connection and website availability
