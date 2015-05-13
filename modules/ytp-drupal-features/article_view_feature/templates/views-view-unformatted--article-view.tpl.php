<?php
    if (!empty($title)): ?>
        <h3><?php print $title; ?></h3>
    <?php endif; ?>

    <div class="row">
        <div class="col-lg-2 article-list-header"><?php print t('News') ?></div>
    </div>
    <div class="article-list">

        <?php if (count($rows) >= 1): ?>
            <div class="row">
                <div class="col-lg-12 col-md-12 col-sm-12">
                    <div class="article">
                        <div<?php if ($classes_array[0]) { print ' class="' . $classes_array[0] .'"'; } ?>>
                            <?php print $rows[0]; ?>
                        </div>
                    </div>
                </div>
            </div>
        <?php endif ?>

        <div class="row">
        <?php for($i = 1, $size = count($rows); $i < $size; ++$i) { ?>

            <div class="col-lg-6 col-md-6 col-sm-6 <?php if($i % 2 != 0):?>left <?php else: ?>right <?php endif ?>">
                <div class="article">
                    <div<?php if ($classes_array[0]) { print ' class="' . $classes_array[0] .'"'; } ?>>
                        <?php print $rows[$i]; ?>
                    </div>
                </div>
            </div>

            <?php if ($i  % 2 == 0) { ?>
                </div>
                <div class="row">
            <?php } ?>

        <?php } ?>
        </div>
    </div>

