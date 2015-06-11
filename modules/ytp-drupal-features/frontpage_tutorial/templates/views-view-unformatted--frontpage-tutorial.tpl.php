<?php if (!empty($title)): ?>
  <h3><?php print $title; ?></h3>
<?php endif; ?>
<?php foreach ($rows as $id => $row): ?>
  <div<?php if ($classes_array[$id]) { print ' class="' . $classes_array[$id] .'"';  } ?>>
    <div class="col-xs-12 col-md-12 col-lg-4 guide-box">
    <div class="media">
      <?php print $row; ?>
    </div>
    </div>
  </div>
<?php endforeach; ?>
