function userSorter(a,b){
    var a_val = $(a)[2].text;
    var b_val = $(b)[2].text;
    if ( a_val < b_val) return -1;
    if ( a_val > b_val) return 1;
    return 0;
}