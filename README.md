# ⌨️ Typing Speed Before and After Practice
## A Statistical Study of Computer Skills — MDM Mini Project

An interactive, end-to-end data analytics and hypothesis testing application built with **Python**, **Streamlit**, **Pandas**, **SciPy**, and **Plotly**.

This project analyzes whether deliberate typing practice leads to a statistically significant improvement in typing speed (Words Per Minute — WPM) among computer science students using a **paired-sample $t$-test**.

---

## 📌 Project Overview

In data management and inferential statistics, when the **same subjects** are measured at two distinct time points (e.g., pre-test vs. post-test), observations are dependent. This project demonstrates the theoretical and computational aspects of:
- Descriptive statistics (pre/post means, standard deviations, variance).
- Paired differences ($d_i = \text{after}_i - \text{before}_i$).
- Inferential statistics (paired-sample $t$-test via `scipy.stats.ttest_rel`).
- Hypothesis testing at $\alpha = 0.05$ significance level with automated plain-language conclusions.
- Interactive data entry, batch CSV upload, and Plotly visual comparisons.

---

## 🚀 Key Features

1. **📊 Overview Dashboard**:
   - High-level KPIs: Total students, Mean Before (WPM), Mean After (WPM), and Mean Improvement ($\bar{d}$).
   - Status indicators clearly distinguishing between demonstration data and real student data.

2. **📝 Student Data Management**:
   - Single-student manual entry form with input validation (duplicate ID rejection, speed bounds).
   - Batch CSV file upload and live preview.
   - Built-in demonstration dataset (10 paired student records).

3. **📈 Interactive Visualizations (Plotly)**:
   - Before vs. After paired slope / parallel coordinates chart showing individual trajectories.
   - Side-by-side distribution box plots and group bar comparisons.
   - Individual gain waterfall / bar chart sorted by magnitude of improvement.
   - Difference distribution histogram with normal curve overlay.

4. **🔬 Statistical Analysis Module**:
   - Complete step-by-step calculation breakdown:
     - Pre-practice mean ($\bar{x}_1$) and sample SD ($s_1$)
     - Post-practice mean ($\bar{x}_2$) and sample SD ($s_2$)
     - Mean difference ($\bar{d}$) and sample SD of differences ($s_d$)
     - Standard error of the mean difference ($SE_d = s_d / \sqrt{n}$)
     - $t$-statistic, degrees of freedom ($df = n - 1$), and two-tailed $p$-value.
   - Hypothesis test outcome: Reject $H_0$ or Fail to Reject $H_0$ at $\alpha = 0.05$.

5. **📄 Plain-Language Interpretation & CSV Export**:
   - Auto-generated narrative interpretation for non-technical readers.
   - One-click downloadable CSV containing all raw records, calculated differences, and test summary.

---

## 📐 Mathematical Formulation

### 1. Paired Difference
For each student $i \in \{1, 2, \dots, n\}$:
$$d_i = \text{after}_i - \text{before}_i$$

### 2. Mean Difference ($\bar{d}$)
$$\bar{d} = \frac{1}{n}\sum_{i=1}^{n} d_i = \bar{x}_{\text{after}} - \bar{x}_{\text{before}}$$

### 3. Sample Standard Deviation of Differences ($s_d$)
$$s_d = \sqrt{\frac{\sum_{i=1}^{n} (d_i - \bar{d})^2}{n - 1}}$$

### 4. Standard Error ($SE_d$)
$$SE_d = \frac{s_d}{\sqrt{n}}$$

### 5. Paired $t$-Statistic
$$t = \frac{\bar{d} - \mu_0}{SE_d} = \frac{\bar{d}}{s_d / \sqrt{n}} \quad (\text{under } H_0: \mu_d = 0)$$
with degrees of freedom $df = n - 1$.

### 6. Hypotheses
- **Null Hypothesis ($H_0$)**: $\mu_d = 0$ (Typing practice has no effect on average typing speed).
- **Alternative Hypothesis ($H_1$)**: $\mu_d \neq 0$ (Typing practice significantly changes average typing speed).
- **Decision Rule**: Reject $H_0$ if $p\text{-value} < 0.05$.

---

## 📂 Project Structure

```text
mdm-typing-speed-project/
│
├── app.py                      # Main Streamlit web dashboard
├── statistics_analysis.py      # Core statistical calculation engine & tests
├── requirements.txt            # Python package dependencies
├── README.md                   # Project documentation & GitHub overview
├── PROJECT_DOCUMENTATION.md    # 16-section comprehensive academic report
├── run_app.bat                 # Windows one-click launcher
│
├── data/
│   └── demo_data.csv           # 10-student sample pre/post dataset
│
└── .gitignore                  # Git exclusions for venv and caches
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+ installed ([python.org](https://www.python.org/))
- Git installed ([git-scm.com](https://git-scm.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/mdm-typing-speed-project.git
cd mdm-typing-speed-project
```

### 2. Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Statistical Engine Verification Test
```bash
python statistics_analysis.py
```
*Expected output: All 6 built-in unit tests PASS.*

### 5. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
The application will open automatically at **`http://localhost:8501`**.

*(On Windows, you can also simply double-click `run_app.bat`)*

---

## 📊 Demonstration Results Summary

Using the included 10-student demonstration dataset (`data/demo_data.csv`):

| Metric | Pre-Practice | Post-Practice | Difference ($d$) |
| :--- | :---: | :---: | :---: |
| **Mean Speed (WPM)** | $47.20$ | $57.50$ | $+10.30$ |
| **Standard Deviation ($s$)** | $10.74$ | $9.85$ | $2.06$ |
| **Standard Error ($SE$)** | — | — | $0.65$ |
| **Degrees of Freedom ($df$)** | — | — | $9$ |
| **Paired $t$-Statistic** | — | — | **$15.820$** |
| **$p$-Value** | — | — | **$4.18 \times 10^{-8}$** |
| **Statistical Conclusion** | — | — | **Reject $H_0$ ($p < 0.001$)** |

> **Academic Integrity Notice:** The numbers above represent the verified 10-student demonstration dataset. When submitting your real class study, upload your real data file via the dashboard to generate your final class report.

---

## 📑 Full Academic Documentation
A 16-section academic report is available in [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md), covering:
- Abstract & Introduction
- Problem Statement & Objectives
- Research Methodology & Sampling
- Full Statistical Theory & Formulas
- System Architecture & Flowchart
- Technology Stack & Implementation
- Discussion, Limitations, & Conclusion
- Academic References

---

## 👤 Author
- **Course:** Mathematics for Data Management (MDM) — Generative AI Foundation
- **Degree:** B.Tech / B.Sc Computer Science (2nd Year)
