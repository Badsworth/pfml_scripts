Feature: Submit a medical claim and adjucation approval - HAP1

  @setFeatureFlags
  @routeRequest
  Scenario: As a claimant, I should be able to submit a claim (HAP1) through the portal
    Given I have a HAP1 claim to submit
    And I log in as a claimant on the portal dashboard
    And I create an application
    And I am on the claims "start" page
    And I start an application
    And I have a claim ID
    And I am on the claims "checklist" page
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

Scenario: As a CSR (Savilinx), I should be able to Approve a HAP1 claim submission 
    Given I am logged in as a Savilinx CSR on the Fineos homepage
    When I search for the HAP1 application in Fineos
    Then I should find the specified claim
    Given I am on the claim case page
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



