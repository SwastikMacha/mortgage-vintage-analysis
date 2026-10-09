# Data

The raw data is not included in this repository. Freddie Mac's terms of use do not allow the files to be redistributed, so each user has to download them.

## Source

Freddie Mac Single-Family Loan-Level Dataset (sample files):
https://freddiemac.com/research/datasets/sf-loanlevel-dataset

## How to download

1. Open the link above and register for a free account (Clarity Data Intelligence).
2. Sign in, accept the terms and conditions, and go to the Single-Family Loan-Level Dataset section.
3. Download the **sample** files, not the full dataset. Each sample file is a random sample of 50,000 loans for one origination year.
4. Download these years: 2005, 2006, 2007, 2008, 2010, 2012, 2015 and 2018.
5. Unzip every file into one folder: `C:\mortgage_data\raw`.

## Expected files

After unzipping, the folder should hold 16 text files, one origination and one performance file per year:

```
sample_orig_2005.txt    sample_perf_2005.txt
sample_orig_2006.txt    sample_perf_2006.txt
sample_orig_2007.txt    sample_perf_2007.txt
sample_orig_2008.txt    sample_perf_2008.txt
sample_orig_2010.txt    sample_perf_2010.txt
sample_orig_2012.txt    sample_perf_2012.txt
sample_orig_2015.txt    sample_perf_2015.txt
sample_orig_2018.txt    sample_perf_2018.txt
```

The origination files are about 6 MB each, and the performance files are 230 to 510 MB each (about 2.9 GB in total).

## File format

- Pipe-delimited text (`|`), with no header row. The scripts add the column names.
- Origination files have 31 columns, and performance files have 35. The scripts read only the columns they need.
- Column definitions are in the Freddie Mac user guide:
  https://www.freddiemac.com/fmac-resources/research/pdf/user_guide.pdf

## Notes

- Unknown values are coded as 9999 (FICO) and 999 (DTI, LTV, CLTV). The scripts convert them to missing values.
- Do not commit these files to Git. They are large, and redistributing them is not allowed.
- Keep the raw files outside cloud-synced folders such as OneDrive, since the performance files are very large.
