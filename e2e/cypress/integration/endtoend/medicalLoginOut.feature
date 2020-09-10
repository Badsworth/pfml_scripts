Feature: Start submittin a medical claim - Logout/Login - complete submission

  @setFeatureFlags
  Scenario: As a claimant, I should be able to log off then login and continue submitting a claim through the portal
    Given I have a MedicalBasic claim to submit
    And I log in as a claimant on the portal dashboard
    And I create an application
    And I am on the claims Checklist page
    And I click on the checklist button called "Verify your identity"
    And I have my identity verified "normal"
    When I log out
    And I log in as a claimant on the portal dashboard
    And I return to my previous application
    Then I should see any previously entered data
    And I have my identity verified "continued"
    Given I am on the claims Checklist page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I finish submitting the claim based on its type
    Given I am on the claims Checklist page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims Checklist page
    When I click on the checklist button called "Report other leave and benefits"
    Then I report other benefits
    Given I am on the claims Checklist page
    When I click on the checklist button called "Add payment information"
    Then I add payment info
    And I should review and submit the application
    Given I am on the claims Review page
    Then I should have confirmed that information is correct
    Given I am on the claims Confirm page
    Then I should have agreed and successfully submitted the claim
    And I should be able to return to the portal dashboard

  Scenario: As a CSR, I should be able to find the claim in Fineos
    Given I am logged in as a CSR on the Fineos homepage
    When I search for the MedicalBasic application in Fineos
    Then I should find their claim in Fineos
