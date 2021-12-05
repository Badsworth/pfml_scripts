# Department of Revenue (DOR)


## Description:

DOR is the Massachusetts department that collects taxes and processes tax filings from individuals and businesses.

## Role:

DOR is required because it's the only source of data on contributions to PFML by employers and employees

## Input:

1. What data does DOR require?
   - DOR requires employers to file quarterly data (what's included in this data?) on each of their employees, including their wages and contributions (from both employer and employee) to the PFML fund. For employers with over 25 employees, both the employer and employee contribute, smaller employers don't have to. Full details at https://www.mass.gov/info-details/family-and-medical-leave-contribution-rates-for-employers#calendar-year-2021-

2. What/Who generates this information?
    - Employers (and employees) use a system called
MassTaxConnect to file online. MassTaxConnect is not part of our system.

## Process:

What does the DOR do with this information?  
- DOR does some processing on the data and then sends this data daily to the PFML system via S3.

## Output:

1. What information does the DOR return into the system? 
    - Employee and Employer data... What data 

2. Where is the output captured?(logs, stdout, file, return value to caller?)
    - DOR sends files (what mechanism does DOR use to send files?)

3. Which part(s) of the system consume this information?
    - The files DOR generates are consumed by the [DOR FINEOS ETL][DFE] which sends it to RDS ([PFML Prod DB][PDB])

[DFE]: linkToSomething
[PDB]: linkToProdDBPage