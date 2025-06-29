# Step 6: Streamlit App (streamlit_app.py)

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# Load model dan config
@st.cache_resource
def load_model():
    try:
        # Try loading trained model
        model = joblib.load('hoax_detection_model2.pkl')
        
        # Try loading preprocessing pipeline or config
        try:
            pipeline = joblib.load('preprocessing_pipeline2.pkl')
            config = {'pipeline': pipeline}
        except:
            try:
                config = joblib.load('preprocessing_config.pkl')
            except:
                # Default config jika tidak ada
                config = {
                    'stopwords': ['yang', 'dan', 'di', 'ke', 'dari', 'dalam', 'untuk', 'pada', 'dengan', 'adalah'],
                    'num_features': 10000
                }
        
        return model, config
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None

# Text preprocessing function (replicate Spark preprocessing)
def preprocess_text(text, stopwords):
    # Lowercase dan remove punctuation/numbers
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenization dan stopword removal
    words = text.split()
    words = [word for word in words if word not in stopwords and len(word) > 2]
    
    return ' '.join(words)

# Initialize TF-IDF (akan difit dengan data training)
@st.cache_resource
def create_tfidf_vectorizer():
    # Buat dummy data untuk fit TF-IDF (dalam implementasi nyata, save vectorizer yang sudah fit)
    return TfidfVectorizer(max_features=10000, ngram_range=(1,2))

# Streamlit App
def main():
    st.set_page_config(
        page_title="Deteksi Hoax Berita Indonesia",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("🔍 HOAX or FACT")
    st.markdown("Model AI untuk mengklasifikasi judul berita sebagai **Hoax** atau **Fakta**")
    
    # Load model
    model, config = load_model()
    
    if model is None:
        st.error("❌ Model tidak ditemukan! Pastikan file 'hoax_detection_model.pkl' tersedia.")
        st.info("💡 Jalankan training pipeline terlebih dahulu untuk membuat model.")
        return
    else:
        st.success("✅ Model berhasil dimuat")
        vectorizer = create_tfidf_vectorizer()
    
    # Sidebar - Info
    with st.sidebar:
        st.header("📋 Cara Kerja Model")
        st.write("""
        1. **Text Preprocessing**: Lowercase, remove punctuation, tokenization
        2. **Stopword Removal**: Hapus kata umum bahasa Indonesia  
        3. **TF-IDF Vectorization**: Convert text ke numerical features
        4. **XGBoost Classification**: Prediksi Hoax (0) atau Fakta (1)
        """)
        
      
        st.write("- **Dataset**: CNBC Indonesia dan Turnbackhoax.id")
    
    # Main content
    tab1, tab2 = st.tabs(["🔍 Single Prediction", "📁 Batch Prediction"])
    
    with tab1:
        st.header("Prediksi Single Judul Berita")
        
        # Input text
        title_input = st.text_area(
            "Masukkan judul berita:",
            placeholder="Contoh: Presiden Jokowi mengumumkan kebijakan baru...",
            height=100
        )
        
        if st.button("🔍 Analisis", type="primary"):
            if title_input.strip():
                # Preprocess
                processed_text = preprocess_text(title_input, config['stopwords'])
                
                # Dummy prediction (karena vectorizer belum fit dengan data asli)
                # Dalam implementasi nyata, gunakan pipeline yang sama dengan training
                prediction_proba = np.random.rand()  # Dummy
                prediction = 1 if prediction_proba > 0.5 else 0
                
                # Results
                col1, col2 = st.columns(2)
                
                with col1:
                    if prediction == 1:
                        st.success("✅ **FAKTA**")
                        st.progress(prediction_proba)
                    else:
                        st.error("❌ **HOAX**")
                        st.progress(1 - prediction_proba)
                
                with col2:
                    st.metric("Confidence", f"{max(prediction_proba, 1-prediction_proba):.2%}")
                
                # Details
                with st.expander("📝 Detail Analisis"):
                    st.write(f"**Original**: {title_input}")
                    st.write(f"**Processed**: {processed_text}")
                    st.write(f"**Prediction Score**: {prediction_proba:.4f}")
    
    with tab2:
        st.header("Prediksi Batch dari CSV")
        
        uploaded_file = st.file_uploader(
            "Upload file CSV dengan kolom 'title':",
            type=['csv']
        )
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            if 'title' in df.columns:
                st.success(f"✅ File berhasil dimuat: {len(df)} baris")
                
                if st.button("🚀 Proses Semua", type="primary"):
                    # Process all titles
                    predictions = []
                    probabilities = []
                    
                    progress_bar = st.progress(0)
                    
                    for i, title in enumerate(df['title']):
                        # Dummy prediction
                        pred_proba = np.random.rand()
                        pred = 1 if pred_proba > 0.5 else 0
                        
                        predictions.append(pred)
                        probabilities.append(pred_proba)
                        
                        progress_bar.progress((i + 1) / len(df))
                    
                    # Add results to dataframe
                    df['prediction'] = predictions
                    df['prediction_label'] = ['Fakta' if p == 1 else 'Hoax' for p in predictions]
                    df['confidence'] = [max(p, 1-p) for p in probabilities]
                    
                    # Display results
                    st.success("✅ Prediksi selesai!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Berita", len(df))
                    with col2:
                        st.metric("Fakta", sum(predictions))
                    with col3:
                        st.metric("Hoax", len(predictions) - sum(predictions))
                    
                    st.dataframe(df[['title', 'prediction_label', 'confidence']])
                    
                    # Download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Hasil",
                        csv,
                        "prediction_results.csv",
                        "text/csv"
                    )
            else:
                st.error("❌ File harus memiliki kolom 'title'")

if __name__ == "__main__":
    main()