# Görüntü Şifreleme Sistemi

Bu proje, matris analizi temelli bir görüntü şifreleme ve çözme uygulamasıdır.  
Uygulama, Streamlit arayüzü üzerinden kullanıcıdan alınan görüntüyü şifreler ve doğru anahtar ile tekrar çözer.

## Kullanılan Yöntemler
- Permütasyon matrisi (piksel konumlarını karıştırma)
- Block scrambling (blok bazlı karıştırma)
- XOR tabanlı diffusion (piksel değerlerini değiştirme)

## Kullanılan Teknolojiler
- Python
- Streamlit
- NumPy
- Pillow

## Uygulamayı Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
