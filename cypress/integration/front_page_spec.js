describe('Basic tests', function() {
  it('Opens frontpage!', function() {
    cy.visit("/")
  });

  it('Opens dataset page!', function() {
    cy.visit("/data/dataset")
  })
});

