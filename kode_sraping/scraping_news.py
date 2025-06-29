import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"  # Ganti dengan URI MongoDB Anda jika berbeda
DATABASE_NAME = "cnbc_scraping"
COLLECTION_NAME = "news_articles" # Dikembalikan ke nama koleksi awal

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}

# Fungsi ambil isi artikel
def get_article_content(link):
    """
    Mengambil konten artikel dari sebuah tautan.
    Args:
        link (str): URL artikel.
    Returns:
        str: Isi artikel dalam bentuk teks.
    """
    try:
        res = requests.get(link, headers=headers)
        res.raise_for_status() # Menambahkan raise_for_status untuk penanganan error HTTP
        soup = BeautifulSoup(res.text, 'lxml')
        div_content = soup.find('div', class_='detail-text')
        if div_content:  # Check if div_content is found
            paragraphs = div_content.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return content
        else:
            print(f"Content div not found for article: {link}")
            return ''
    except requests.exceptions.RequestException as e: # Menambahkan penanganan error spesifik untuk requests
        print(f"Error fetching article content from {link}: {e}")
        return ''
    except Exception as e:
        print(f"Error artikel: {link} | {e}")
        return ''

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Step 1: Ambil halaman list judul artikel pertama untuk mencari total jumlah halaman (multiple page)
# Menggunakan URL dari file .ipynb yang diberikan
url_first = 'https://www.cnbcindonesia.com/search?query=pemerintah+indonesia&page=1&fromdate=2024/01/01&todate=2025/06/21'
print(f"Mengakses halaman pertama untuk mencari total halaman: {url_first}")
try:
    res_first = requests.get(url_first, headers=headers)
    res_first.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    soup_first = BeautifulSoup(res_first.text, 'lxml')
except requests.exceptions.RequestException as e:
    print(f"Gagal mengakses halaman pertama: {e}")
    # Exit or handle the error appropriately if the first page cannot be accessed
    exit()

# Cari angka halaman terbesar
page_numbers = []
# Find all <a> tags that might contain page numbers
for a in soup_first.find_all('a'):
    try:
        # Attempt to convert the text to an integer
        num = int(a.text.strip())
        page_numbers.append(num)
    except ValueError:
        # Ignore if it's not a valid number
        continue
    except AttributeError:
        # Ignore if a.text is None
        continue

last_page = 1 # Default to 1 if no page numbers are found
if page_numbers:
    last_page = max(page_numbers)

print(f"🔎 Total halaman ditemukan {last_page}")

# Inisialisasi counter untuk jumlah data yang diperoleh
data_count = 0

# Step 2: Scraping dan simpan ke MongoDB
# Loop tiap halaman
for page in range(1, last_page + 1):
    print(f"\n📄 Scraping halaman {page}...")
    # Menggunakan URL dari file .ipynb yang diberikan
    # Note: The original code had different date ranges in url_first and url.
    # I'm keeping the date range from the loop URL as per the user's original code.
    url = f'https://www.cnbcindonesia.com/search?query=pemerintah+indonesia&page={page}&fromdate=2024/03/01&todate=2025/04/30'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(res.text, 'lxml')
        articles = soup.find_all('article')

        if not articles:
            print(f"Tidak ada artikel ditemukan di halaman {page}. Mungkin sudah mencapai akhir hasil atau ada masalah dengan struktur halaman.")
            break # Exit the loop if no articles are found, assuming it's the end

        for art in articles:
            try:
                a_tag = art.find('a')
                if not a_tag:
                    print(f"Tag <a> tidak ditemukan dalam artikel di halaman {page}. Melewatkan.")
                    continue

                title_tag = a_tag.find('h2')
                if not title_tag:
                    print(f"Tag <h2> untuk judul tidak ditemukan dalam artikel di halaman {page}. Melewatkan.")
                    continue
                title = title_tag.text.strip()
                link = a_tag['href']

                # Get the last span tag for time info
                time_spans = a_tag.find_all('span')
                time_info = time_spans[-1].text.strip() if time_spans else "N/A"

                content = get_article_content(link)

                # Prepare data as a dictionary
                article_data = {
                    "title": title,
                    "link": link,
                    "time": time_info,
                    "content": content,
                    "Label": 1  # Menambahkan objek JSON "Label": 1
                }

                # --- START: Kode penanganan duplikat ditambahkan di sini ---
                # Check if the article already exists to prevent duplicates
                # Using 'link' as a unique identifier
                if collection.count_documents({"link": link}) == 0:
                    collection.insert_one(article_data)
                    print(f"✅ {title}")
                    data_count += 1  # Tambahkan jumlah data
                else:
                    print(f"[!] Artikel sudah ada (link: {link}). Melewatkan.")
                # --- END: Kode penanganan duplikat ---

                time.sleep(1) # Jeda untuk menghindari pemblokiran
            except Exception as e:
                print(f"Error parsing artikel di halaman {page}: {e}")
                continue

        # Jeda antar halaman agar tidak diblokir
        time.sleep(2) # Increased sleep time between pages
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengakses halaman {page}: {e}")
        print("Mencoba melanjutkan ke halaman berikutnya...")
        continue
    except Exception as e:
        print(f"Error tidak terduga saat memproses halaman {page}: {e}")
        continue

print(f"\nScraping selesai dan {data_count} data telah disimpan di MongoDB.")
client.close()  # Close the MongoDB connection
