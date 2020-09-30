Feature: Submit and accept HAP2 claim: Simple claim, out of state resident

  @portal
  Scenario: As a claimant, I should be able to submit a claim (HAP2) through the portal
    Given I begin the process to submit a "HAP2" claim
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
  Scenario: As a CSR (Savilinx), I should be able to Approve a HAP2 claim submission
    Given I search for the proper claim in Fineos
    Given I am on the tab "Documents"
    Then I should confirm "OOS ID form" is not present
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    Given I am on the tab "Evidence"
    When I click Manage Evidence
    Then I should confirm evidence is "valid"
    When I highlight ID Proof
    And I click Manage Evidence
    Then I should confirm evidence is "invalid due to missing identity documents"
    Given I am on the tab "Manage Request"
    Then I click Reject
    Given I am on the claim case page
    And claim is rejected
    When I click Deny
    Given I complete claim Denial for "Insufficient Certification"
    And I should confirm claim has been completed



