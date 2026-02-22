# Image-metadata-extractor
📸 Image Metadata Extractor API
Sebuah API berbasis Python Flask yang dirancang untuk mengekstraksi metadata mendalam dari gambar, melakukan analisis forensik sederhana untuk mendeteksi manipulasi perangkat lunak, serta mengidentifikasi asal foto (apakah berasal dari kamera asli atau platform media sosial).

---

## 🚀 Fitur Utama
 * Ekstraksi EXIF Lengkap: Mengambil data teknis seperti model kamera (Make/Model), resolusi, tipe file, dan waktu pengambilan foto.
 * Geolokasi Precision: Mengonversi koordinat GPS mentah dari metadata menjadi format desimal (latitude & longitude) yang siap digunakan untuk mapping (Google Maps, dsb).
 * Deteksi Media Sosial: Algoritma heuristik untuk mendeteksi jejak digital dari platform seperti Instagram, Facebook, WhatsApp, dan TikTok melalui analisis profil warna ICC dan pembersihan EXIF.
 * Analisis Forensik Perangkat Lunak: Mendeteksi penggunaan aplikasi pengeditan seperti Adobe Photoshop, Lightroom, Canva, PicsArt, dan Snapseed.
 * Optimasi Memori: Menggunakan sistem context manager untuk memastikan file sementara dihapus segera setelah diproses, menjaga penyimpanan server tetap bersih.
🛠️ Arsitektur Teknologi
 * Framework: Flask (Pure API Mode)
 * Image Processing: Pillow (PIL)
 * Metadata Handling: Piexif
 * Security: Werkzeug (Secure Filename Handling)
📥 Instalasi
 * Clone Repositori:
   ```git clone https://github.com/Lilith-VnK/Image-metadata-extractor/```
   
 * Masuk direktori
   ```cd image-metadata-extractor```

 * Instal Dependensi:
   ```pip install flask pillow piexif werkzeug```

 * Jalankan Aplikasi:
   ```
   python Image_extractor.py
   ```
   
---

## 🧪Cara Penggunaan
Endpoint Utama
 * URL: /extract
 * Method: POST
 * Payload: multipart/form-data
 * Key: image (File)
Contoh Request (cURL)
```
curl -X POST -F "image=@foto_test.jpg" http://127.0.0.1:5000/extract
```

Contoh Respons JSON
```
{
  "analysis": {
    "detected_origins": ["meta_icc_profile"],
    "is_modified": true,
    "software_detected": ["adobe photoshop 2024"]
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
 * Akurasi PNG: File PNG secara standar tidak menyimpan metadata EXIF selengkap JPEG. API akan menandai PNG sebagai "stripped" karena ketiadaan data sensor kamera primer.
 * Keamanan: API membatasi ukuran unggahan maksimal sebesar 20MB untuk mencegah serangan Denial of Service (DoS).

## 🤝 Kontribusi
Kontribusi selalu terbuka! Silakan lakukan fork pada repositori ini dan kirimkan pull request untuk fitur-fitur baru seperti deteksi deepfake atau integrasi API Reverse Image Searching
