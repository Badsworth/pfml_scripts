Feature: Submit a Medical Claim in which the claimant mails their HCP form at later time

  @portal
  Scenario: As a claimant, I should be able to start submitting a GBM1 claim through the portal
    Given I begin the process to submit a "GBM1" claim
    And Part One of the claim has been submitted
    And I am on the claims "checklist" page
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document

  @fineos
  Scenario: As a CSR (Savilix), I should be able to confirm that the HCP is missing
    Given I am logged into Fineos as a Savilinx user
    Then I can commence intake on that claim
    And I click through the commence intake flow
    And I am on the tab "Documents"
    And the document "HCP" has been uploaded with "State Managed" business type
    Then I should find the "HCP" document
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    Given I am on the tab "Paid Benefits"
    When I click edit
    Then I should add weekly wage
    Given I am on the tab "Evidence"
    And I am on the tab "Certification Periods"
    Then I should fufill availability request
    When I click Adjudicate
    Given I am on the tab "Evidence"
    When I click Manage Evidence
    Then I should confirm evidence is "valid"
    When I highlight ID Proof
    And I click Manage Evidence
    Then I should confirm evidence is "valid"
    Given I am on the tab "Manage Request"
    Then I click Accept
    Given I am on the claim case page
    Then I should be able to approve the claim