Feature: Submit Part One of a claim, without documents, and then find in FINEOS

  @portal
  Scenario: As a claimant, I submit a claim through the portal (part one only)
    Given I begin to submit a "MHAP1" claim as a "financially eligible" employee
    And Part One of the claim has been submitted

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to locate claim for Adjudication
    Given I am logged into Fineos as a Savilinx user
    Then I should be able to find claim in Adjudication
