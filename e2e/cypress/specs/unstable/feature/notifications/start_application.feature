Feature: Submit a bonding claim Part One and employer receives Application Started notification

  @portal
  Scenario: A claimant submits part one of a leave claim through the portal
    Given I begin to submit a "BHAP1" claim as a "financially eligible" employee
    And Part One of the claim has been submitted
    Then I should receive a "application started" notification