Feature: Find a started claim in the portal and upload a document to it

  @portal
  Scenario: I should be able to find a specific claim in the portal and upload a document to it
    Given I begin to submit a "BHAP1" claim as a "financially eligible" employee
    When I am the "existing" claimant visiting the portal
    Then I continue creating the claim
    And Part One of the claim has been submitted
    When I log out
    And I log into the portal
    Given I am on the page for that claim
    And I have added payment information
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document "MA ID"

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to commence intake on a HAP1 claim
    Given I am logged into Fineos as a Savilinx user
    And I should be able to find claim in Adjudication
    Given I am on the tab "Documents"
    Then I should find the "MA ID" document