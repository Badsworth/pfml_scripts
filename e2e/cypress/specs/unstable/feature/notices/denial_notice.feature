Feature: Submit Part One of a claim, denies claim in Fineos - then checks legal notice document
  
  @portal
  Scenario: As a claimant, I submit a claim through the portal (part one only)
    Given I begin to submit a "BHAP1" claim as a "financially ineligible" employee
    When I am the "new" claimant visiting the portal
    Then I continue creating the claim
    And Part One of the claim has been submitted
  
  @fineos
  Scenario: As a CSR (Savilinx), I should be able to deny their claim
    Given I am logged into Fineos as a Savilinx user
    Then I should be able to find claim in Adjudication
    And I should reject the plan
    Given I complete claim Denial for "Financial Ineligibility"
  
  @portal
  Scenario: I should be able to download a Denial Notice document from the app card
    Given I return to the portal as the "new" claimant
    And I find my application card
    When I see a pdf "Denial" notice to download
    # @ToDo Will add later, currently just checking notice link
    # Then I should confirm the "Denial" notice is valid