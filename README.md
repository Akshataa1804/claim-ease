# ClaimGenius AI

ClaimEase is a GenAI-powered insurance claims assistant that automates the claim intake, document analysis, fraud detection, and settlement prediction process using natural language and uploaded files.

---

## 🚀 Features

* 🧠 Natural language claim processing via LLaMA 3 (Ollama)
* 📁 Upload & auto-analyze documents (PDFs, images, etc.)
* 🔍 Fraud risk assessment
* 💰 Settlement outcome prediction
* 🧾 Claim history & chat timeline
* 📊 Analytics dashboard

---

## 🛠️ Tech Stack

| Layer        | Tool/Framework               |
| ------------ | ---------------------------- |
| Frontend     | Streamlit                    |
| Backend      | Python (modular)             |
| GenAI Engine | Ollama (LLaMA 3)             |
| Document OCR | Custom (Tesseract / PyMuPDF) |
| Storage      | SQLite                       |

---

## 📂 Project Structure

```
claim-ease/
│
├── app.py                 # Core logic: analysis, follow-up, prediction
├── streamlit_ui.py        # Streamlit UI & interaction logic
├── document_processor.py  # OCR, entity extraction, classification
├── database.py            # SQLite functions for CRUD
├── requirements.txt
├── README.md
└── ...
```

---

## ⚙️ Setup Instructions

### ✅ Step 1: Install Ollama and download LLaMA 3

Follow official guide: [https://ollama.com](https://ollama.com)

```bash
ollama pull llama3
```

### ✅ Step 2: Clone Repo & Install Python Packages

```bash
git clone https://github.com/your-username/claimease.git
cd claimease
pip install -r requirements.txt
```

### ✅ Step 3: Run the App

```bash
streamlit run streamlit_ui.py
```

---

## 🔑 Key Components

### `analyze_claim()`

Uses a structured prompt to extract:

* Claimant info
* Incident summary
* Estimated loss
* Fraud score
* Recommended actions

### `generate_followup()`

Creates 2–3 questions to gather missing data or clarify input.

### `predict_settlement()`

Estimates settlement outcome and amount range using claim details.

---

## 📝 Sample Prompt Input

Paste the below text into the chat input of ClaimEase to analyze a sample claim:

```
My 2022 Honda Accord (VIN: 1HGCV1F12MA123456) was rear-ended while stopped at a red light on Main Street and 5th Avenue. The other driver (identified as Robert Johnson, driving a 2018 Toyota Camry) admitted fault at the scene. Police report #CR-2025-0615-789 was filed.

Damage includes:
- Severe rear bumper damage
- Trunk deformation
- Whiplash injury requiring chiropractic treatment

Estimated repair costs from authorized Honda dealer: $8,750
Medical expenses to date: $1,200

Supporting documents available:
- Police report
- Repair estimate
- Medical bills
- Photos of damage
```

---

## 👤 Author

**Akshata Khandekar**
Built for GenAI Hackathon 2025 🚀

---

## 📃 License

MIT License
