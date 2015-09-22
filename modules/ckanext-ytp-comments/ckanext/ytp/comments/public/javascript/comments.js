function ShowCommentForm(id){
    $("#" + id).removeClass('hidden');
}

function updateSubscription(dataset_id) {


    var checked = $('#notification-subscribe').is(':checked');

    console.log(checked);

    if (checked) {
        var controllerUrl = dataset_id + "/comments/subscription/add";
    }
    else {
        var controllerUrl = dataset_id + "/comments/subscription/remove";
    }


    $.ajax({
        type: "POST",
        url: controllerUrl,
        data: { checked : checked },
        success: function(data) {
            console.log("success!! subscribe: " + checked);
        },
        error: function() {
        },
        complete: function() {
        }
    });

}
