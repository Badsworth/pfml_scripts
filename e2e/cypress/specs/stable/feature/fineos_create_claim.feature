Feature: Create a new continuous leave, bonding claim in FINEOS

  @fineos
  Scenario: I can create a claim on a pre-existing user in FINEOS
    Given I find an employee in the FINEOS system
    Then I begin to submit a new claim on that employee in FINEOS
    And I start create a new notification