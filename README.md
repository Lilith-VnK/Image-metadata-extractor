# Image Metadata Extractor (IME)
📸 **Image Metadata Extractor API** adalah REST API berbasis Flask yang dirancang untuk mengekstraksi metadata mendalam (EXIF) dari gambar, melakukan analisis statistik, serta memberikan indikasi kemungkinan manipulasi atau asal-usul gambar (kamera asli vs platform media sosial).

---

## 🚀 Fitur Utama
* **Ekstraksi EXIF Lengkap:** Mengambil data teknis seperti manufaktur kamera (`Make`), model (`Model`), resolusi, tipe file, dan timestamp pengambilan foto.
* **Geolokasi Precision:** Mengonversi koordinat GPS mentah dari metadata menjadi format desimal (*latitude* & *longitude*) yang siap digunakan untuk pemetaan.
* **Analisis Statistik Gambar:** Menghitung tingkat kecerahan (*brightness*) dan distribusi warna untuk memahami karakteristik visual gambar.
* **Deteksi Forensik Sederhana:** Mengidentifikasi indikasi *metadata stripping* dan penggunaan perangkat lunak pengeditan seperti Adobe Photoshop melalui tag EXIF.
* **REST API Ready:** Memberikan respon dalam format JSON yang bersih, memudahkan integrasi dengan aplikasi web atau mobile lainnya.
* **Ringan & Efisien:** Dibangun hanya menggunakan Pillow dan Piexif tanpa ketergantungan berat pada OpenCV.

---

## 🛠️ Arsitektur Teknologi
* **Language:** Python 3.10+
* **Framework:** Flask
* **Image Processing:** Pillow (PIL)
* **Metadata Handling:** Piexif
* **Security:** Werkzeug (Secure Filename Handling)

---

## 📥 Instalasi

> [!IMPORTANT]
> Pastikan Anda berada di branch `Lilith-VnK-patch-1` untuk mengakses file `app.py` yang berada di dalam folder `IME/`.

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/Lilith-VnK/IME.git
    cd IME
    ```

2.  **Checkout Branch:**
    ```bash
    git checkout Lilith-VnK-patch-1
    ```

3.  **Masuk ke Direktori Aplikasi:**
    ```bash
    cd IME
    ```
    *Struktur folder: `IME/IME/app.py`*

4.  **Install Dependensi:**
    ```bash
    pip install flask pillow piexif werkzeug
    ```

5.  **Jalankan Server:**
    ```bash
    python app.py
    ```
    Jika berhasil, API akan berjalan di: `http://127.0.0.1:5000`

---

## 🧪 Cara Penggunaan

### Endpoint Utama
* **URL:** `/extract`
* **Method:** `POST`
* **Payload:** `multipart/form-data`
* **Key:** `image` (File gambar: jpg, jpeg, png)

### Contoh Request (cURL)
```bash
curl -X POST -F "image=@foto_test.jpg" http://127.0.0.1:5000/extract
```

### Contoh Respons JSON
```json
{
  "analysis": {
    "is_modified": true,
    "software_detected": ["adobe photoshop"]
  },
  "format": "JPEG",
  "width": 1920,
  "height": 1080,
  "Make": "Canon",
  "Model": "EOS R5",
  "gps": {
    "latitude": -6.2088,
    "longitude": 106.8456
  }
}
```

---

## 📝 Catatan Teknis
* **Batas Unggahan:** Ukuran maksimal file adalah **20MB** untuk menjaga performa server.
* **Karakteristik Format:** File PNG secara standar tidak menyimpan metadata EXIF selengkap JPEG. API mungkin menandai PNG sebagai "stripped" karena ketiadaan data sensor kamera.
* **Heuristik:** Hasil analisis (seperti deteksi modifikasi) bersifat indikasi heuristik dan tidak dimaksudkan sebagai bukti forensik hukum yang absolut.

---

## 🤝 Kontribusi
Kontribusi selalu terbuka! Silakan fork repositori ini dan buat *pull request* untuk peningkatan seperti:
* Peningkatan akurasi algoritma deteksi manipulasi.
* Penambahan endpoint untuk pemrosesan batch.
* Integrasi deteksi profil warna ICC yang lebih mendalam.
