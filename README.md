# Payment Investigation System

An AI-assisted finance operations system that investigates payment lifecycle anomalies, groups related exceptions into investigations, and provides evidence-backed root-cause analysis.

## 🚀 Live Demo

**Streamlit App:**  
https://payment-investigation-system-uwcnzdu7ithqojpd3egqls.streamlit.app/

## 💻 GitHub Repository

https://github.com/karthikmanchala23-cell/payment-investigation-system

---

## 🎯 Problem

Finance and payment operations teams often receive exceptions from different stages of the payment lifecycle.

A single underlying issue can create multiple downstream exceptions across payments, refunds, settlements, and finance records.

Traditional reconciliation systems often report these exceptions individually, which can make investigation slow and difficult.

The goal of this project is to move from simply detecting mismatches to investigating related financial exceptions as connected cases.

---

## 💡 Solution

The Payment Investigation System analyzes a synthetic payment lifecycle:

**Orders → Payments → Refunds → Settlements → Finance Records**

The system:

1. Loads and validates financial records.
2. Detects objective anomalies using deterministic rules.
3. Connects related anomalies through shared transaction identifiers.
4. Groups related anomalies into investigations.
5. Builds an evidence chain for each investigation.
6. Uses Gemini for advisory root-cause analysis.
7. Sends uncertain or consequential cases for human review.
8. Records investigation activity in an audit trail.
9. Evaluates detection performance against known ground-truth anomalies.

---

## 🏦 Razorpay AI Finance Controller Track

This project is designed for the **AI Finance Controller** track.

The system processes a synthetic batch of financial records and reports:

- Records processed
- Detected anomalies
- Investigation groups
- Detection performance
- Correctly detected issues
- False positives
- False negatives
- Unresolved exceptions
- Evidence supporting each investigation

The focus is not only on finding exceptions, but also on explaining what happened and identifying which cases still require human investigation.

---

## 🧩 Architecture

```text
Synthetic Data Generator
        ↓
CSV Data Sources
        ↓
Data Loader & Validator
        ↓
Deterministic Anomaly Detector
        ↓
Investigation Grouper
        ↓
Evidence Chain Builder
        ↓
Gemini Advisory Analyzer
        ↓
Human Review Queue
        ↓
Audit Trail
        ↓
Streamlit Dashboard
```

---

## 🔍 Anomaly Detection

The system checks for nine types of anomalies:

1. Payment / Order Amount Mismatch
2. Missing Payment
3. Duplicate Payment
4. Missing Refund
5. Incorrect Refund Amount
6. Settlement Mismatch
7. Duplicate Settlement
8. Missing Settlement
9. Orphan Record

The deterministic detection layer handles objective financial facts such as:

- Amount comparisons
- Record existence
- Duplicate detection
- Identifier relationships
- Settlement matching
- Refund matching

This keeps core financial decisions reproducible and auditable.

---

## 🤖 Role of Gemini

Gemini is used as an **advisory analysis layer**, not as the source of truth.

The deterministic engine first establishes the facts.

Gemini then receives the selected investigation evidence and helps produce:

### Verified Facts

Facts directly supported by the detected anomalies and evidence.

### Root Cause Hypothesis

A possible explanation for why the related exceptions occurred.

### Unknowns / Assumptions

Information that cannot be established from the available data.

### Recommended Human Investigation Action

A suggested next step for a human finance or operations reviewer.

Gemini is instructed not to invent unsupported financial facts and not to recommend irreversible financial actions without human verification.

---

## 🔗 Investigation Grouping

A key feature of the system is **investigation grouping**.

Instead of treating every anomaly as an unrelated ticket, the system connects anomalies using shared identifiers such as:

- Order ID
- Payment ID
- Settlement ID
- Batch ID

Related anomalies are grouped into a single investigation.

For example, a payment/order mismatch may be connected to a duplicate payment and a settlement mismatch because they involve the same transaction.

This helps reduce investigation fragmentation and gives the reviewer a complete evidence chain.

---

## 📊 Evaluation

The system was tested using a synthetic dataset containing:

- **200 orders**
- **202 payments**
- **35 refunds**
- **193 settlements**
- **34 known ground-truth anomalies**

Latest benchmark results:

| Metric | Result |
|---|---:|
| Precision | 73.9% |
| Recall | 100% |
| F1 Score | 85.0% |
| True Positives | 34 |
| False Positives | 12 |
| False Negatives | 0 |
| Total Detected | 46 |
| Ground Truth | 34 |
| Investigation Groups | 35 |

### Why are there more detected anomalies than ground-truth anomalies?

Some injected issues create downstream reconciliation effects.

For example, one injected payment issue can also cause a settlement mismatch or missing settlement condition.

The system intentionally reports these additional detected exceptions instead of hiding them.

The strict ground-truth evaluation achieved:

**100% recall**

This means all known injected anomalies were detected.

---

## 🧪 Synthetic Data

The project uses synthetic financial data.

No real customer information, real payment credentials, or real financial transactions are used.

Sample data includes:

- `orders.csv`
- `payments.csv`
- `refunds.csv`
- `settlements.csv`
- `finance_records.csv`

Ground-truth labels are stored in:

`data/ground_truth.json`

---

## 🖥️ Dashboard

The Streamlit application provides:

- Finance operations dashboard
- Investigation list
- Priority classification
- Confidence scores
- Amount affected
- Evidence chains
- Transaction explorer
- Gemini root-cause analysis
- Human review workflow
- Audit information

---

## 📁 Project Structure

```text
Payment Investigation System/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── ground_truth.json
│   └── sample/
│       ├── orders.csv
│       ├── payments.csv
│       ├── refunds.csv
│       ├── settlements.csv
│       └── finance_records.csv
│
├── src/
│   ├── __init__.py
│   ├── data_generator.py
│   ├── data_loader.py
│   ├── anomaly_detector.py
│   ├── investigator.py
│   ├── gemini_analyzer.py
│   ├── evidence.py
│   ├── review.py
│   ├── audit.py
│   └── evaluator.py
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── investigation_view.py
│   ├── evidence_view.py
│   └── explorer.py
│
└── tests/
    ├── test_anomaly_detector.py
    ├── test_investigator.py
    ├── test_evaluator.py
    └── test_data_loader.py
```

---

## ⚙️ Technology Stack

- **Python**
- **Streamlit**
- **Pandas**
- **Plotly**
- **Google Gemini API**
- **Pytest**
- **CSV**
- **JSON**

---

## 🔐 Security

The Gemini API key is not stored in the source code.

For deployment, the API key is provided through Streamlit Secrets using:

```toml
GEMINI_API_KEY = "your-api-key"
```

The actual API key must never be committed to GitHub.

---

## 🛠️ Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/karthikmanchala23-cell/payment-investigation-system.git
cd payment-investigation-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini

Set the Gemini API key as an environment variable:

```text
GEMINI_API_KEY=your-api-key
```

Do not commit the API key to GitHub.

### 4. Start the application

```bash
streamlit run app.py
```

The application will open in the browser.

---

## 🧪 Testing

The project includes automated tests for:

- Data loading
- Data validation
- Anomaly detection
- Investigation grouping
- Evaluation metrics

Latest test result:

**27 tests passed**

---

## ⚠️ Limitations

- The dataset is synthetic.
- Detection rules are designed for the selected payment lifecycle.
- Gemini analysis is advisory and depends on the available evidence.
- The system does not execute real financial transactions.
- Human review is required for uncertain or consequential financial actions.

---

## 🔄 Failure Recovery

During development, the system was tested against cases where multiple anomalies were connected.

Instead of allowing an AI model to independently decide what happened, the architecture was changed to make the deterministic detection and evidence chain the source of truth.

Gemini is therefore used only after the factual investigation is established.

This provides a safer separation between:

**Facts → Evidence → AI Hypothesis → Human Decision**

---

## 👤 Project

**Payment Investigation System**

Built as an AI Finance Controller project for the Razorpay AI Buildathon / AI Builder Internship challenge.

---

## 📌 Links

**Live Demo:**  
https://payment-investigation-system-uwcnzdu7ithqojpd3egqls.streamlit.app/

**GitHub:**  
https://github.com/karthikmanchala23-cell/payment-investigation-system
