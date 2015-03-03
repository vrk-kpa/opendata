function SelectByName(event){
    console.log(event)
    if (!event.added.created || event.added.created == false){
        $('#field-url').val(window.location.origin + "/data/dataset/" + event.added.id)
        $('#field-title').val(event.added.text)

    }
    else{

    }
}