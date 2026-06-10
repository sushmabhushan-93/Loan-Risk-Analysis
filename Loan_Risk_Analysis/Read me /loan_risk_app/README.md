# 🏦 LoanRisk IQ — Streamlit App

A 3-page loan risk intelligence platform built from your Jupyter notebook.

## Pages

| Page | What it does |
|------|-------------|
| 📊 EDA & Data Insights | Upload CSV/Excel → automatic cleaning, distributions, correlation heatmap, missing value analysis |
| 📈 Power BI Dashboards | Embed live Power BI reports via paste-in URL |
| 🤖 Predictive Model | Train Logistic Regression + Random Forest, view ROC curves, confusion matrices, CV scores, download model |

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

## Data Format

Your dataset should contain:
- `PROSPECTID` — common key to merge CIBIL + Bank data
- `Approved_Flag` — target column (P1/P2 = low risk, P3/P4 = high risk)
- Numeric features from CIBIL (credit score, enquiries, delinquency history)
- Demographic features (EDUCATION, GENDER, MARITALSTATUS, income)

## Power BI

To embed your `.pbix` dashboard:
1. Publish it to Power BI Service
2. File → Embed → Publish to web
3. Paste the embed URL on Page 2

## Model Output

The trained model is exported as `loan_model.pkl` containing:
- `model` — fitted LogisticRegression
- `scaler` — fitted StandardScaler  
- `features` — list of RFE-selected feature names
