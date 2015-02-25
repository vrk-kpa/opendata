function userSorter(a,b){
    var a_val = $(a)[2].text.toLowerCase();
    var b_val = $(b)[2].text.toLowerCase();
    if ( a_val < b_val) return -1;
    if ( a_val > b_val) return 1;
    return 0;
}

function lowercaseSorter(a,b){
    var a_val = a.toLowerCase();
    var b_val = b.toLowerCase();
    if ( a_val < b_val) return -1;
    if ( a_val > b_val) return 1;
    return 0;
}