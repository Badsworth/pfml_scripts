Feature: Submit Part One of a claim, without documents, and commence it in FINEOS

  @portal
  Scenario: As a claimant, I submit a HAP1 claim through the portal (part one only)
    Given I begin the process to submit a "HAP1" claim
    And Part One of the claim has been submitted

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to commence intake on a HAP1 claim
    Given I am logged into Fineos as a Savilinx user
    Then I can commence intake on that claim