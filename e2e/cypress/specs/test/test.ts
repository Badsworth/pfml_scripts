describe("Test 1", () => {
  const a = it("Should do a thing",  () => {
    cy.visit("/");
    expect("a").to.equal("b");
  });
});
