describe("Organization tests", function() {

  beforeEach(function(){
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
  });

  it('Creates organization', function(){
    cy.visit('/');
    cy.get('nav a[href="/data/fi/organization"]').click();
    cy.get('a[href="/data/fi/organization/new"]').click();

    cy.get("input[name='title_translated-fi']").type('test organization');

    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get("input[name='name']").type('test-organization');

    cy.get('button[name="save"]').click();

    cy.url().should('/data/fi/organization/test-organization');

  })
});
