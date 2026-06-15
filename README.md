# Image Encryption System

This project is an image encryption and decryption application based on matrix analysis.
The application encrypts an image uploaded by the user through a Streamlit interface and decrypts it again using the correct key.

## Kullanılan Yöntemler
- Permutation matrix (shuffling pixel positions)
- Block scrambling (block-based shuffling)
- XOR-based diffusion (modifying pixel values)

## Technologies Used
- Python
- Streamlit
- NumPy
- Pillow

## Running the Application

```bash
pip install -r requirements.txt
streamlit run app.py
