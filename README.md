Berikut Model Mesin Translasi untuk 10 bahasa daerah di indonesia beserta bahasa nasional (bahasa indonesia) dan bahasa internasional (bahasa inggris)

tujuan dari pembuatan model ini adalah untuk:
1.Memperkuat pemahaman materi dan praktek Machine Translasi NLP
2.Mengatasi permasalahan dalam berinteraksi terutama karena adanya Gap bahasa (perbedaan bahasa lokal yang digunakan)
3.Turut melestarikan keragaman Bahasa Lokal Indonesia

Model ini kita buat dengan mengacu pada paper yang berjudul : 
"**NusaX: Multilingual Parallel Sentiment Dataset for 10 Indonesian Local Languages**
sekilas tentang paper:
paper ini disubmit pada tahun 2023, hasil kolaborasi berbagai pihak kampus ternama di dunia NLP  (Bloomberg, MBZUAI, HKUST, Universitas Indonesia, INACL, The University of Melbourne, Telkom University, Kanda University of International Studies, University of Zurich) 
dan beberapa perusahaan dan startup AI (Google Research, Kata.ai)
penulis : Genta Indra Winata, Alham Fikri Aji, Samuel Cahyawijaya, Rahmad Mahendra, Fajri Koto, Ade Romadhony, Kemal Kurniawan, David Moeljadi, Radityo Eko Prasojo, Pascale Fung, Timothy Baldwin, Jey Han Lau, Rico Sennrich, Sebastian Ruder

paper ini membahas 2 tugas utama NLP, yaitu sentimen analisis dan machine translasi.
pada kesempatan kali ini kami mencoba membuat machine translasi berdasarkan data dan insight dari paper ini, yang kami coba sendiri dengan menggunakan pre-Trained Model T5 small

berikut alur kerja notebook ini:
1. install & import Library yg diperlukan untuk machine translasi
2. tentukan dan install matriks evaluasi yang dipakai
3. petakan bahasa lokal apa saja yang ingin dibuat mesin translasinya (12 bahasa)
4. Load data dari "indonlp/NusaX-MT"
5. Lakukan Exploratory Data Analyst untuk memahami pola dan insight data Nusa X
   - data ini terdiri dari total 132.000 baris (50% data Train,10% data validation dan 40% data test),masing-masing bahasa ada 1000 row data
   - jumlah kata dalam kalimat secara umum adalah berkisar 20-32 kata dalam satu baris, dengan kalimat terpanjang adalah sebanyak 107 kata dari bahasa inggris, sedangkan secara umum kalimat terpanjang pada semua bahasa daerah indonesia adalah sepanjang 70-80an kata
   - kata yang paling banyak muncul di setiap bahasa umumnya termasuk kata hubung tempat,waktu, dan artikel. kata ini tidak kita hapus dari dataset karena memiliki makna dalam tugas mesin translasi(berbeda dengan tugas sentimen analisis)
6. Lakukan Data Pre-Processing
7. kita gabung dan susun ulang porsi data train,validation, dan data test,menjadi 80:10:10.
8. cek distribusi data (cek Keseimbangan data tiap bahasa)
9.  Buat dan Load Tokenizer. dalam kesempatan ini kami menggunakan T5 Tokenizer
    kita menggunkan Tokenizer transformer dengan padding berdasarkan max_lengt sebesar 300 kata, dengan parameter hasil tensornya PyTorch
10. khusus untuk bahasa (sunda & jawa) sebelum model dilatih dengan T5 small,kita unsupervised learning dahulu dengan data bahasa sunda-jawa dari data set CC100,@300k rows)
11. lakukan metrix evaluasi untuk machine translasi(Bleu score, Meteor,dan Bleurt Score)
12. Terakhir, lakukan Predict Hasil Terjemahan, dan bandingkan dengan target, apakah dapat dimengerti manusia
