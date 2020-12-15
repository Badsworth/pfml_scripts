Feature: Mark evidence received on a claim in FINEOS and employer responds by denying claim

  @portal
  Scenario: As a claimant, I should be able to submit a claim (BHAP1) through the portal
    Given I begin to submit a "BHAP1" claim as a "financially eligible" employee
    When I am the "existing" claimant visiting the portal
    Then I continue creating the claim
    When I have submitted all parts of the claim

    When I log out
    Given I am a Leave Admin for the submitted applications
    And I am on the New Application page
    And I confirm I am the right person to respond
    And I review the application: I "do not" suspect fraud, employee gave "insufficient" notice, and I "deny" the claim

  @portal
  Scenario: An employer should receive a notification to respond to claim and be able to deny it
    Then I should receive a "employer response" notification

  @fineos
  Scenario: A CSR should find the employer response in FINEOS
    Given I am logged into Fineos as a Savilinx user
    And I should be able to find claim in Adjudication
    Then I should find the Employer Response to Leave Request
