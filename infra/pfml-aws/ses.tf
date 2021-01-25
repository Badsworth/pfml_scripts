# Add the email we want to send from	
resource "aws_ses_email_identity" "noreply" {
  email = "noreplypfml@mass.gov"
}
