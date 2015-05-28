<?php $count = 0; ?>
<?php foreach ($fields as $id => $field): ?>
      <?php if ($count == 1){
        print '<div class="media-body">';
    }
    ?>
    <?php print $field->content; ?>
    <?php if ($count == 2){
        print '</div>';
    }
    ?>

<?php $count++; ?>
<?php endforeach; ?>