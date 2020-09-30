Feature: Submit a medical claim that is missing an HCP, and refer it to DFML

  @portal
  Scenario: As a claimant, I should be able to start submitting a GBR1 claim through the portal
    Given I begin the process to submit a "GBR1" claim
    When I click on the checklist button called "Verify your identity"
    Then I have my identity verified "normal"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I finish submitting the claim based on its type
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims "checklist" page
    When I resume "Enter leave details"
    Then I start submitting the claim
    And I finish submitting the claim based on its type
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
    Then I should confirm "HCP form" is not present
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    Given I am on the tab "Evidence"
    When I click Manage Evidence
    Then I should confirm evidence is "invalid due to missing HCP form"
    Given I am on the claim case page
    And I am on the tab "Tasks"
    When I complete adding Evidence Review Task
    Then I should transfer task to DMFL
    And I should confirm task assigned to DFML Ops
