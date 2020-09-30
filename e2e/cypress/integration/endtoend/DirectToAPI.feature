Feature: Submit a <Scenario> claim directly to API

Scenario: As a tester - I can submit and adjudicate directly to the API
  Given I submit "HAP1" claim directly to API
  Then I should adjudicate the "HAP1" claim properly in Fineos