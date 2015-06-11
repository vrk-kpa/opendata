<?php
    if ( substr($output, -1) == '>' ){
        $output =  substr($output, 0, -2) . 'class="media-object"' . substr($output, -1);
    }
?>



<?php print $output; ?>


