import json
import os
from pymongo import MongoClient
import pandas as pd

# Konfigurasi MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "cnbc_scraping"
COLLECTION_NAME = "news_articles"
OUTPUT_DIR = "data/raw/"

# Membuat direktori jika belum ada
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Koneksi ke MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Mengambil semua data dari koleksi
data = list(collection.find())
# Mengonversi data ke DataFrame
df = pd.DataFrame(data)
# Menyimpan data ke file CSV
df.to_csv(os.path.join(OUTPUT_DIR, "news_articles2.csv"), index=False)
print(f"Data berhasil diekspor ke {OUTPUT_DIR}news_articles.csv")
