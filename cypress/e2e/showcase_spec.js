describe('Showcase tests', function() {

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user('showcase_test_organization', 'test-publisher', true);
  })

  describe('Showcase creation tests', function(){

    it('Create a new minimal showcase, edit it and delete it', function() {
      cy.add_showcase_user();
      const showcase_name = 'test_showcase';
      cy.create_new_showcase(showcase_name);
      cy.edit_showcase(showcase_name);
  
      // Delete and make sure it was deleted. Edit doesn't affect the showcase name in url, so the unmodified
      // name is passed as a parameter
      cy.delete_showcase(showcase_name);
    });
  
    it('Create a showcase with all fields', function() {
      cy.add_showcase_user();
      const showcase_name = 'test_showcase_with_all_fields';
      const showcase_form_data = {
        '#field-title_translated-fi': showcase_name,
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test']},
        '#s2id_autogen2': {type: 'select2', values: ['test']},
        '#s2id_autogen3': {type: 'select2', values: ['test']},
        '#field-author': {type: 'select2', values: ['test']},
        '#field-author_website': 'www.example.com',
        '#field-application_website': 'www.example.com',
        '#field-store_urls': 'www.example.com',
        '#field-notes_translated-fi': 'test kuvaus',
        '#field-notes_translated-en': 'test description',
        '#field-notes_translated-sv': 'test beskrivning'
      };
  
      cy.create_new_showcase(showcase_name, showcase_form_data);
    });
  
    it('Cannot create showcase if logged out', function() {
      cy.visit('/');
      cy.get('nav a[href="/data/fi/showcase"]').click();
      cy.get('a[href="/data/fi/showcase/new"]').should('not.exist');
    })
  
    it('Fill showcase form with anonymous user', function() {
      cy.visit('/');
  
      // Create admin user
      cy.login_post_request('admin', 'administrator')
      cy.visit('/data/fi/dataset')
      cy.logout_request()
  
  
      cy.get('nav a[href="/data/fi/showcase"]').click();
      cy.create_new_showcase_using_public_form("testisovellus");
      cy.get('nav a[href="/data/fi/showcase"]').click();
      cy.get("testisovellus").should('not.exist'); // The showcase should not be visible on the list
    })
  
    it('Add dataset to showcase and edit showcase with dataset', function() {
  
      cy.add_showcase_user();
      cy.logout_request();
  
      // Organization
      cy.login_post_request('admin', 'administrator');
      const organization_name = 'testi_organisaatio_2';
      cy.create_new_organization(organization_name);
      cy.approve_organization(organization_name);
      cy.visit(`/data/fi/organization/member_new/${organization_name}`);
      cy.get('#s2id_username').click();
      cy.get('#s2id_autogen1_search').type('test-publisher', {force: true}).wait(1000).type('{enter}');
      cy.get('#s2id_role').click();
      cy.get('#s2id_autogen2_search').type('admin', {force: true}).wait(1000).type('{enter}');
      cy.get('button[type=submit]').click();
      cy.logout_request();
  
  
      cy.login_post_request('test-publisher', 'test-publisher');
  
      cy.visit(`/data/fi/organization/${organization_name}`)
  
      // Dataset linked to organization
      const dataset_form_data = {
        "#field-title_translated-fi": 'test dataset',
        '#field-notes_translated-fi': 'Dataset test description',
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
        '#field-maintainer': 'test maintainer',
        '#field-maintainer_email': 'test.maintainer@example.com',
      }
      cy.get('nav a[href="/data/fi/dataset"]').click();
      // Dataset will be created with default resource_form_data
      const resource_form_data = null;
      const showcase_name = "test-showcase";
      cy.create_new_dataset("test dataset", dataset_form_data, resource_form_data, organization_name);
  
      // Create a showcase with dataset
      cy.create_new_showcase(showcase_name);
      cy.get(`a[href="/data/fi/showcase/edit/${showcase_name}"]`).click();
      cy.get(`a[href="/data/fi/showcase/manage_datasets/${showcase_name}"]`).click();
      //There should be only one checkbox, because there is only one dataset
      cy.get("tbody td input").first().click({force: true});
      cy.get('button[name="bulk_action.showcase_add"]').click()
      //Remove button should exist after adding the dataset
      cy.get('button[name="bulk_action.showcase_remove"')
      cy.get(`a[href="/data/fi/showcase/${showcase_name}"]`).first().click();
      cy.edit_showcase(showcase_name);
    })
  
    it('Submitting empty showcase notifies about all mandatory fields', function (){
      cy.visit('/')
  
      // Create admin user
      cy.login_post_request('admin', 'administrator')
      cy.visit('/data/fi/dataset')
      cy.logout_request()
  
      cy.get('ul.nav a[href="/data/fi/showcase"]').click()
      cy.get('a[href="/data/fi/submit-showcase"]').click()
      cy.get('button[name=save]').click()
  
      cy.get('.error-block').should('have.length', 5)
      cy.get('.error-block').siblings('input[name=title]').should('exist')
      cy.get('.error-block').siblings('input[name=author]').should('exist')
      cy.get('.error-block').siblings('textarea[name=notes_translated-fi]').should('exist')
      cy.get('.error-block').siblings('textarea[name=notes_translated-sv]').should('exist')
      cy.get('.error-block').siblings('textarea[name=notes_translated-en]').should('exist')
    });
  
    it('Submitting showcase with non-existing dataset adds notification to notes', function (){
      cy.visit('/')
  
      // Create admin user
      cy.login_post_request('admin', 'administrator')
      cy.visit('/data/fi/dataset')
      cy.logout_request()
  
      cy.get('ul.nav a[href="/data/fi/showcase"]').click()
  
      const showcase_data = {
        "#field-title": "nonexisting_dataset",
        '#field-notes_translated-fi': 'Showcase test description',
        '#notifier': 'test author',
        '#notifier_email': 'test@example.com',
        '#field-author': 'Author of showcase',
        // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test_keyword']}
      }
  
      cy.create_new_showcase_using_public_form("nonexisting_dataset", showcase_data);
      cy.login_post_request('admin', 'administrator')
      cy.visit('/data/fi/showcase/nonexistingdataset')
      cy.get('.notes').should('contain', "Seuraavaa aineistoa ei voitu automaattisesti liittää sovellukseen:")
  
    })

  });

  it('Showcase should not render as dataset', function () {
    cy.add_showcase_user();
    cy.create_new_showcase("test_showcase_render");

    cy.visit('/data/fi/dataset/test_showcase_render')
    cy.get(".dataset-container").should('exist')

  })
});
