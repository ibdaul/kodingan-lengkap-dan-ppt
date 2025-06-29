import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
import re # Import regex module

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "cnbc_scraping"
COLLECTION_NAME = "news_articles" # New collection name for TurnBackHoax

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
# Tambahan fungsi ambil isi hoaks
def ambil_konten_hoaks(link):
    try:
        res = requests.get(link, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        blockquote = soup.find('blockquote')
        if blockquote:
            paragraphs = blockquote.find_all('p')
            konten = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return konten
        return ""
    except Exception as e:
        print(f"[!] Gagal ambil konten hoaks dari {link}: {e}")
        return ""


# Base URL for TurnBackHoax, pages are like /page/1/, /page/2/, etc.
BASE_URL = 'https://turnbackhoax.id/page/'

# Step 1: Find the last page number
print("Mengakses halaman pertama untuk mencari total halaman...")
last_page = 1
try:
    res_first = requests.get(f'{BASE_URL}1/', headers=headers)
    res_first.raise_for_status()
    soup_first = BeautifulSoup(res_first.text, 'lxml')

    # Look for pagination links, typically within a <ul> with a specific class or directly accessible <a> tags
    # This might need adjustment based on the actual HTML structure of TurnBackHoax's pagination
    pagination_links = soup_first.find_all('a', class_='page-numbers') # Common class for pagination links
    if pagination_links:
        # Get the text of each link and try to convert to int, then find the maximum
        page_numbers = []
        for link in pagination_links:
            try:
                # Exclude 'Next' or 'Previous' text, focus on numbers
                if link.text.isdigit():
                    page_numbers.append(int(link.text))
            except ValueError:
                pass
        if page_numbers:
            last_page = max(page_numbers)
        else:
            # Fallback if specific page-numbers class isn't found or doesn't contain numbers
            # Sometimes the last page is explicitly marked, or we can look for "last page" button
            # Let's try to find 'current' page and 'total' pages
            current_page_span = soup_first.find('span', class_='page-numbers current')
            if current_page_span:
                try:
                    last_page_from_text = re.search(r'of (\d+)', current_page_span.text)
                    if last_page_from_text:
                        last_page = int(last_page_from_text.group(1))
                except AttributeError:
                    pass

except requests.exceptions.RequestException as e:
    print(f"Gagal mengakses halaman pertama: {e}")
    print("Mencoba melanjutkan dengan asumsi hanya ada satu halaman.")
    # Proceed with last_page = 1 if initial access fails
except Exception as e:
    print(f"Error saat mencari total halaman: {e}")
    print("Mencoba melanjutkan dengan asumsi hanya ada satu halaman.")


print(f"🔎 Total halaman ditemukan: {last_page}")

# Inisialisasi counter untuk jumlah data yang diperoleh
data_count = 0
# Ubah di sini jika ingin mulai dari halaman tertentu
start_page = 375

# Step 2: Scraping and saving to MongoDB
for page in range(start_page, last_page + 1):
    print(f"\n📄 Scraping halaman {page}...")
    url = f'{BASE_URL}{page}/'
    ...

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        # Find all article tags
        articles = soup.find_all('article')

        if not articles:
            print(f"Tidak ada artikel ditemukan di halaman {page}. Mungkin sudah mencapai akhir hasil atau ada masalah dengan struktur halaman.")
            break

        for art in articles:
            try:
                title_tag = art.find('h3', class_='entry-title mh-loop-title')
                link_tag = art.find('a')
                time_tag = art.find('span', class_='mh-meta-date updated')
    

                title = ""
                link = ""
                time_info = "0" # Default to "0" if not found
                content = ""

                if title_tag:
                    raw_title = title_tag.text.strip()
                    # Remove content within square brackets, e.g., [HOAX], [FITNAH]
                    title = re.sub(r'\[.*?\]\s*', '', raw_title).strip()
                else:
                    print(f"Judul tidak ditemukan untuk artikel di halaman {page}. Melewatkan.")
                    continue

                if link_tag and 'href' in link_tag.attrs:
                    link = link_tag['href']
                else:
                    print(f"Link tidak ditemukan untuk artikel di halaman {page}. Melewatkan.")
                    continue

                if time_tag:
                    time_info = time_tag.text.strip()
                
                # TurnBackHoax articles don't typically have a separate 'content' div directly
                # on the search results page. If you need full article content,
                # a separate function similar to get_article_content would be needed
                # to visit each article link, but for now, we only extract what's on
                # the article list page as per your request.
                
                # Prepare data as a dictionary
                hoax_content = ambil_konten_hoaks(link)
                article_data = {
                    "title": title,
                    "link": link,
                    "time_info": time_info,
                     "hoax_content": hoax_content,
                    "Label": 0 # Adding the specified JSON object
                }

                # Check for duplicates before inserting
                if collection.count_documents({"link": link}) == 0:
                    collection.insert_one(article_data)
                    print(f"✅ {title}")
                    data_count += 1
                else:
                    print(f"[!] Artikel sudah ada (link: {link}). Melewatkan.")

                time.sleep(1) # Jeda untuk menghindari pemblokiran
            except Exception as e:
                print(f"Error parsing artikel di halaman {page}: {e}")
                continue

        time.sleep(2) # Jeda antar halaman
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengakses halaman {page}: {e}")
        print("Mencoba melanjutkan ke halaman berikutnya...")
        continue
    except Exception as e:
        print(f"Error tidak terduga saat memproses halaman {page}: {e}")
        continue

print(f"\nScraping selesai dan {data_count} data telah disimpan di MongoDB.")
client.close()