describe('Guide page tests', function() {

  it.skip('Navigation', function(){
    // The navigation template will be changed soon, so write this test after that
  });

  // Without login 
  it('Open guide without logging in', function () {
    cy.visit("/fi/kayttoohjeet");
  });
  
  // With login
  it('Open guide while logged in', function () {
    cy.login_post_request('test-user', 'test-user');
    cy.visit("/fi/kayttoohjeet");
  });

  //TODO translation tests

})
