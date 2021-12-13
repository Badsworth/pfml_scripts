# Department of Revenue (DOR)


## Description:

DOR is the Massachusetts department that collects taxes and processes tax filings from individuals and businesses.

## Role:

DOR is required because it's the only source of data on contributions to PFML by employers and employees

## Input:

1. What data does DOR require?
   - DOR requires employers to file quarterly data on each of their employees, including their wages and contributions (from both employer and employee) to the PFML fund. For employers with over 25 employees, both the employer and employee contribute, smaller employers don't have to. Full details at https://www.mass.gov/info-details/family-and-medical-leave-contribution-rates-for-employers#calendar-year-2021-
   

2. What/Who generates this information?
    - Employers (and employees) use a system called
MassTaxConnect to file online. MassTaxConnect is not part of our system.

## Process:

What does the DOR do with this information?  
- DOR does some processing on the data and then sends this data daily to the PFML system via S3.

## Output:

1. What information does the DOR return into the system? 
    - This data includes:
       - Employer information (name, FEIN, dba, address, etc.)
       - Employer exemption (from DFML) fields
       - Employee information (name, SSN, etc.)
       - Employee wage data (quarterly wages)
       - Employee and employer contributions to DFML
   - See the full list of data fields here: https://github.com/EOLWD/pfml/blob/main/api/massgov/pfml/dor/importer/dor_file_formats.py

2. Where is the output captured?(logs, stdout, file, return value to caller?)
    - DOR writes the data to a file that is sent to the agency-transfer S3 bucket using DOR MOVEit. A special IAM role was shared with DOR for this write.
    - See the diagram here: https://lwd.atlassian.net/wiki/spaces/API/pages/448954417/DOR+Importer

3. Which part(s) of the system consume this information?
    - The files DOR generates are consumed by the DOR FINEOS ETL which sends them to RDS (PFML Prod DB) and FINEOS
    - The API uses it too. For example there's a financial eligibility API (that FINEOS calls) which determines if eligibility and some other data. FINEOS calculates the payment amounts. https://lwd.atlassian.net/wiki/spaces/API/pages/636420178/Financial+Eligibility
    - Some of the data fields (contribution amounts) never go to FINEOS so we have to keep it. It's also kept so we can determine what data from DOR is new and what is unmodified.
