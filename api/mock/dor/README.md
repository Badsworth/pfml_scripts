# Mock data tools

## Setup

```
pip3 install --requirement=requirements.txt
```

## Run

Run script with the number of employees you want generated.

Script will determine the number of employer pool generated. See `EMPLOYEE_TO_EMPLOYER_MULTIPILER` in script.
```
./generate.py --count=160000
```

## Copy to S3 for testing

```
aws s3 cp dor.txt s3://massgov-pfml-sandbox/external-integrations/dor/employees.txt
aws s3 cp dor.txt s3://massgov-pfml-sandbox/external-integrations/dor/employers.txt
```
