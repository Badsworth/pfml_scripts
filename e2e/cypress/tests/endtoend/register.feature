Feature: Register new account

  @portal
  Scenario: As a portal user, I should be able to register a new account
    Given I am an anonymous user on the portal homepage
    When I submit the account registration form
    And I log into the portal
    And I accept the terms of service
    Then I should be logged in
