# flutter-docs-rag

Flutter dokümanı üzerinde, Türkçe ve İngilizce soru alan, kaynak gösteren bir RAG sistemi. Asıl amaç sistemin kendisi değil, **ne kadar iyi çalıştığını ölçmek**: 80 soruluk bir altın set, sayfa bazlı arama metrikleri, LLM-judge ve hata analizi.

![Ablation](docs/ablation.png)

| Config | Ne ekliyor | Hit@5 | MRR | tr Hit@5 |
|---|---|---|---|---|
| r0 | sabit boyutlu chunk, MiniLM | 0.723 | 0.654 | 0.200 |
| r1 | başlık bazlı chunk | 0.815 | 0.658 | 0.400 |
| r2a | bge-small embedding | 0.862 | 0.767 | 0.400 |
| r3 | + BM25 ve RRF (hibrit) | 0.862 | 0.731 | 0.600 |
| r4 | + sorgu yeniden yazma (r3 üstüne) | 0.862 | 0.714 | 0.900 |
| r4v | yeniden yazma, hibritsiz (r2a üstüne) | 0.877 | 0.742 | 0.900 |
| r5 | + LLM rerank (r4v üstüne) | 0.892 | 0.754 | 0.900 |
| r6 | yalnız BM25 (vektör yok) | 0.708 | 0.577 | 0.700 |
| r7 | BM25 + yeniden yazma (canlı site) | 0.846 | 0.701 | 0.800 |

Retrieval 65 cevaplanabilir soru üzerinde, sayfa URL'si düzeyinde ölçülür. Tüm tablolar: [docs/EVAL.md](docs/EVAL.md).

Tam hat (cevap + judge, Groq modelleri, 80 soru):

| | r0 | r4v |
|---|---|---|
| Cevaplanan oranı | 0.80 | 0.91 |
| Red doğruluğu | 0.838 | 0.925 |
| Kaynak doğruluğu | 0.885 | 0.915 |
| Accuracy (cevaplananlarda, 1-5) | 4.46 | 4.56 |
| Faithfulness (cevaplananlarda, 1-5) | 4.90 | 4.92 |
| Gecikme (ms/soru) | 1022 | 1384 |
| LLM çağrısı/soru | 1.0 | 1.9 |

## Ne öğrendim

- **Türkçe en büyük kazancı verdi.** İngilizce embedding ile Türkçe soru: Hit@5 0.20. Sorguyu İngilizce arama metnine çeviren yeniden yazma adımıyla 0.90. Genel Hit@5 ise yalnızca 0.862'den 0.877'ye çıktı.
- **Hibrit arama net kazanç getirmedi** (r3): Hit@5 aynı, MRR düştü. Türkçede yardımcı oldu (0.40 → 0.60), ama yeniden yazma bunun üstünü zaten sağladı.
- **Rerank maliyetine değmedi.** r5, r4v'ye göre 1 soruluk ek isabet için gecikmeyi 707 ms'den 8448 ms'ye çıkardı (yerel model ile).
- **Hataların çoğu aramada değil, parça sınırlarında ve soru kapsamında.** Aşağıya bak.

## Nasıl ölçtüm

- **Altın set:** 80 soru. 40 tek sayfalı, 15 çok sayfalı, 10 Türkçe, 15 kapsam dışı (cevap dokümanda yok, sistem reddetmeli).
- **İlgi tanımı sayfa URL'sidir**, chunk içinde anahtar kelime geçmesi değil. Aynı kelime alakasız bir sayfada da geçebilir. Metrikler (Hit@5, Recall@5, MRR, nDCG@5) sayfa bazında hesaplanır, aynı sayfanın tekrar eden chunk'ları önce tekilleştirilir. Metrik fonksiyonlarını kendim yazdım (RAGAS gibi kütüphane kullanmadım): öğrenmek için.
- **Cevap kalitesi** iki ayrı puanla ölçülür: *accuracy* (referans cevapla uyum) ve *faithfulness* (cevap verilen pasajlarla destekleniyor mu). Model pasajlarda olmayan doğru bir şey söyleyebilir; ikisi bu yüzden ayrı.
- **Model rolleri:** yeniden yazma ve rerank `openai/gpt-oss-20b`, cevap `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b` (cevabı yazandan farklı aile). Hepsi Groq'da, seed 42.
- **Judge kalibrasyonu:** 20 cevap (6'sı düşük puanlı olacak şekilde örneklendi) judge'ın puanı görülmeden puanlandı. Accuracy'de tam uyum %85, en fazla 1 puan fark %100. Faithfulness'ta tam uyum %60, en fazla 1 puan fark %95, judge ortalama **+0.45 daha cömert**. Eşik (en fazla 1 puan farkta %70) ikisinde de geçildi. **Puanlamayı insan değil, Claude yaptı**; bu bir insan kalibrasyonu değil, ikinci bir LLM ile çapraz kontrol.

## Hata analizi (r4v, 80 soruda 11 başarısız)

Başarısız = arama metriği 0, accuracy ≤ 2, cevaplanabilir soruya ret, ya da kapsam dışına cevap.

| Neden | Adet |
|---|---|
| Chunking (doğru sayfa geldi, cevabın parçası top-5'e girmedi) | 3 |
| Belirsiz altın set (gelen sayfa da soruyu cevaplıyor) | 2 |
| Çok sayfalı sorunun yalnız bir kısmı bulundu | 2 |
| Sıralama, anlamsal boşluk, kayıplı yeniden yazma, yanlış ret | 1'er |

Nedenlerin her biri tek satır olarak [eval/error_labels-r4v.csv](eval/error_labels-r4v.csv) içinde. **Etiketleri LLM yazdı**; q017 ve q026 chunking etiketi doğrulanmadı (judge gerekçesine dayanıyor). 11 başarısızlık küçük bir sayı, yüzdeleri güçlü istatistik sayma.

Başlangıç config'i r0'da 21 başarısızlık vardı; İngilizce kaçırmaların hepsinde beklenen sayfa ilk 28 içindeydi (sıralama sorunu), Türkçe kaçırmaların 5'i ilk 50'de bile yoktu (dil boşluğu).

## Canlı sürüm neden vektörsüz (r7)

Canlı sitede en iyi config (r4v) çalışmıyor: sorgu embedding'i için `sentence-transformers` ve `torch` gerekir, bunlar sunucusuz ortama sığmaz. Gemini embedding'i de denenemedi (r2b, faturalandırma). Bu yüzden canlı site **r7** kullanır: yeniden yazma (Groq) + BM25, vektör yok. Ödediği bedel ölçüldü: Hit@5 0.877 yerine 0.846, MRR 0.742 yerine 0.701 (iki ölçüm de aynı 65 soruda, ancak r4v retrieval tablosu yerel `llama3.2` ile, r7 Groq ile ölçüldü, birebir kıyaslanmaz). Yalnız BM25 (r6, yeniden yazmasız) 0.708'de kalıyor; yeniden yazma Hit@5'e +0.14 ekliyor: çok sayfalı sorularda 0.53 → 0.93, Türkçede 0.70 → 0.80, tek sayfalılarda 0.78 → 0.83. Türkçe BM25 skoru şaşırtıcı derecede yüksek; Türkçe sorularda geçen `Row`, `Expanded` gibi kod adları İngilizce dokümanla birebir eşleşiyor, bu yüzden bu, genel Türkçe başarısı sayılmamalı.

## Neden vektör veritabanı yok

453 sayfa, başlık bazlı chunk'larla 4376 parça eder. 4376 x 384 (bge-small) bir float16 matris 3.4 MB'tır, belleğe sığar ve tek matris çarpımıyla benzerlik hesabı çok kısa sürer; Chroma, pgvector gibi çözümler bu ölçekte gereksiz bir parça olurdu. Yaklaşık 100 bin chunk üstüne çıkınca veya doküman sık güncellenmeye başlayınca bir vektör veritabanına geçerdim. Chroma'yı kurstan biliyorum, tercih ölçekle ilgili.

## Bilinen sınırlar

- 80 soru küçük bir set; iki config arasındaki 1-2 puanlık fark anlamlı değil. Çoğu retrieval farkı (örneğin r4v ile r5) bu sınırın altında.
- Altın set bir LLM tarafından hazırlandı, betikle doğrulandı (sayfa gerçekten var mı, beklenen URL doküman setinde mi). Elle denetim sınırlı. 12 soru sayfa başlıklarına yakın yazıldığı için arama skorları iyimser olabilir. Birkaç tek sayfalı soru (q018, q019, q030, q033, q048) birden fazla sayfaya uyabilir.
- Judge bir LLM; yukarıdaki kalibrasyon insanla değil Claude ile yapıldı ve judge faithfulness'ta cömert (+0.45). Kalibrasyon örneği düşük puanlıları fazla temsil ediyor.
- Retrieval tablosundaki r4, r4v, r5 (yeniden yazma, rerank) **yerel `llama3.2`** ile ölçüldü, tam hat tablosu ise Groq modelleriyle. İkisi aynı ölçüm değil: yerel model İngilizce sorularda anahtar kelimeleri düşürüyordu (Hit@5 0.95 → 0.85), Groq modeliyle bu bozulma yok (tek sayfalı İngilizce sorular Hit@5 0.95). Bu yüzden r4v'nin Hit@5'i iki yerde farklı (0.877 / 0.938).
- Accuracy ve faithfulness yalnız cevaplanan sorularda hesaplanır; ret edilen sorular bu ortalamaya girmez. Türkçe accuracy 4.8, ancak n=10.
- **Gemini embedding (r2b) ölçülmedi**: ücretsiz katmanın günlük sınırına takıldı ve faturalandırma gerektirdi, denenemedi.
- Doküman belirli bir commit'e sabit (aşağıda); sonradan değişen sayfalar yansımaz. Sürüm notları (`release/`) indekste yok.
- Gecikme sütunu r0, r1, r3, r4 için boş: bu ölçümler gecikme kaydı eklenmeden önce alındı.

## Çalıştırma

```bash
uv sync
uv run python -m rag.ingest                      # data/pages.jsonl (bkz. data/SOURCE.md)
uv run python -m rag.index r4v                   # indeks
uv run python -m eval.run --config r4v --stage retrieval
uv run python -m eval.run --config r4v --stage full --provider groq   # GROQ_API_KEY gerekir
uv run python -m eval.report                     # docs/EVAL.md ve grafik
uv run pytest
```

API anahtarları `.env` içinde durur, repoda yoktur.

## Kaynak ve lisans

İçerik: [docs.flutter.dev](https://docs.flutter.dev), CC BY 3.0; kod örnekleri BSD. Veri `flutter/website` deposunun `c1acb419c3c2b43be543d7c2eb0de0a6ba0e153b` commit'idir (2026-11-23), ayrıntı [data/SOURCE.md](data/SOURCE.md). Her cevap kaynak sayfa linkini gösterir.
