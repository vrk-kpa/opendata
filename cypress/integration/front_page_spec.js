describe('Basic tests', function() {
  it('Opens frontpage!', function() {
    cy.visit("/")
  });

  it('Opens dataset page!', function() {
    cy.visit("/data/dataset")
  })
});

describe('Login page', function(){
  it('sets auth cookie when logging in via form submission', function (){
    const username = 'test-user';
    const password = 'test-user';

    cy.visit('/user/login');

    cy.get('input[name=name]').type(username);
    cy.get('input[name=pass]').type(password);
    cy.get('#edit-submit').click();

    cy.url().should('include', '/fi/user');

    cy.getCookies().should('have.length', 1).then((cookies) => {
      expect(cookies[0]).to.have.property('name').to.match(/^SESS/);
    })
  });

  it('Removes auth cookie on logout', function(){
    const username = 'test-user';
    const password = 'test-user';

    cy.request({
      method: 'POST',
      url: '/user/login',
      form: true,
      body: {
        name: username,
        pass: password,
        form_id: 'user_login_form'
      }
    });


    cy.visit('/user/logout');

    cy.url().should('eq', Cypress.config().baseUrl + '/fi');
    cy.getCookies().should('have.length', 0);
  })
});

