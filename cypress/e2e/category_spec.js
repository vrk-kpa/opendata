describe('Category tests', function () {

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user('category_test_organization', 'test-user', true);
  });


  it('Create a category as an admin', function(){
    cy.login_post_request('admin', 'administrator');
    const category_name_1 = 'test_category_1';
    cy.create_category(category_name_1);

    //check if the category was created succesfully
    cy.visit('/data/group')
    cy.get('.media-view').should('contain.text', category_name_1);

  });

  it('Normal user cant create a category', function(){
    cy.login_post_request('test-user', 'test-user');

    // new category button should not be visible
    cy.visit('/data/group/');
    cy.get('.btn').should('not.exist');

    // direct url should also give 403 forbidden
    cy.visit(('/data/group/new'), {
      failOnStatusCode: false
    });
    cy.contains('403 Forbidden');
  });

  it('Anonymous user cant create a category', function(){
    // new category button should not be visible
    cy.visit('/data/group/');
    cy.get('.btn').should('not.exist');

    // direct url should also give 403 forbidden
    cy.visit(('/data/group/new'), {
      failOnStatusCode: false
    });
    cy.contains('403 Forbidden');
  });


});
