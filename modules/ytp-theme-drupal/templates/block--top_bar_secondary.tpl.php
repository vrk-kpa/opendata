<?php
    global $language;
?>
<div class="tutorial-box-content">
<?php

    global $user;

    if (!(bool) $user->uid){ ?>
    <div class="media">
        <div class="media-left">
            <img src="/resources/images/frontpage/rekisteroidy_125x125.png" class="media-object"/>
        </div>
        <div class="media-body">
            <h1 class="media-heading"><?php print t('Getting started') ?></h1>
            <p><?php print t('Opendata.fi allows you to find open datasets, and to publish and manage your own.') ?></p>

            <div class="tutorial-register"><?php print t('<a href="/en/user/register">Register</a>')?></div>
            <div class="tutorial-signin"><?php print t('<a href="/en/user/login">Sign in</a> <a class="pull-right" href="/en/user/password">Forgot your password?</a>') ?></div>
        </div>
    </div>
    <?php
    }
    else{
        $temp = user_load($user->uid);
        $not_in_organization = true;
        if ( isset($temp->field_ckan_api_key['und']) && isset($temp->field_ckan_api_key['und'][0]) && isset($temp->field_ckan_api_key['und'][0]['value'])){
            $url = 'https://localhost/data/api/3/action/organization_list_for_user?permission=read';
            $options = array(
              'method' => 'GET',
              'headers' => array('Authorization' => $temp->field_ckan_api_key['und'][0]['value'])
            );
            $result = drupal_http_request($url, $options);
            $json = drupal_json_decode($result->data);
            if ( count($json['result']) > 1 ){
                $not_in_organization = false;
            ?>



            <?php }
        }

            if ($not_in_organization == true){ ?>
             <div class="media">
                    <div class="media-left">
                        <img src="/resources/images/frontpage/liity_organisaatioon_125x125.png" class="media-object"/>
                    </div>
                    <div class="media-body">
                        <h1 class="media-heading"><?php print t('Not yet a member of an organization?') ?></h1>
                        <p><?php print t('Join an organization in the <a href="/data/en/organization">Data Producers</a> page, and publish data, tools and guidelines. You can also publish applications or services that utilize open data.') ?></p>
                    </div>
                </div>

            <?php }
            else{?>
            <div class="media">
            <div class="media-left">
                <img src="/resources/images/frontpage/julkaise_aineistoja_125x125.png" class="media-object"/>
            </div>
            <div class="media-body">
                <h1 class="media-heading"><?php print t('Publish data') ?></h1>

                <p><?php print t('Publish data, tools and guidelines for others to use. You can also publish your applications.') ?></p>
                <p><?php print t('Start publishing data from the Publish data page.') ?></p>
                <p><?php print t('If you are interested in using a programmable interface, our API documentation will provide an introduction.') ?></p>
            </div>
        </div>
<?php
            }
        ?>

<?php }



    ?>


</div>
