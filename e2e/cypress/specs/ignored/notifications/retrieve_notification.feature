Feature: Leave Admin retrieves notification from testmail

  @portal
  Scenario: I am a leave admin that has received an employer response notification
    Then I should be able to retrieve a "employer response" notification from testmail
