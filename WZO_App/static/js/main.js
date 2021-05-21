
// === Env-Var === //
const ini_lat = 52.405132
const ini_long = 9.735823
const ini_zoom = 5
var eort_markers = null;
var circle_markers = L.layerGroup();
var ikz = null;
const Toast = Swal.mixin({
    toast: true,
    position: 'bottom-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true
});
myMarker = L.Marker.extend({
    options: {
        EortID: 'Custom data!'
    }
})
var Rules = new RuleWT()
var cursorlat = null;
var cursorlng = null;

var mymap = L.map('mapid').setView([ini_lat, ini_long], ini_zoom)
mymap.addEventListener('mousemove', function (ev) {
    cursorlat = ev.latlng.lat;
    cursorlng = ev.latlng.lng;
});
var ci = new ColorIndex()

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 20,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'sk.eyJ1IjoiYWVqc2k1IiwiYSI6ImNrbjIzNmVuaTBjNHQycG1udDQ4dnMwNG4ifQ.K4KH3tZI0KDQa6L5d7W2cw'
}).addTo(mymap);

$(document).ready(function(){

    $('.arrow-up').click(function(){
        $(this).toggleClass('rotate-540');
        $('.control-form').toggleClass('opacity-null');
        $('.control-container').toggleClass('control-container-small');
    });

    $('#query_exe').click(function(){
        if(eort_markers !=null){
            mymap.removeLayer(eort_markers)
        }
        eort_markers = L.layerGroup()
        var q = create_query_string();
        var url = '/api/v1/eortlist/';
        if(q==null){
            Toast.fire({
                icon: 'error',
                title: 'Kein Filter',
                text: 'Mind. 1 Filter muss gesetzt sein, ansonsten explodiert dein PC'
            });
            return
        }else{
            url = url + q;
        }
        console.log(url)
        $.ajax({
            type: 'GET',
            url: url,
            success: function (result, status, xhr) {
                create_eorte(result);
                $('.arrow-up').toggleClass('rotate-540');
                $('.control-form').toggleClass('opacity-null');
                $('.control-container').toggleClass('control-container-small');
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    })

    $('.controls-close-eort').click(function () {
        close_slide_eort()
    })
    $('.controls-close-veh').click(function () {
        close_slide_veh()
    })  
    $('.controls-close-rule').click(function(){
        close_slide_rule()
    })
    var wtrulesopen = false;
    $('#show-rules').click(function(){
        if(!wtrulesopen){
            Rules.draw();
        }
        wtrulesopen = true;
        $('.slider-rule-data').removeClass('height0');
    })
    var edit_mode = false;
    $('#new_circle').click(function(){
        edit_mode = true;
    })

    $('.li-eraser.active').click(function(){
        eraser(false);
        if (circle_markers != null) {
            mymap.removeLayer(circle_markers);
            circle_markers = L.layerGroup();
        }
    })

    $('#mapid').click(function(){
        if(edit_mode){
            eraser(true);
            var circle = L.circle([cursorlat, cursorlng], { radius: 500, color: ci.get(), opacity: 0.8 }).bindPopup();
            circle.on('click', function(){
                circle_click(circle)
            })
            circle_markers.addLayer(circle);
            circle_markers.addTo(mymap);
            edit_mode = false;
        }
    })
    $('.rtable-search-input').on('keyup', function(){
        doSearch();
    })

    var ruletbl = document.getElementById('ruletbl-wtrules');
    ruletbl.addEventListener('scroll', function(event){
        var element = event.target;
        if (element.scrollHeight - element.scrollTop === element.clientHeight) {
            Rules.next_page()
        }
    })

    $(document).on('click', '.rrule-draw', function(){
        eraser(true);
        var lat = $(this).parents('.ruletbl-tr').find('.ruletbl-col2').text()
        var lng = $(this).parents('.ruletbl-tr').find('.ruletbl-col3').text()
        var radius = $(this).parents('.ruletbl-tr').find('.ruletbl-col4').text() * 1000
        var wst = $(this).parents('.ruletbl-tr').find('.ruletbl-col13').text()
        var circle = L.circle([lat, lng], { radius: radius, color: ci.get(wst), opacity: 0.8 }).bindPopup();
        circle.on('click', function () {
            circle_click(circle, wst)
        })
        circle_markers.addLayer(circle);
        circle_markers.addTo(mymap);
    })

    $(document).on('click', '.rrule-draw-all', function () {
        eraser(true);
        $('#ruletbl-wtrules .ruletbl-tr').each(function(){
            var lat =$(this).find('.ruletbl-col2').text()
            var lng = $(this).find('.ruletbl-col3').text()
            var radius = $(this).find('.ruletbl-col4').text() * 1000
            var wst = $(this).find('.ruletbl-col13').text()
            var circle = L.circle([lat, lng], { radius: radius, color: ci.get(wst), opacity: 0.8 }).bindPopup();
            circle.on('click', function () {
                circle_click(circle, wst)
            })
            circle_markers.addLayer(circle);
            circle_markers.addTo(mymap);
        })
    })
});
function eraser(on){
    if(on){
        $('.li-eraser').removeClass('disabled');
        $('.li-eraser').addClass('active');
    }else{
        $('.li-eraser').addClass('disabled');
        $('.li-eraser').removeClass('active');
    }
}

function circle_click(e, wst=null){
    console.log(e)
    var $markup = $(
        "<div>"+
            "<div class='circle-popup-div'><span class='circle-popup-lat'></span><span class='circle-popup-lng'></span><span class='circle-popup-radius'></span></span><span class='circle-popup-wst'></span></div>"+
            "<div class='circle-range'>"+
                "<input type='range' class='form-range circle-popup-range' min='10' max='30000' value='" + e.getRadius() + "' id='circle_"+ e._leaflet_id +"'>"+
            "</div>"+
            "<span class='delete_circle' id='circle_delete_"+ e._leaflet_id +"'>Löschen</span>"+
        "</div>"
    )
    $markup.find('.circle-popup-lat').text("Lat:" + Number(e.getLatLng()["lat"]).toFixed(6));
    $markup.find('.circle-popup-lng').text("Lng:" + Number(e.getLatLng()["lng"]).toFixed(6));
    $markup.find('.circle-popup-radius').text("Radius:" + Number(e.getRadius()).toFixed(1) + "Meter");
    if(wst!=null){
        $markup.find('.circle-popup-wst').text("Werkstatt:" + wst);
    }
    var selector = '#circle_'+ e._leaflet_id;
    $(document).on('input',selector,function(){
        var p = $(this).parents('.leaflet-popup-content');
        p.find('.circle-popup-radius').text("Radius:" + $(this).val() + "Meter");
        e.setRadius($(this).val());
    })
    var selector2 = '#circle_delete_' + e._leaflet_id;
    $(document).on('click', selector2, function () {
        mymap.removeLayer(e)
    })
    e._popup.setContent($markup.html())
}

var delayTimer;
function doSearch() {
    clearTimeout(delayTimer);
    delayTimer = setTimeout(function () {
        console.log("Feuer")
        $('.ruletbl-loader').removeClass('ruletbl-loader-noshow');
        $('.ruletbl-tbody').empty();
        var q = create_query_string_rules()
        console.log(q)
        Rules.reset_page(q);
        Rules.get_rules();
    }, 2000);
}

function create_query_string_rules() {
    var query = '?'
    var make = $('#ruletbl-inp-make').val().replace(', ', ',')
    if (make != '') {
        query = query + '&make=' + make
    }
    var wst = $('#ruletbl-inp-wst').val().replace(' ', '')
    if (wst != '') {
        query = query + '&kuerzel=' + wst
    }
    var address = $('#ruletbl-inp-address').val().replace(' ', '')
    if (address != '') {
        query = query + '&address=' + address
    }
    var note = $('#ruletbl-inp-note').val().replace(' ', '')
    if (note != '') {
        query = query + '&note=' + note
    }
    query.replace(' ', '+')
    if(query=='?'){
        return null
    }
    return encodeURI(query)
}
    
function close_slide_rule(){
    $('.slider-rule-data').addClass('height0');
}

function close_slide_eort(){
    $('.slider-eort-data').addClass('width0');
    is_open= false;
    if(vtbl){
        vtbl.destroy();
    }
}
function close_slide_veh() {
    $('.slider-vehicle-data').addClass('width0');
    veh_is_open = false;
    if (wtbl) {
        wtbl.destroy();
    }
}

function create_query_string(){
    var query = '?'
    var region = $('#inp_region').val().replace(', ',',')
    if(region != ''){
        query = query + '&region=' + region
    }
    var name = $('#inp_name').val().replace(' ', '%20')
    if (name != '') {
        query = query + '&name=' + name
    }
    var zip = $('#inp_zip_code').val().replace(' ', '%20')
    if (zip != '') {
        query = query + '&zip_code=' + zip
    }
    var city = $('#inp_city').val().replace(' ', '%20')
    if (city != '') {
        query = query + '&city=' + city
    }
    var ikz = $('#inp_ikz').val().replace(' ', '%20')
    if (ikz != '') {
        query = query + '&ikz=' + ikz
    }
    var objno = $('#inp_objno').val().replace(' ', '%20')
    if (objno != '') {
        query = query + '&objno=' + objno
    }
    var make = $('#inp_make').val().replace(' ', '%20')
    if (make != '') {
        query = query + '&make=' + make
    }
    var model = $('#inp_model').val().replace(' ', '%20')
    if (model != '') {
        query = query + '&model=' + model
    }
    var reg_date = $('#inp_reg_date').val()
    if (reg_date != '') {
        query = query + '&reg_date=gte__' + reg_date
    }
    var age = $('#inp_age').val().replace(' ', '%20').replace('.','').replace(',', '')
    if (age != '') {
        var operator = $('#operator').val()
        if(operator =='='){
            query = query + '&age=' + age
        } else if (operator == '<'){
            query = query + '&age=lte__' + age
        } else if (operator == '>') {
            query = query + '&age=gte__' + age
        }
    }
    var service_contract = $('#inp_service_contract').val()
    if (service_contract=='Ja'){
        query = query + '&service_contract=True'
    } else if (service_contract == 'Nein'){
        query = query + '&service_contract=False'
    }
    if(query=='?'){
        return null
    }
    return encodeURI(query.replace(' ','+'))
};

function create_eorte(jsobj){
    var data = jsobj['data']
    var result = []
    for(var i in data ){
        eort = new Eort(data[i]['eort_id'], data[i]['fm_eort_id'], data[i]['lat'], data[i]['lng'], data[i]['name'], data[i]['street'], data[i]['zip_code'], data[i]['city']['city'], data[i]['has_vehicle'], data[i]['make_list'])
        /*if (data[i]['vehicles'] && data[i]['vehicles'].length > 0) {
            var vdata = data[i]['vehicles']
            for (var j in vdata) {
                veh = new Vehicle(vdata[j]['ikz'], vdata[j]['objno'], vdata[j]['make'], vdata[j]['model'], vdata[j]['reg_date'], vdata[j]['age'], vdata[j]['service_contract']);
                eort.add_veh(veh);
            }
        }*/
    result.push(eort);
    }
    print_eort_marker(result);
}

function print_eort_marker(list) {
    var greyIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    for (var i in list) {
        if (list[i]['has_veh']) {
            var marker = new myMarker([list[i]['lat'], list[i]['lng']], { EortID: list[i]['fm_eort_id'] }).on('click', eort_marker_click)
            marker.bindTooltip(list[i].get_context())
        } else {
            var marker = new myMarker([list[i]['lat'], list[i]['lng']], { EortID: list[i]['fm_eort_id'], icon: greyIcon }).on('click', eort_marker_click)
            marker.bindTooltip(list[i].get_context())
        }
        eort_markers.addLayer(marker)
    }
    eort_markers.addTo(mymap)
}

var is_open = false;
function eort_marker_click(e) {
    var eort_id = e.target.options.EortID
    if(is_open){
        vtbl.destroy();
    }
    fill_vehicle_table(eort_id)
    get_eort_slider(eort_id)
}
var veh_is_open = false;
function open_veh_slider(){
    if (veh_is_open) {
        wtbl.destroy();
    }
    fill_workshop_table()
    get_veh_slider()
}

var vtbl = null;
function fill_vehicle_table(eort_id){
    is_open = true
    $('.slider-eort-data').removeClass('width0')
    vtbl = $('#vehicle_tbl').DataTable({
        responsive: false,
        stateSave: false,
        select: 'single',
        ajax: {
            url: '/api/v1/eort/' + eort_id + '/vehicles/?format=json',
            dataSrc: 'data',
        },
        "info": true,
        "processing": true,
        "ordering": true,
        "searching": true,
        "language": {
            "emptyTable": "Keine Daten verfügbar",
            "info": "Angezeigt werden _START_ bis _END_ von _TOTAL_ Einträge",
            "infoEmpty": "Keine Daten verfügbar",
            "infoFiltered": "(gefiltert von _MAX_ Einträgen)",
            "thousands": ".",
            "lengthMenu": "_MENU_ Einträge pro Seite",
            "search": "Suche",
            "paginate": {
                "first": "Erste",
                "last": "Letzte",
                "next": "Vor",
                "previous": "Zurück"
            },
        },
        "columns": [
            {
                "data": 'ikz',
                "title": "IKZ"
            },
            {
                "data": 'objgroup',
                "title": "Objecktgruppe"
            },
            {
                "data": 'make',
                "title": "Hersteller"
            },
            {
                "data": 'model',
                "title": "Fz-Modell"
            },
            {
                "data": 'service_contract',
                "title": "SV"
            },
            {
                "data": 'wt_workshop',
                "title": "Stammwerkstatt",
                "render": function (value) {
                    if (!value) {
                        return 'ohne Wst'
                    }else{
                        return value['kuerzel']
                    }
                }
            },
            {
                "data": 'acc_workshop',
                "title": "Unfallwerkstatt",
                "render": function (value) {
                    if (!value) {
                        return 'ohne Wst'
                    } else {
                        return value['kuerzel']
                    }
                }
            },
        ]
    }).on('select', function (e, dt, type, indexes){
        ikz = vtbl.rows(indexes).data().pluck('ikz')[0]
        open_veh_slider();
    });
}
var wtbl = null;
function fill_workshop_table() {
    veh_is_open = true
    $('.slider-vehicle-data').removeClass('width0')
    wtbl = $('#workshop_tbl').DataTable({
        responsive: false,
        stateSave: false,
        select: 'single',
        ajax: {
            url: '/api/v1/vehicle/' + ikz + '/workshops/?format=json',
            dataSrc: 'data',
        },
        "info": true,
        "processing": true,
        "ordering": true,
        "searching": true,
        "language": {
            "emptyTable": "Keine Daten verfügbar",
            "info": "Angezeigt werden _START_ bis _END_ von _TOTAL_ Einträge",
            "infoEmpty": "Keine Daten verfügbar",
            "infoFiltered": "(gefiltert von _MAX_ Einträgen)",
            "thousands": ".",
            "lengthMenu": "_MENU_ Einträge pro Seite",
            "search": "Suche",
            "paginate": {
                "first": "Erste",
                "last": "Letzte",
                "next": "Vor",
                "previous": "Zurück"
            },
        },
        "columns": [
            {
                "data": 'type',
                "title": "Art"
            },
            {
                "data": 'kuerzel',
                "title": "Kürzel"
            },
            {
                "data": 'name',
                "title": "Name"
            },
            {
                "data": 'street',
                "title": "Straße"
            },
            {
                "data": 'zip_code',
                "title": "PLZ"
            },
            {
                "data": 'city',
                "title": "Stadt"
            },
            {
                "data": 'phone',
                "title": "Telefon"
            },
            {
                "data": 'central_email',
                "title": "Zentrale Email"
            },
            {
                "data": 'contact_email',
                "title": "Asp Email"
            },
            {
                "data": 'wp_user',
                "title": "Werkstattportal"
            },
        ]
    });
}

function get_eort_slider(eort_id){
    var url = '/api/v1/eort/' + eort_id
    $.ajax({
        type: 'GET',
        url: url,
        success: function (result, status, xhr) {
            fill_eort_slider(result["data"])
        },
        error: function (result, status, xhr) {
            console.log(status)
            console.log(result)
        },
        timeout: 120000,
    });
}
function get_veh_slider() {
    var url = '/api/v1/vehicle/' + ikz
    $.ajax({
        type: 'GET',
        url: url,
        success: function (result, status, xhr) {
            fill_veh_slider(result["data"])
        },
        error: function (result, status, xhr) {
            console.log(status)
            console.log(result)
        },
        timeout: 120000,
    });
}

function fill_eort_slider(data){
    $('.slider-eort-header').text(data['name'])
    $('#slider-fm-eort-id').val(data['fm_eort_id'])
    $('#slider-eort-bez').val(data['name'])
    $('#slider-lat').val(data['lat'])
    $('#slider-lng').val(data['lng'])
    $('#slider-street').val(data['street'])
    $('#slider-zip').val(data['zip_code'])
    $('#slider-lr').val(data['region'])
    if(data['city']){
        $('#slider-city').val(data['city']['city'])
        $('#slider-state').val(data['city']['state'])
    }
}

function fill_veh_slider(data) {
    $('#slider-veh-ikz').val(data['ikz'])
    $('#slider-veh-sc').val(data['service_contract'])
    $('#slider-veh-objgroup').val(data['objgroup'])
    $('#slider-veh-objnr').val(data['objno'])
    $('#slider-veh-make').val(data['make'])
    $('#slider-veh-model').val(data['model'])
    $('#slider-veh-year').val(data['year'])
    $('#slider-veh-reg').val(data['reg_date'])
    $('#slider-veh-age').val(data['age'])
}

