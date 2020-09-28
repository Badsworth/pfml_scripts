Feature: Submit a medical claim that is missing an HCP, and refer it to DFML

  @setFeatureFlags
  @routeRequest
  Scenario: As a claimant, I should be able to start submitting a GBR1 claim through the portal
    Given I have a GBR1 claim to submit
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
  
  Scenario: As a CSR (Savilix), I should be able to confirm that the HCP is missing
    Given I am logged in as a Savilinx CSR on the Fineos homepage
    When I search for the GBR1 application in Fineos
    Then I should find the specified claim
    Given I am on the claim case page
    Given I am on the tab "Documents"
    Then I should confirm HCP form is not present
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    Given I am on the tab "Evidence"
    When I click Manage Evidence
    Then I should confirm evidence is "invalid"
    Given I am on the claim case page
    And I am on the tab "Tasks"
    When I click Add
    And I search for Evidence Review
    Then I click Next
    And I click on Evidence Review 
    When I click Open
    Then I should start transferring task to DMFL
    Given I am on the Transfer to Dept page
    Then I should finish transferring task to DMFL
    Then I should confirm task assigned to DFML Ops
