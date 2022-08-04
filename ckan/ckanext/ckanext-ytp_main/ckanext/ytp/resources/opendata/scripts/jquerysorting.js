$(document).ready(function()
    {
        $("#report-table").tablesorter({
            dateFormat: "pt",
        });
        $(".js-auto-submit").change(function () {
            $(this).closest("form").submit();
        });
    }
);
