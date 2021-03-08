/* eslint-disable no-undef */

// set from terraform template
/* eslint-disable no-template-curly-in-string */
const URI = "${uri}";

/* eslint-disable promise/catch-or-return */
// test login
$browser
  .get(URI)
  .then(() => {
    return $browser.findElement($driver.By.linkText("Log in")).click();
  })
  .then(() => {
    return (
      $browser
        .findElement($driver.By.name("username"))
        // Portal credentials are managed in New Relic secrets.
        // Reach out to a Mass admin to have them changed.
        // Username and password should be changed when Andrew Lomax leaves.
        .sendKeys($secure.PORTAL_USERNAME)
    );
  })
  .then(() => {
    return (
      $browser
        .findElement($driver.By.name("password"))
        // Portal credentials are managed in New Relic secrets.
        // Reach out to a Mass admin to have them changed.
        // Username and password should be changed when Andrew Lomax leaves.
        .sendKeys($secure.PORTAL_PASSWORD)
    );
  })
  .then(() => {
    return $browser
      .findElement($driver.By.xpath("//button[@type='submit']"))
      .click();
  })
  .then(() => {
    return $browser.findElement($driver.By.linkText("Create an application"));
  });
