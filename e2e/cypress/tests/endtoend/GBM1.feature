Feature: Submit a Medical Claim in which the claimant mails their HCP form at later time

  @portal
  Scenario: As a claimant, I should be able to start submitting a GBM1 claim through the portal
    Given I begin to submit a "GBM1" claim as a "financially eligible" employee
    When I click on the checklist button called "Verify your identity"
    Then I have my identity verified "normal"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I answer the pregnancy question
    And I answer the continuous leave question
    And I answer the reduced leave question
    And I answer the intermittent leave question
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Report other leave, income, and benefits"
    Then I report other benefits
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Review and confirm"
    Given I am on the claims "review" page
    Then I should have confirmed that information is correct
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Add payment information"
    Then I add payment info
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to return to the portal dashboard

  @fineos
  Scenario: As a CSR (Savilix), I should be able to confirm that the HCP is missing
    Given I search for the proper claim in Fineos
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
    Then I should approve claim