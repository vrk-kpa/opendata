function SelectByName(event){
    if (!event.added.created || event.added.created == false){
        $('#field-url').val(ckan.url('dataset/' + event.added.id));
        $('#field-title').val(event.added.text)
    }
}