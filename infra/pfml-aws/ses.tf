# Deprecated email identity
resource "aws_ses_email_identity" "noreply" {
  email = "noreplypfml@mass.gov"
}

# New email domain and identity -- see https://lwd.atlassian.net/browse/PFMLPB-640.
#
resource "aws_ses_domain_identity" "eol" {
  domain = "eol.mass.gov"
}

resource "aws_ses_domain_dkim" "eol" {
  domain = aws_ses_domain_identity.eol.domain
}

resource "aws_ses_email_identity" "pfml_donotreply" {
  email = "PFML_DoNotReply@eol.mass.gov"
}

# Alias
resource "aws_ses_domain_identity" "eol_state" {
  domain = "eol.state.ma.us"
}

resource "aws_ses_domain_dkim" "eol_state" {
  domain = aws_ses_domain_identity.eol_state.domain
}

resource "aws_ses_email_identity" "pfml_donotreply_state" {
  email = "PFML_DoNotReply@eol.state.ma.us"
}
