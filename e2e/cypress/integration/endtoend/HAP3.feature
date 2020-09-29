Feature: Submit a medical claim that is happy, but financially ineligible, and is denied

  @setFeatureFlags
  @routeRequest
  Scenario: As a claimant, I should be able to start submitting a MedicalBasic claim through the portal
    Given I have a HAP3 claim to submit
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
  
  Scenario: As a CSR (Savilinx), I should be able to deny a claim based off financial ineligibility 
    Given I am logged in as a Savilinx CSR on the Fineos homepage
    When I search for the HAP3 application in Fineos
    Then I should find the specified claim
    Given I am on the claim case page
    When I click Adjudicate
    Given claim is financially ineligible
    Then I click Reject
    Given I am on the claim case page
    And claim is rejected
    When I click Deny
    And I select "Ineligible" for Denial Reason
    Then I add Financially Ineligible as reason in notes
    And I should confirm claim has been completed