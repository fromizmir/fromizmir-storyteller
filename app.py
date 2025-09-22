import streamlit as st
import json
from transformers import pipeline
import os
import tempfile
import time
import re
import gtts  # Google Text-to-Speech
from io import BytesIO

# Streamlit config
st.set_page_config(page_title="Fromizmir AI Hikaye", layout="wide")

# CSS stili
st.markdown("""
<style>
    .hikaye-metin {
        font-size: 16px;
        line-height: 1.6;
        color: #2c3e50;
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Dersleri yükle
try:
    with open("dersler.json", "r") as f:
        dersler = json.load(f)
except FileNotFoundError:
    st.error("dersler.json bulunamadı!")
    st.stop()

# Ana sayfa
st.title("📖 Fromizmir AI Hikaye Anlatıcısı")
st.markdown("**İngilizce derslerden AI hikayeleri dinle** 🇬🇧")

# Sidebar - Ders seçimi
st.sidebar.header("📚 Ders Seç")
ders_options = {ders["title"]: ders for ders in dersler}
selected_ders = st.sidebar.selectbox("Ders:", list(ders_options.keys()))

# Ana içerik
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎭 AI Hikaye")
    
    # Hikaye üretme butonu
    if st.button("✨ Hikaye Üret", use_container_width=True, type="primary"):
        with st.spinner("🤖 AI hikaye üretiyor..."):
            # Model yükle (cache'li)
            if 'generator' not in st.session_state:
                st.session_state.generator = pipeline("text-generation", model="distilgpt2")
            
            generator = st.session_state.generator
            ders = ders_options[selected_ders]
            
            # Prompt
            prompt = f"""Write an engaging 130-160 word English learning story about {selected_ders}. 
            Include practical examples of {ders['summary']}. Create characters, a simple plot, 
            and use the grammar/vocabulary naturally. Make it educational and fun.

            Title: A Lesson in {selected_ders}
            
            Story:"""
            
            # Hikaye üret
            result = generator(
                prompt, 
                max_new_tokens=140,
                min_new_tokens=100,
                temperature=0.85,
                top_p=0.9,
                do_sample=True,
                num_return_sequences=1,
                pad_token_id=generator.tokenizer.eos_token_id,
                eos_token_id=generator.tokenizer.eos_token_id,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3
            )[0]["generated_text"]
            
            # Temizle
            hikaye = result.replace(prompt, "").strip()
            hikaye = re.sub(r'\n\s*\n', '\n\n', hikaye)
            hikaye = re.sub(r'[ \t]+', ' ', hikaye)
            
            # Kelime kontrolü
            words = hikaye.split()
            kelime_sayisi = len(words)
            
            if kelime_sayisi < 80:
                result2 = generator(prompt, max_new_tokens=160, temperature=0.8)[0]["generated_text"]
                hikaye = result2.replace(prompt, "").strip()
                words = hikaye.split()
                kelime_sayisi = len(words)
            
            if kelime_sayisi > 170:
                words = words[:155]
                hikaye = ' '.join(words)
                kelime_sayisi = 155
            
            if hikaye:
                hikaye = hikaye[0].upper() + hikaye[1:]
            
            # Session state
            st.session_state.current_hikaye = {
                "text": hikaye,
                "ders": selected_ders,
                "kelime": kelime_sayisi,
                "timestamp": time.time()
            }
        
        st.success(f"✅ Hikaye üretildi! ({kelime_sayisi} kelime)")
    
    # HİKAYE GÖSTER
    if 'current_hikaye' in st.session_state:
        hikaye_data = st.session_state.current_hikaye
        
        st.markdown(f"### 📚 {hikaye_data['ders']}")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("📝 Kelime", hikaye_data['kelime'])
        with col_info2:
            st.metric("⏱️ Üretim", f"{time.time() - hikaye_data['timestamp']:.0f}s")
        
        st.markdown("---")
        
        # HİKAYE - GÜZEL KUTU
        st.markdown('<div class="hikaye-metin">', unsafe_allow_html=True)
        st.markdown("**Hikaye:**")
        st.write(hikaye_data["text"])
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

# SAĞ TARAFTA SES - gTTS İLE
with col2:
    st.header("🔊 Ses Kontrolü")
    
    if 'current_hikaye' in st.session_state:
        hikaye_data = st.session_state.current_hikaye
        st.success(f"✅ Hazır ({hikaye_data['kelime']} kelime)")
        
        # YENİ HİKAYE
        if st.button("🔄 Yeni", use_container_width=True, type="secondary"):
            if 'current_hikaye' in st.session_state:
                del st.session_state.current_hikaye
            st.rerun()
        
        st.markdown("---")
        
        # gTTS SESLENDİRME - %100 ÇALIŞIR!
        if st.button("🎵 Dinle", use_container_width=True, type="primary"):
            hikaye_metni = st.session_state.current_hikaye["text"]
            
            if len(hikaye_metni.split()) < 10:
                st.error("❌ Hikaye çok kısa!")
            else:
                with st.spinner("🎤 Google ses hazırlanıyor..."):
                    try:
                        # gTTS ile MP3 oluştur
                        tts = gtts.gTTS(text=hikaye_metni, lang='en', slow=False)
                        
                        # BytesIO ile hafızada tut
                        audio_buffer = BytesIO()
                        tts.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)
                        
                        # Streamlit'te çal
                        st.audio(audio_buffer, format="audio/mp3")
                        
                        # Dosya boyutu bilgisi
                        audio_size = len(audio_buffer.getvalue())
                        st.success(f"✅ Ses hazır: {audio_size//1000}KB")
                        
                        # Buffer'ı temizle
                        audio_buffer.close()
                        
                    except Exception as e:
                        st.error(f"🔇 Ses hatası: {str(e)}")
                        st.info("İnternet bağlantınızı kontrol edin.")
    else:
        st.info("ℹ️ Önce hikaye üretin!")
        
        # HIZLI gTTS TESTİ
        if st.button("🔊 Ses Testi", use_container_width=True):
            try:
                test_text = f"Merhaba! {selected_ders} dersi için Google ses sistemi hazır."
                tts = gtts.gTTS(text=test_text, lang='en')
                
                audio_buffer = BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                
                st.audio(audio_buffer, format="audio/mp3")
                st.success("✅ Google ses çalışıyor!")
                st.balloons()
                
                audio_buffer.close()
                
            except Exception as e:
                st.error(f"❌ Test hatası: {str(e)}")
                st.info("İnternet gerekli! `pip install gtts` kurun.")

# Footer
st.markdown("---")
st.markdown("*AI ile özgün hikayeler* | *Google seslendirme* | *130-160 kelime*")
