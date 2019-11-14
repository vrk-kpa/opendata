describe('Category tests', function () {
  beforeEach(function () {
  cy.reset_db();
  });

  it('Add dataset to category during dataset creation', function () {
    cy.login_post_request('admin', 'administrator');

    const category_name_1 = 'test_category_1';
    const category_name_2 = 'test_category_2';

    cy.create_category(category_name_1);
    cy.create_category(category_name_2);

    cy.logout();

    cy.login_post_request('test-user', 'test-user')
    const dataset_name = 'category_test';
    const dataset_form_data = {
      "#field-title_translated-fi": dataset_name,
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'test.maintainer@example.com'
    };

    cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.get('a[href="/data/fi/dataset/new"]').click();
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(dataset_name);
    cy.fill_form_fields(dataset_form_data);
    cy.get('#field-categories-' + category_name_1 + ' ~ span').click();
    cy.get('button[name=save]').click();

    const resource_form_data = {
      "#field-name_translated-fi": 'test data',
      '#field-image-url': 'http://example.com'
    };

    cy.contains('a', 'Linkki').click();
    cy.fill_form_fields(resource_form_data);
    cy.get('button[name=save]').contains('Valmis').click();

    cy.get('a[href="/data/fi/dataset/groups/' + dataset_name + '"]').click();

    cy.get('a[href="/data/fi/group/' + category_name_1 + '"]').should('exist');
  })
});
