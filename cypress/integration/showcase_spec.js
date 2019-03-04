describe('Showcase tests', function() {

  beforeEach(function () {
    cy.reset_db();
    cy.login_post_request('admin', 'admin')
    cy.visit('/');
    // We're forcing the click since drupal toolbar obscures the link
    // and due to cypress-io/cypress#2302 the auto-scrolling does not work
    cy.get('nav a[href="/data/fi/showcase"]').click({force: true});
  })

  it('Create a new minimal showcase, edit it and delete it', function() {
    const showcase_name = 'test_showcase';
    cy.create_new_showcase(showcase_name);
    cy.edit_showcase(showcase_name);

    // Delete and make sure it was deleted. Edit doesn't affect the showcase name in url, so the unmodified
    // name is passed as a parameter
    cy.delete_showcase(showcase_name);
  })

  it('Create a showcase with all fields', function() {
    const showcase_name = 'test_showcase_with_all_fields';
    const showcase_form_data = {
      '#field-title': showcase_name,
      '#s2id_autogen1': 'test {enter}',
      '#s2id_autogen2': 'test {enter}',
      '#s2id_autogen3': 'test {enter}',
      '#s2id_autogen4': 'test {enter}',
      '#s2id_autogen6': 'test',
      '#s2id_autogen7': 'test',
      '#field-author': 'test',
      '#field-author_website': 'www.example.com',
      '#field-application_website': 'www.example.com',
      '#field-store_urls': 'www.example.com',
      '#field-notes_translated-fi': 'test kuvaus',
      '#field-notes_translated-en': 'test description',
      '#field-notes_translated-sv': 'test beskrivning'
    };

    cy.create_new_showcase(showcase_name, showcase_form_data);
  })

  it('Creating an empty showcase fails', function() {
    cy.get('a[href="/data/fi/showcase/new"]').click();
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');

  })

  it('Cannot create showcase if logged out', function() {
    cy.logout();
    cy.visit('/');
    cy.get('nav a[href="/data/fi/showcase"]').click();
    cy.get('a[href="/data/fi/showcase/new"]').should('not.exist');
  })
})

