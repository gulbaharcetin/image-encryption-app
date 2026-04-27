import streamlit as st
import numpy as np
import hashlib
import secrets
from PIL import Image
import io


# ----------------------------
# Yardımcı Fonksiyonlar
# ----------------------------

def generate_key():
    return secrets.token_hex(16)


def key_to_seed(key):
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)


def image_to_gray_array(uploaded_file):
    img = Image.open(uploaded_file).convert("L")
    return np.array(img, dtype=np.uint8)


def array_to_png_bytes(arr):
    img = Image.fromarray(arr.astype(np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def parse_shape_from_filename(filename):
    """
    Dosya adı şu formatta olmalı:
    encrypted_HEIGHT_WIDTH.png
    Örnek:
    encrypted_640_960.png
    """
    try:
        name = filename.replace(".png", "")
        parts = name.split("_")
        height = int(parts[-2])
        width = int(parts[-1])
        return height, width
    except Exception:
        return None


# ----------------------------
# Şifreleme
# ----------------------------

def encrypt_image(gray, block_size=8):
    key = generate_key()
    seed = key_to_seed(key)
    rng = np.random.default_rng(seed)

    rows, cols = gray.shape

    h_new = (rows // block_size) * block_size
    w_new = (cols // block_size) * block_size

    gray_cropped = gray[:h_new, :w_new]

    row_perm = rng.permutation(h_new)
    col_perm = rng.permutation(w_new)

    permuted_img = gray_cropped[row_perm, :][:, col_perm]

    num_blocks_row = h_new // block_size
    num_blocks_col = w_new // block_size
    total_blocks = num_blocks_row * num_blocks_col

    blocks = []
    for i in range(num_blocks_row):
        for j in range(num_blocks_col):
            block = permuted_img[
                i * block_size:(i + 1) * block_size,
                j * block_size:(j + 1) * block_size
            ]
            blocks.append(block)

    block_perm = rng.permutation(total_blocks)
    shuffled_blocks = [blocks[i] for i in block_perm]

    scrambled_img = np.zeros_like(permuted_img)

    idx = 0
    for i in range(num_blocks_row):
        for j in range(num_blocks_col):
            scrambled_img[
                i * block_size:(i + 1) * block_size,
                j * block_size:(j + 1) * block_size
            ] = shuffled_blocks[idx]
            idx += 1

    keystream = rng.integers(0, 256, size=(h_new, w_new), dtype=np.uint8)
    encrypted_img = np.bitwise_xor(scrambled_img, keystream)

    original_shape = (h_new, w_new)

    return encrypted_img, key, original_shape


# ----------------------------
# Çözme
# ----------------------------

def decrypt_image(encrypted_img, key, original_shape, block_size=8):
    h_new, w_new = original_shape

    encrypted_img = encrypted_img[:h_new, :w_new]

    seed = key_to_seed(key)
    rng = np.random.default_rng(seed)

    row_perm = rng.permutation(h_new)
    col_perm = rng.permutation(w_new)

    num_blocks_row = h_new // block_size
    num_blocks_col = w_new // block_size
    total_blocks = num_blocks_row * num_blocks_col

    block_perm = rng.permutation(total_blocks)

    keystream = rng.integers(0, 256, size=(h_new, w_new), dtype=np.uint8)

    scrambled_img = np.bitwise_xor(encrypted_img, keystream)

    scrambled_blocks = []
    for i in range(num_blocks_row):
        for j in range(num_blocks_col):
            block = scrambled_img[
                i * block_size:(i + 1) * block_size,
                j * block_size:(j + 1) * block_size
            ]
            scrambled_blocks.append(block)

    original_blocks = [None] * total_blocks

    for new_pos, old_pos in enumerate(block_perm):
        original_blocks[old_pos] = scrambled_blocks[new_pos]

    descrambled_img = np.zeros((h_new, w_new), dtype=np.uint8)

    idx = 0
    for i in range(num_blocks_row):
        for j in range(num_blocks_col):
            descrambled_img[
                i * block_size:(i + 1) * block_size,
                j * block_size:(j + 1) * block_size
            ] = original_blocks[idx]
            idx += 1

    inv_row_perm = np.argsort(row_perm)
    inv_col_perm = np.argsort(col_perm)

    recovered_img = descrambled_img[inv_row_perm, :][:, inv_col_perm]

    return recovered_img


# ----------------------------
# Streamlit Arayüz
# ----------------------------

st.set_page_config(
    page_title="Görüntü Şifreleme Sistemi",
    layout="wide"
)

st.title("Görüntü Şifreleme ve Çözme Sistemi")
st.write("Permütasyon matrisi, block scrambling ve XOR tabanlı görüntü şifreleme uygulaması.")

tab1, tab2 = st.tabs(["Şifreleme", "Çözme"])


# ----------------------------
# TAB 1 - Şifreleme
# ----------------------------

with tab1:
    st.header("Görüntü Şifreleme")

    uploaded_encrypt = st.file_uploader(
        "Şifrelenecek görüntüyü yükleyin",
        type=["png", "jpg", "jpeg", "bmp"],
        key="encrypt_uploader"
    )

    if uploaded_encrypt is not None:
        gray = image_to_gray_array(uploaded_encrypt)

        st.subheader("Orijinal Görüntü")
        st.image(gray, caption="Orijinal Gri Görüntü", use_container_width=True)

        if st.button("Şifrele"):
            encrypted_img, key, original_shape = encrypt_image(gray)

            st.session_state["encrypted_img"] = encrypted_img
            st.session_state["key"] = key
            st.session_state["original_shape"] = original_shape

            height, width = original_shape

            st.subheader("Şifrelenmiş Görüntü")
            st.image(encrypted_img, caption="Şifreli Görüntü", use_container_width=True)

            st.success("Şifreleme tamamlandı.")

            st.write("Anahtar:")
            st.code(key, language="text")

            st.write("Orijinal boyut:")
            st.code(f"height={height}, width={width}", language="text")

            encrypted_png = array_to_png_bytes(encrypted_img)

            st.download_button(
                label="Şifreli Görüntüyü İndir",
                data=encrypted_png,
                file_name=f"encrypted_{height}_{width}.png",
                mime="image/png"
            )

            st.warning("Anahtarı kaybetmeyin. Çözme işlemi için gereklidir.")


# ----------------------------
# TAB 2 - Çözme
# ----------------------------

with tab2:
    st.header("Görüntü Çözme")

    decrypt_mode = st.radio(
        "Çözme yöntemi",
        [
            "Bu oturumdaki şifreli görüntüyü kullan",
            "Dosyadan şifreli görüntü yükle"
        ]
    )

    key_input = st.text_input("Anahtarı girin")

    if decrypt_mode == "Bu oturumdaki şifreli görüntüyü kullan":
        if "encrypted_img" in st.session_state and "original_shape" in st.session_state:
            if st.button("Çöz"):
                if not key_input:
                    st.error("Lütfen anahtarı girin.")
                else:
                    try:
                        encrypted_img = st.session_state["encrypted_img"]
                        original_shape = st.session_state["original_shape"]

                        recovered_img = decrypt_image(
                            encrypted_img,
                            key_input,
                            original_shape
                        )

                        st.subheader("Çözülmüş Görüntü")
                        st.image(recovered_img, caption="Çözülmüş Görüntü", use_container_width=True)

                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")
        else:
            st.info("Önce Şifreleme sekmesinde bir görüntü şifreleyin.")

    else:
        uploaded_decrypt = st.file_uploader(
            "Şifreli görüntüyü yükleyin",
            type=["png"],
            key="decrypt_uploader"
        )

        if uploaded_decrypt is not None:
            encrypted_uploaded = image_to_gray_array(uploaded_decrypt)

            st.subheader("Yüklenen Şifreli Görüntü")
            st.image(encrypted_uploaded, caption="Şifreli Görüntü", use_container_width=True)

            detected_shape = parse_shape_from_filename(uploaded_decrypt.name)

            if detected_shape is not None:
                height, width = detected_shape
                st.success(f"Boyut bilgisi dosya adından alındı: height={height}, width={width}")
            else:
                st.warning("Dosya adından boyut bilgisi okunamadı.")
                height = st.number_input("Orijinal yükseklik", min_value=1, step=1)
                width = st.number_input("Orijinal genişlik", min_value=1, step=1)

            if st.button("Yüklenen Görüntüyü Çöz"):
                if not key_input:
                    st.error("Lütfen anahtarı girin.")
                else:
                    try:
                        original_shape = (int(height), int(width))

                        recovered_img = decrypt_image(
                            encrypted_uploaded,
                            key_input,
                            original_shape
                        )

                        st.subheader("Çözülmüş Görüntü")
                        st.image(recovered_img, caption="Çözülmüş Görüntü", use_container_width=True)

                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")