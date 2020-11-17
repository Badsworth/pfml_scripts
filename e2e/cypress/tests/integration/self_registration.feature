Feature: Register new paid leave admin account from the employer portal.

  @portal
  Scenario: As a portal user, I should be able to register a employer account
    Given I am an anonymous employer user on the portal homepage
    When I submit the employer registration form
    And I log into the employer portal
    And I accept the terms of service
    Then I should be logged in
