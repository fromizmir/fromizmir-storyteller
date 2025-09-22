import streamlit as st
     import json
     import pyttsx3
     from transformers import pipeline
     import sqlite3
     import os

     # Veritabanı kurulumu
     conn = sqlite3.connect("results.db")
     c = conn.cursor()
     c.execute('''CREATE TABLE IF NOT EXISTS results (user_id TEXT, ders_id INTEGER, score INTEGER)''')
     conn.commit()

     # Dersleri yükle
     try:
         with open("dersler.json", "r") as f:
             dersler = json.load(f)
     except FileNotFoundError:
         st.error("dersler.json dosyası bulunamadı!")
         st.stop()

     st.title("Fromizmir AI Hikaye Anlatıcısı")
     st.write("İngilizce derslerden hikayeler üret, quiz çöz ve X'te paylaş! 🇬🇧")

     # Ders seçimi
     ders_options = {ders["title"]: ders for ders in dersler}
     selected_ders = st.selectbox("Bir İngilizce dersi seç:", list(ders_options.keys()))

     if st.button("Hikaye Üret"):
         ders = ders_options[selected_ders]
         ders_id = ders["id"]
         ders_summary = ders["summary"]

         # AI ile hikaye üret
         with st.spinner("Hikaye üretiliyor..."):
             generator = pipeline("text-generation", model="distilgpt2")
             prompt = f"A short English story based on {selected_ders}: {ders_summary}"
             hikaye = generator(prompt, max_length=100, num_return_sequences=1)[0]["generated_text"]
         st.subheader("Hikaye")
         st.write(hikaye)

         # Seslendirme
         with st.spinner("Seslendirme hazırlanıyor..."):
             engine = pyttsx3.init()
             engine.setProperty("voice", "english")  # İngilizce ses
             audio_file = "story.mp3"
             engine.save_to_file(hikaye, audio_file)
             engine.runAndWait()
         if os.path.exists(audio_file):
             st.audio(audio_file)
         else:
             st.warning("Ses dosyası oluşturulamadı.")

         # Quiz
         st.subheader("Quiz")
         quizler = {
             "Present Simple": {
                 "soru": "What is the correct form? She ___ (go) to school every day.",
                 "cevaplar": ["go", "goes", "going", "went"],
                 "doğru_cevap": "goes"
             },
             "Past Simple": {
                 "soru": "What is the past form of 'eat'?",
                 "cevaplar": ["eated", "ate", "eaten", "eating"],
                 "doğru_cevap": "ate"
             },
             "English Idioms": {
                 "soru": "What does 'break the ice' mean?",
                 "cevaplar": ["To start a conversation", "To argue", "To leave", "To cook"],
                 "doğru_cevap": "To start a conversation"
             },
             "Modal Verbs": {
                 "soru": "Which modal verb shows obligation?",
                 "cevaplar": ["Can", "Might", "Must", "Could"],
                 "doğru_cevap": "Must"
             },
             "Vocabulary": {
                 "soru": "What does 'journey' mean?",
                 "cevaplar": ["A short walk", "A trip or travel", "A job", "A book"],
                 "doğru_cevap": "A trip or travel"
             },
             "Conditional Sentences": {
                 "soru": "Complete: If I ___ (study), I will pass.",
                 "cevaplar": ["study", "studied", "studies", "studying"],
                 "doğru_cevap": "study"
             },
             "Articles": {
                 "soru": "Which article fits? ___ apple is red.",
                 "cevaplar": ["A", "An", "The", "No article"],
                 "doğru_cevap": "An"
             },
             "Adjectives and Adverbs": {
                 "soru": "Choose the adverb: She sings ___.",
                 "cevaplar": ["beautiful", "beauty", "beautifully", "beautify"],
                 "doğru_cevap": "beautifully"
             },
             "Passive Voice": {
                 "soru": "Active to passive: They build houses → Houses ___ .",
                 "cevaplar": ["are built", "build", "were building", "built"],
                 "doğru_cevap": "are built"
             },
             "Questions": {
                 "soru": "Which is a correct question?",
                 "cevaplar": ["Where you live?", "Where do you live?", "You live where?", "Live you where?"],
                 "doğru_cevap": "Where do you live?"
             }
         }
         quiz = quizler.get(selected_ders, {
             "soru": f"Define a term from {selected_ders}.",
             "cevaplar": ["Answer A", "Answer B", "Answer C", "Answer D"],
             "doğru_cevap": "Answer A"
         })
         cevap = st.radio(quiz["soru"], quiz["cevaplar"])
         if st.button("Cevabı Kontrol Et"):
             score = 1 if cevap == quiz["doğru_cevap"] else 0
             c.execute("INSERT INTO results (user_id, ders_id, score) VALUES (?, ?, ?)", ("user1", ders_id, score))
             conn.commit()
             st.write(f"Doğru cevap: {quiz['doğru_cevap']}. Puanın: {score}")

         # X paylaşımı (dummy buton)
         st.button("X'te Paylaş", help="Hikayeni X'te paylaş!")

     conn.close()
