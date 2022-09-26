describe('Articles page', function() {

  it("Navigate to article page", function(){
    cy.visit("/");
    cy.get('.nav > :nth-child(5) > a').click();
    cy.location('pathname', {timeout: 60000}).should('contain', `/artikkelit`);
  });

  // This is an old test that should be expanded upon at some point
  it("Search for an article", function(){
    cy.visit("/fi/artikkelit");
    const options = {scrollBehavior: 'center'};
    cy.get('#avoindata-articles-search-input').click(options);
    cy.get('#avoindata-articles-search-input').type('helsinki');
    cy.get('#avoindata-articles-search-btn').click(options);
  });

})
