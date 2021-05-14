class ColorIndex {
    constructor() {
        this.colors = [
            '#e9cdb5', '#b39e7b', '#3a0c12', '#69eda0', '#8c886a', '#6c70e8', '#492a62', '#e53ec9', '#bb3a6a', '#8458f8', '#f82378', '#d47bf4', '#0761a7', '#cc02fe', '#4487e1', '#f1df44', '#ec851a', '#8e505d', '#0e31aa', '#29f687',
            '#7bff55', '#ce5899', '#9409cb', '#ea8f63', '#a4d321', '#d5140e', '#f1bc07', '#2955a7', '#8e31f0', '#59a356', '#885714', '#771706', '#ed3765', '#3d4658', '#55a3af', '#e9c126', '#811141', '#5f66fb', '#6fc482', '#2ffcfc',
            '#734ebf', '#0e51f1', '#b7c8b2', '#d205e5', '#acb531', '#483777', '#86ec1c', '#287599', '#367d60', '#cfd00c', '#0133fc', '#ec09a5', '#619a04', '#ed3929', '#1acf9e', '#700c23', '#d03164', '#ea9415', '#f2e82f', '#f9004f'
        ]
        this.storage = {}
    }

    get(wst){
        if(!wst){
            var random = Math.floor(Math.random() * this.colors.length);
            var color = this.colors[random]
            return color
        }else{
            if(wst in this.storage){
                return this.storage[wst]
            }else{
                var random = Math.floor(Math.random() * this.colors.length);
                var color = this.colors[random]
                this.storage[wst]= color
                return color
            }
        }
    }
}

var color_index = new ColorIndex();

class Vehicle{
    constructor(ikz, objno, make, model, reg_date, age, service_contract){
        this.ikz = ikz;
        this.objno = objno;
        this.make = make;
        this.model = model;
        this.reg_date = new Date(reg_date);
        this.age = age;
        this.service_contract = service_contract;
    }
}


class Eort{
    constructor(eort_id, fm_eort_id, lat, lng, name=null, street=null, zip_code=null, city=null, has_veh=false, make_info=null){
        this.eort_id = eort_id;
        this.fm_eort_id = fm_eort_id
        this.lat= lat;
        this.lng = lng;
        this.name = name;
        this.street = street;
        this.zip_code = zip_code;
        this.zip_code_region = this.get_zip_code_region(zip_code);
        this.city = city;
        this.veh_list = []
        this.has_veh = has_veh;
        this.make_info = make_info
    }

    get_zip_code_region(zip_code){
        if(zip_code!=null){
            return zip_code.substring(0,2)
        }else{
            return null
        }
    }
    
    print_make_info(){
        var $res = $("<ul class='make-info-ul'></ul>")
        var $line = $("<li class='make-info-li'><span class='make-info-make'></span> <span class='make-info-count'></span></li>");
        for(var i in this.make_info){
            $line.find('.make-info-make').text(this.make_info[i]['make']);
            $line.find('.make-info-count').text(this.make_info[i]['total']);
            $res.append($line);
            $line = $("<li class='make-info-li'><span class='make-info-make'></span> <span class='make-info-count'></span></li>")
        }
        return $res[0].outerHTML
    }
    
    get_context(){
        return '<h5>' + this.name + '</h5>' +
                    '<p>' + this.street + '<br>'+
                    this.zip_code + ' ' + this.city + '</p>' +
                    '<p>' + this.print_make_info() + '</p>'
    }
}

class RuleWT{
    constructor(){
        this.page = 1
        this.init = false;
        this.query = null;
    }

    draw(){
        if(!this.init){
            this.get_rules();
        }
    }

    print_rules(){
        console.log(this.rules)
    }

    next_page(){
        this.page += 1;
        this.get_rules();
    }
    reset_page(query){
        this.page = 1;
        this.query = query;
    }

    get_rules(){
        this.init = true;
        if(this.query!=null){
            var url = '/api/v1/rules/wear-and-tear/' + this.query + '&page=' + this.page;
        }else{
            var url = '/api/v1/rules/wear-and-tear/?page=' + this.page;
        }
        console.log(url)
        var that = this;
        $.ajax({
            type: 'GET',
            url: url,
            success: function (result, status, xhr) {
                that.append_rows(result['results']);
                $('.ruletbl-loader').addClass('ruletbl-loader-noshow');
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    }

    append_rows(list){
        var j = 1;
        var $ret = "";
        for (var i of list) {
            var $markup = $(
                "<div class='ruletbl-tr'>"+
                    "<div class='ruletbl-col1 ruletbl-td'></div>"+
                    "<div class='ruletbl-col2 ruletbl-td'></div>" +
                    "<div class='ruletbl-col3 ruletbl-td'></div>" +
                    "<div class='ruletbl-col4 ruletbl-td'></div>" +
                    "<div class='ruletbl-col5 ruletbl-td'></div>" +
                    "<div class='ruletbl-col6 ruletbl-td'></div>" +
                    "<div class='ruletbl-col7 ruletbl-td'></div>" +
                    "<div class='ruletbl-col8 ruletbl-td'></div>" +
                    "<div class='ruletbl-col9 ruletbl-td'></div>" +
                    "<div class='ruletbl-col10 ruletbl-td'></div>" +
                    "<div class='ruletbl-col11 ruletbl-td'></div>" +
                    "<div class='ruletbl-col12 ruletbl-td'></div>" +
                    "<div class='ruletbl-col13 ruletbl-td'></div>" +
                    "<div class='ruletbl-col14 ruletbl-td'></div>" +
                    "<div class='ruletbl-col15 ruletbl-td'></div>" +
                    "<div class='ruletbl-col16 ruletbl-td'></div>" +
                "</tr>")
            if (j % 2 === 0) {
                $markup[0].classList.add("ruletbl-tr-alt");
            }
            $markup.find('.ruletbl-col1').text(i['row']);
            $markup.find('.ruletbl-col2').text(i['lat']);
            $markup.find('.ruletbl-col3').text(i['lng']);
            $markup.find('.ruletbl-col4').text(i['radius']);
            $markup.find('.ruletbl-col5').text(i['zip_code']);
            $markup.find('.ruletbl-col6').text(i['make']);
            $markup.find('.ruletbl-col7').text(i['model']);
            $markup.find('.ruletbl-col8').text(i['objno']);
            $markup.find('.ruletbl-col9').text(i['year']);
            $markup.find('.ruletbl-col10').text(i['age']);
            $markup.find('.ruletbl-col11').text(i['service_contract']);
            $markup.find('.ruletbl-col12').text(i['ikz']);
            $markup.find('.ruletbl-col13').text(i['kuerzel']);
            $markup.find('.ruletbl-col14').text(i['address']);
            $markup.find('.ruletbl-col15').text(i['note']);
            if(i['lbr']){
                $markup.find('.ruletbl-col16').html("<span class='rrule-draw'><i class='fas fa-drafting-compass'></i></span>")
            }
            $ret = $ret + $markup[0].outerHTML;
            j += 1;
        }
        $('.ruletbl-tbody').append($ret);
    }

}
