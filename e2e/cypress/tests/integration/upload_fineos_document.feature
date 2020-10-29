Feature: Upload a document in FINEOS and see it has been uploaded in the portal

  @portal
  Scenario: I upload Part One and Payment information of a HAP1 claim
    Given I begin to submit a "MHAP1" claim as a "financially eligible" employee
    And Part One of the claim has been submitted
    And I have added payment information

  @fineos
  Scenario: As a CSR (Savilinx), I upload an MA ID document to a claim
    Given I am logged into Fineos as a Savilinx user
    Then I can commence intake on that claim
    And I click through the commence intake flow
    Given I am on the tab "Documents"
    And the document "MA ID" has been uploaded with "Identification Proof" business type
    Then I should find the "MA ID" document

  @portal
  Scenario: I should be able to see that a document has been uploaded in the portal
    Given I return to the portal
    And I go directly to the ID upload page
    Then there should be 1 ID document uploaded

