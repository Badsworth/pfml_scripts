import boto3
import os
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

# S3 bucket and prefix to search
BUCKET_NAME = "massgov-pfml-prod-agency-transfer"
BASE_PREFIX = "reductions/dfml"

# Email settings
SUBJECT = "DUA_DFML file"
SENDER = "Mass No Reply <PFML_DoNotReply@eol.mass.gov>"
EMAIL_RECIPIENTS = [
    "Chris Ashton <chris.ashton@focusconsulting.io>",
    "Matthew Smiddy <matthew.j.smiddy@mass.gov>",
    "Jasmine Patel <jasmine.patel@mass.gov>",
    "Sye Chanthaboun <sye.chanthaboun2@mass.gov>",
    "Clinika Hylton <clinika.m.hylton@mass.gov>",
    "Carl Lamour <carl.h.lamour@mass.gov>",
]
# The email body for recipients with non-HTML email clients.
BODY_TEXT = "Hello,\r\nDUA_DFML file attached."
# The HTML body of the email.
BODY_HTML = """
<html>
<head></head>
<body>
<h1>Good morning!</h1>
<p>Today's DUA DFML csv report is attached.</p>
</body>
</html>
"""
AWS_REGION = "us-east-1"


def find_todays_dua_file() -> tuple:
    """ Returns tuple for the path and filename for the DUA_DFML file """
    for key in boto3.client("s3").list_objects(Bucket=BUCKET_NAME, Prefix=BASE_PREFIX)[
        "Contents"
    ]:
        if f"DUA_DFML_{datetime.now().strftime('%Y%m%d')}" in key["Key"]:
            filename = key["Key"].split("/")[-1]
            return (key["Key"], filename)


def download_file(path, filename):
    """ Downloads file from S3 into current working directory """
    prefix = "/".join(path.split("/")[0:-1])
    print(f"prefix is {prefix}, path is {path}")
    boto3.resource("s3").Bucket(BUCKET_NAME).download_file(path, f"/tmp/{filename}")


def make_zip_file(path, filename) -> str:
    """ Downloads a file from S3 and makes a zip file out of it """
    download_file(path, filename)
    with ZipFile(f"/tmp/{filename}.zip", "w", ZIP_DEFLATED) as zipp:
        zipp.write(f"/tmp/{filename}")

    return f"/tmp/{filename}.zip"


def email_file(
    attachment_filepath,
    subject,
    sender,
    email_recipients,
    body_text,
    body_html,
    aws_region,
) -> str:
    """ Composes email, attaches document, and sends it to the recipients above """
    # docs for below: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-email-raw.html

    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a new SES resource and specify a region.
    client = boto3.client("ses", region_name=aws_region)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart("mixed")
    # Add subject, from and to lines.
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ",".join(email_recipients)

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart("alternative")

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(body_text.encode(CHARSET), "plain", CHARSET)
    htmlpart = MIMEText(body_html.encode(CHARSET), "html", CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(attachment_filepath, "rb").read())

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header(
        "Content-Disposition",
        "attachment",
        filename=os.path.basename(attachment_filepath),
    )

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)
    # print(msg)
    try:
        # Provide the contents of the email.
        response = client.send_raw_email(
            Source=sender,
            Destinations=email_recipients,
            RawMessage={"Data": msg.as_string(),},
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        return e.response["Error"]["Message"]
    else:
        return f"Email sent! Message ID:\n{response['MessageId']}"


def lambda_handler(event, context=None):
    """ Lambda entrypoint """
    ATTACHMENT = make_zip_file(*find_todays_dua_file())
    # email_file returns message for error or success
    return email_file(
        ATTACHMENT, SUBJECT, SENDER, EMAIL_RECIPIENTS, BODY_TEXT, BODY_HTML, AWS_REGION
    )
