# Autism Brain 🧩

自閉症譜系障礙（ASD）文獻每日自動追蹤系統。

每天自動從 PubMed 抓取最新自閉症相關文獻，由 NVIDIA Nemotron 進行摘要分析，生成繁體中文日報，部署於 GitHub Pages。

## 架構

- **資料來源**：PubMed E-utilities API
- **分析模型**：NVIDIA Nemotron 3 Super（fallback: Nemotron 3 Nano）
- **排程**：GitHub Actions（每天台北時間 00:00）
- **部署**：GitHub Pages

## 線上閱讀

👉 [https://u8901006.github.io/autism-brain/](https://u8901006.github.io/autism-brain/)

## 相關連結

- [李政洋身心診所](https://www.leepsyclinic.com/)
- [訂閱電子報](https://blog.leepsyclinic.com/)
- [Psychiatry Brain（精神醫學文獻日報）](https://u8901006.github.io/Psychiatry-brain/)
