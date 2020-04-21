# Mock data tools

## Setup

```
pip3 install --requirement=requirements.txt
```

## Run

Run script with the number of employees you want generated.

Script will determine the number of employer pool generated. See `EMPLOYER_TO_EMPLOYEE_MULTIPLIER` in script.
```
./generate.py --count=160000
```

## Copy to S3 for testing

```
aws s3 cp data/<employer_file _name> s3://massgov-pfml-sandbox/external-integrations/dor/daily_import/received/<employer_file _name>
aws s3 cp data/<employee_file _name> s3://massgov-pfml-sandbox/external-integrations/dor/daily_import/received/<employee_file _name>
```
