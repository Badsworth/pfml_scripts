# Overview
Does your payment logic require the ability to easily create a CSV report?

Does that report need to be sent to several different places with a lot of configuration?

Then you need to use these fun report utilities.
# How to Use

## Records
Records are the base of a report. They contain one unit of information,
usually corresponding to a payment, employee or similar. A record needs to be able
to contain everything in a single row of your report. For example, if you need
to store an ID, description and count for your scenario, you might create something
like:
```python
@dataclass # Not strictly needed, but makes the init function for you
class ExampleRecord(AbstractRecord):
    id: Optional[str] = None
    description: Optional[str] = None
    count: Optional[str] = None

    # This is the
    def get_dict(self) -> Dict[str, Optional[str]]:
        return {
          "ID": self.id,
          "Description": self.description,
          "Count:": self.count
        }
```
As you iterate over your dataset, you'll need to create example records
into a list which you'll put into the report object (see next section).

## Report
A report is a container for collecting all of the records and will be
used to create one file. Creating a report is very easy, you only need to
specify a few fields:
```python
example_report = Report(report_name="example_report", csv_headers=["ID","Description","Count"])
```
Report name is used to create the name of the file which will also add timestamp prefixes and
an appropriate format suffix (.csv).

CSV Headers needs to correspond to the dictionary keys returned by your record class.

## Report Group
Once you have your report(s) you need to toss them in a report group. Report groups
are where the configuration lives that will handle sending your report out to email/S3.

Any configurations added to a report group will make it send the file(s) to that location,
so if you don't want to send an email, don't add an email config.

```python
email_config = EmailConfig(
    sender="example_mail@mail.com",
    recipient=EmailRecipient(to_addresses=["receiver@mail.com"]),
    subject="Title of your email",
    body_text="Contents of your email",
    bounce_forwarding_email_address_arn="arn:://something"
)
s3_config = S3Config(
  s3_prefix="s3://example_bucket/path/to/reports/"
)
example_report_group = ReportGroup(
    email_config=email_config,
    s3_config=s3_config
)
```

## Putting it all together
```python
record1 = ExampleRecord(
    id="123",
    description="record1",
    count="1"
)

record2 = ExampleRecord(
    id="456",
    description="record2",
    count="2"
)

example_report = Report(report_name="example_report", csv_headers=["ID","Description","Count"])
example_report.records = [record1, record2] # Can also add with the add_record method

s3_config = S3Config(
  s3_prefix="s3://example_bucket/path/to/reports/"
)
# Highly recommended to put the report group creation into a utility method
# as it's going to be static in most cases
example_report_group = ReportGroup(
    email_config=None,
    s3_config=s3_config
)
example_report_group.add_report(example_report)

# Finally create and send the records
example_report_group.create_and_send_reports()

# Your reports can now be found in the s3://example_bucket/path/to/reports/ folder
# and will look like the below. Note that reports created with no records still
# produce a header.

# "ID", "Description", "Count"
# "123", "record1", "1"
# "456", "record2", "2"
```


# Future Ideas
- Make reports of formats other than CSV
- Add additional places to send reports (Sharepoint?)