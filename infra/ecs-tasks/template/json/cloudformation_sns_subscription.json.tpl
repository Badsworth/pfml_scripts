{
 "AWSTemplateFormatVersion": "2010-09-09",
  "Resources": {
    "SNSSubscription": {
      "Type": "AWS::SNS::Subscription",
      "Properties": {
          "Endpoint" : "${sns_email}",
          "Protocol" : "email-json",
          "TopicArn" : "${sns_topic_arn}"
      }
    }
  }
}
