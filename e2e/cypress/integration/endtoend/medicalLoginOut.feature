Feature: Start submittin a medical claim - Logout/Login - complete submission

  @setFeatureFlags
  Scenario: As a claimant, I should be able to log off then login and continue submitting a claim through the portal"
    Given I have a MedicalBasic claim to submit
    And I am logged in as a claimant on the portal dashboard
    And I create an application
    When I log out and log back into the portal
    And I return to my previous application
    Then I should see any previously entered data
    And I should be able to finish submitting the claim
    Then I should see a success page confirming my claim submission
    And I should be able to return to the portal dashboard

  Scenario: As a CSR, I should be able to find the claim in Fineos
    Given I am logged in as a CSR on the Fineos homepage
    When I search for the MedicalBasic application in Fineos
    Then I should find their claim in Fineos
