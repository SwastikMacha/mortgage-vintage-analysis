# Mortgage Vintage Risk Monitor

**Business question:** Are newer mortgage cohorts riskier than older ones, and what drives the deterioration?

This project builds a vintage (cohort) analysis of mortgage delinquency, the standard portfolio-risk view used in banks and NBFCs. It tracks how fast each origination year reaches 90+ days past due, splits the difference between vintages into borrower mix and worse performance, and presents the results in a three-page Power BI dashboard.

**Tools:** Python (pandas, NumPy, matplotlib), Power BI (DAX, Power Query)

## Data

Freddie Mac Single-Family Loan-Level Dataset, sample files (50,000 loans per origination year, with monthly performance history).

Vintages analysed: 2005, 2006, 2007, 2008, 2010, 2012, 2015, 2018.

The raw data is not in this repository because of Freddie Mac's terms of use. See [`data/README.md`](data/README.md) for download steps.

## Key findings

- **2007 was the worst vintage.** 6.1% of its loans reached 90+ DPD within 24 months, against 0.7% for 2012, about 9x higher. By month 60, 2007 reached 13.7% against 1.4% for 2012.
- **Deterioration was broad, not limited to weak borrowers.** Prime borrowers (FICO 740+) defaulted about 6x more often in 2007 than in 2012 (1.68% vs 0.27% at 24 months).
- **Mix vs performance (2007 vs 2012, 24 months).** Of the 5.46-point gap, about 47% (2.59 points) came from a riskier borrower mix and about 53% (2.87 points) from worse performance within the same FICO band.
- **Risk peaked at different loan ages for different vintages**, because calendar time (the 2009-2011 housing crisis) drove it. The monthly hazard for 2007 peaked near month 30, and for 2006 near month 43.
- **No sign of newer cohorts drifting back to pre-crisis risk.** The 2010, 2012 and 2015 vintages track each other closely, and 2015 is slightly better than 2012 after adjusting for FICO mix.

| Vintage | 12 months | 24 months | 36 months |
|---|---|---|---|
| 2005 | 1.13% | 2.10% | 3.08% |
| 2006 | 1.71% | 3.39% | 6.12% |
| 2007 | 2.42% | 6.12% | 9.80% |
| 2008 | 1.87% | 4.44% | 6.00% |
| 2010 | 0.32% | 0.82% | 1.28% |
| 2012 | 0.31% | 0.66% | 0.92% |
| 2015 | 0.20% | 0.54% | 0.92% |
| 2018 | 0.21% | n/a | n/a |

*Cumulative share of originated loans that reached 90+ DPD or REO by loan age.*

## Dashboard

The Power BI file is in [`powerbi/Mortgage_Risk_Monitor.pbix`](powerbi/Mortgage_Risk_Monitor.pbix). It reads the CSV files in `output/` and has three pages. A screenshot of each page is saved in the `docs/` folder:

| Page | What it shows | Screenshot |
|---|---|---|
| 1. Executive view | Worst vintage, worst and best 24-month default rates, ratio of the worst vintage to 2012, cumulative default curves, and default rates at 12, 24 and 36 months | `docs/page1_executive.png` |
| 2. Vintage matrix | Heatmap of cumulative 90+ DPD by vintage and months on book, plus the monthly hazard rate (3-month rolling average) | `docs/page2_matrix.png` |
| 3. Drivers | 24-month default rate by FICO or LTV band, the mix vs performance split of each vintage's gap to 2012, and the FICO mix of each vintage | `docs/page3_drivers.png` |

## How it works

1. **`scripts/Transforming.py`** reads the raw origination and monthly performance files and reduces them to one row per loan: the loan age at first 90+ DPD and the last age observed. Unknown FICO (9999) and unknown LTV, DTI and CLTV (999) are set to missing.
2. **`scripts/Matrix.py`** builds the vintage curves, the monthly hazard rate, the vintage matrix and segment cuts by FICO band and LTV band.
3. **`scripts/mix_shift.py`** applies each vintage's FICO-band default rates to 2012's borrower mix. The result separates the gap into a mix effect and a performance effect.
4. **Power BI** loads the CSV outputs and presents them in three pages.

## Definitions and assumptions

- **Default event:** the first month with delinquency status of 90+ days past due (status 3 or higher) or REO.
- **Cumulative default rate:** loans that have reached the default event by age *m*, divided by loans observable at age *m*.
- **Hazard rate:** new default events in month *m* divided by loans still at risk (not yet defaulted, not yet prepaid or otherwise gone).
- **COVID cutoff:** performance data is cut at December 2019. Forbearance and payment deferrals after that point inflate delinquency without being normal credit deterioration. Without the cutoff, the 2018 vintage looked like the third-worst, which was wrong.
- **Right-censoring:** a loan is counted at age *m* only if it could have reached age *m* before the cutoff. A curve stops once fewer than half of its vintage's loans are observable. This is why 2015 and 2018 end early, and why empty matrix cells are blank, not zero.
- **FICO bands:** below 620, 620-679, 680-739 and 740+.
- **Mix split reference:** 2012, the cleanest post-crisis vintage.

## Limitations

- Sample data (50,000 loans per vintage), so small segments, such as FICO below 620 in 2010 to 2015, are noisy.
- The mix split adjusts for FICO bands only. LTV, DTI and loan purpose also changed between vintages, so part of the "performance effect" is probably mix on those variables.
- The performance effect also includes macro conditions (house prices, unemployment). It does not isolate underwriting quality.
- The split depends on the choice of 2012 as the reference year.
- Prepayment is a competing risk. It appears only through the hazard view.
- No loss severity or recoveries, so this measures delinquency, not credit loss.
- The 2015 and 2018 vintages are only partly observed, so they cannot be compared with older vintages over the full 60 months.
- US mortgage data, not Indian retail lending. The method carries over directly to Indian DPD buckets (SMA-0, SMA-1, SMA-2 and NPA at 90+ DPD) with monthly collection data.

## Repository structure

```
mortgage-vintage-analysis/
├── README.md
├── requirements.txt
├── data/
│   └── README.md            # download instructions (raw data not included)
├── scripts/
│   ├── Transforming.py
│   ├── Matrix.py
│   └── mix_shift.py
├── output/
│   ├── vintage_curves.csv
│   ├── vintage_matrix.csv
│   ├── vintage_segments.csv
│   ├── mix_shift.csv
│   └── mix_by_fico.csv
├── powerbi/
│   └── Mortgage_Risk_Monitor.pbix
└── docs/
    ├── page1_executive.png
    ├── page2_matrix.png
    └── page3_drivers.png
```

## How to run

1. Download the raw data (see [`data/README.md`](data/README.md)) and unzip it into `C:\mortgage_data\raw`. Files should be named `sample_orig_YYYY.txt` and `sample_perf_YYYY.txt`.
2. Install the libraries:
```
   pip install -r requirements.txt
```
3. Run the scripts in this order. Each step reads what the previous one saved.
```
   python scripts/Transforming.py
   python scripts/Matrix.py
   python scripts/mix_shift.py
```
4. Open `powerbi/Mortgage_Risk_Monitor.pbix` and point its data sources to the CSV files in `output/` (Home, Transform data, Data source settings).

The scripts expect the folders `C:\mortgage_data\raw` (input) and `C:\mortgage_data\clean` (output). Change the `RAW` and `OUT` lines at the top of each script to use different locations.

## Data source

Freddie Mac, Single-Family Loan-Level Dataset: https://freddiemac.com/research/datasets/sf-loanlevel-dataset. Used for analysis and research under Freddie Mac's terms of use. This project is not affiliated with Freddie Mac.
