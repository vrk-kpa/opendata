describe('Basic tests', function() {
  it('Opens frontpage!', function() {
    cy.visit("/")
  });

  it('Opens dataset page!', function() {
    cy.visit("/data/dataset")
  })
});

describe('Login page', function(){
  it('Logs in', function(){
    cy.login('admin', 'admin')
  })
  it('Logs out', function(){
    cy.login_post_request('admin', 'admin');
    cy.logout();
  })
});

