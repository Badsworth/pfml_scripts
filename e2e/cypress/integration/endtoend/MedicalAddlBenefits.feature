Feature: Submit a medical claim that involves additional benefits received

  @setFeatureFlags
  Scenario: As a claimant, I should be able to submit a MedicalAddlBenefits claim through the portal
    Given I have a MedicalAddlBenefits claim to submit
    And I am logged in as a claimant on the portal dashboard
    And I create an application
    When I submit the claim
    Then I should see a success page confirming my claim submission
    And I should be able to return to the portal dashboard

  Scenario: As a CSR, I should be able to find the claim in Fineos
    Given I am logged in as a CSR on the Fineos homepage
    When I search for the MedicalAddlBenefits application in Fineos
    Then I should find their claim in Fineos
