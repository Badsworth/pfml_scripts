# Generate keys for agencies to encrypt data on their end before send it over.
#
# The spec should use asymmetric RSA-based encryption with the longest number of bits
# to deter brute-force attempts.
#
# Symmetric encryption cannot be used as the raw unencrypted key cannot be exported out of AWS KMS.
# ECC/ECDSA are used for signing and verifying messages, not encrypting and decrypting them.
#
# More info here: https://docs.aws.amazon.com/kms/latest/developerguide/symm-asymm-choose.html
#
# TODO: add an IAM policy to restrict usage of this KMS key.
resource "aws_kms_key" "department_of_revenue" {
  for_each                 = toset(concat(local.vpcs, local.environments))
  description              = "(${each.key}) KMS key for encrypting and decrypting data provided by Department of Revenue"
  key_usage                = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "RSA_4096"
  deletion_window_in_days  = 7
}

resource "aws_kms_alias" "department_of_revenue" {
  for_each      = toset(concat(local.vpcs, local.environments))
  name          = "alias/agency_transfer_dor_${each.key}"
  target_key_id = aws_kms_key.department_of_revenue[each.key].key_id
}
