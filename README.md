# Artifact for: Disentangling the Throughput Contributions of MIMO and Carrier Aggregation in 5G Networks
PAM 2026

---

## Overview

This artifact reproduces all figures from our paper **"Disentangling the Throughput Contributions of MIMO and Carrier Aggregation in 5G Networks"**, providing preprocessed datasets and plotting scripts in a template-aligned layout.

The artifact includes:
- Preprocessed real-world datasets (`.pkl` files)
- Python scripts to reproduce figures
- A master script to generate all figures at once

All results can be reproduced using standard Python packages on any Unix-like environment (or Windows with a Bash shell).

---

## Directory Structure

```text
.
├── pkl/               # Preprocessed measurement data (.pkl format)
├── plots/             # Output directory for generated figures (PDFs)
├── scripts/           # Individual scripts to reproduce one result at a time
├── reproduce_all.sh   # Master script to reproduce all results at once
└── README.md          # This file
```


---

## System Requirements

- OS: Linux or macOS (or Windows with WSL / Git Bash)
- Python: 3.6 or newer
- No GPU or special hardware required

---

## Dependencies

Install the required Python packages:

```bash
pip install pandas numpy matplotlib seaborn
```

We also use `pickle` from the Python standard library (no installation needed).

---

## Reproducing All Figures

Follow these steps to reproduce every figure in the paper (run inside the `code` folder):

### Step 1: Clone the repository

```bash
git clone https://github.com/NUWiNS/pam25-mimo-ca-dataset.git
cd pam25-mimo-ca-dataset
```

### Step 2: Install dependencies

```bash
pip install pandas numpy matplotlib seaborn
```

### Step 3: Run all scripts

```bash
chmod +x reproduce_all.sh
./reproduce_all.sh
```

This will:
- Automatically run all scripts in the `scripts/` directory
- Print which figure is being generated (if logged by the script)
- Print where each figure is saved (e.g., `../plots/box_ca_tput_dl.pdf`)
- Save all plots to the `plots/` directory

---

## Expected Output

- Each script outputs one figure corresponding to a paper figure
- Files are saved as high-quality `.pdf` in `plots/`
- Console output confirms figure generation and may include numerical statistics
- Outputs are deterministic with no randomness or variation

---

## Customization

Each script in `scripts/` is self-contained and easy to modify:
- Adjust plot styles via matplotlib or `scripts/matplotlibrc`
- Swap out `.pkl` inputs to run custom or ablated experiments

---

## Troubleshooting

- Ensure you are running from the project root directory
- Confirm Python version is 3.6+:
  ```bash
  python3 --version
  ```
- Make sure the `plots/` directory exists and is writable

---

## Contact

**Yufei Feng**
Email: `feng.yuf[at]northeastern.edu`
GitHub: [https://github.com/NUWiNS](https://github.com/NUWiNS)

---
