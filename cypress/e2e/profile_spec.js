describe('Profile page tests', function(){
    const test_organization = 'dataset_test_organization';

    before(function(){
        cy.reset_db();
        cy.create_organization_for_user(test_organization, 'test-user', true);
    });


    describe('Datasets on profile page', function(){
        const profile_dataset_name = "my_profile_dataset";

        before(function(){
            cy.login_post_request('test-user', 'test-user')
            cy.create_new_dataset(profile_dataset_name);
        });

        beforeEach(function(){
            cy.login_post_request('test-user', 'test-user')
        });

        it('Created datasets are visible on users profile', function(){
            cy.visit('/data/dataset');
            cy.get('[href="/fi/profile"] > span').click();
            cy.get('.dataset-content > .align-items-center > .dataset-heading > a').should('have.text', profile_dataset_name);
          });

        it('Dataset can be opened from the profile page', function(){
            cy.get('[href="/fi/profile"] > span').click();
            cy.get('.dataset-content > .align-items-center > .dataset-heading > a').should('contain.text', profile_dataset_name).click();
            cy.location('pathname').should('contain', `/dataset/${profile_dataset_name}`);
            cy.get('.dataset-title').should('contain.text', profile_dataset_name);
            cy.get('.resource-item__info__title').should('contain.text', 'test data').click();
            cy.location('pathname').should('contain', `/dataset/${profile_dataset_name}/resource`);
        });

        it('Deleted datasets are not visible on users profile', function(){
            cy.visit(`/data/fi/dataset/${profile_dataset_name}`);
            cy.delete_dataset(profile_dataset_name);
            cy.visit('/data/dataset');
            cy.get('[href="/fi/profile"] > span').click();
            cy.get('.primary > .module > .module-content > .empty').should('contain.text', 'Käyttäjä ei ole luonut tietoaineistoja.');
        });

    });

    describe('User settings', function(){

        // Remnant from general_spec.js
        // This test currently does not work as intended and will be skipped until refactored properly
        it.skip('User sets their default language', function(){
            cy.visit('/');
            cy.login_post_request('test-user', 'test-user');
            cy.contains('Tietoaineistot').click();
            cy.contains('Minun tietoaineistoni').click();
            cy.contains('Käyttäjätilin asetukset').click();
            // Change language to Svedish
            cy.get('select').eq(0).select('sv').should('have.value', 'sv');
            cy.get('button[name="op"]').click();
            
            cy.visit('/');
            cy.contains('Tietoaineistot').click()
            cy.contains('Minun tietoaineistoni').click()
            cy.contains('Käyttäjätilin asetukset').click()
            // Change lanquage to English
            cy.get('select').eq(0).select('en').should('have.value', 'en') //[name="preferred_langcode"]').click();
            cy.get('button[name="op"]').click();
            
            cy.visit('/');
            cy.contains('Tietoaineistot').click()
            cy.contains('Minun tietoaineistoni').click()
            cy.contains('Käyttäjätilin asetukset').click()
            cy.get('select').eq(0).select('fi').should('have.value', 'fi') //[name="preferred_langcode"]').click();
            cy.get('button[name="op"]').click();
        });

    });

});