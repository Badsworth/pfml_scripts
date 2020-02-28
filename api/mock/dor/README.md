# Mock data tools

## Setup

```
pip3 install --requirement=requirements.txt
```

## Run

```
./generate.py --count=160000 >dor.txt
```

## Copy to S3 for testing

```
aws s3 cp dor.txt s3://massgov-pfml-sandbox/external-integrations/dor/dor_large.txt
```
