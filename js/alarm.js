(function($){
    $.fn.moveTo = function(selector){
        return this.each(function(){
            var cl = $(this).clone();
            $(cl).appendTo(selector);
            $(this).remove();
        });
    };
})(jQuery);


function move_options(select) {
    var target = $(this).data('target');
    var bin = $(this).data('bin');
    $(target).children().moveTo(bin);
    var show = $("option:selected", this).data('show');
    var show_obj = $(show);
    show_obj.moveTo(target);
}

function start_edit(btn) {
    var self = this;
    var target = $(self).data('target');
    var id = $(self).data('id');
    var cancel_target = target + " .cancel-btn-edit";
    var submit_target = target + " .submit-btn-edit";
    var non_target = target + " .non-btn-edit";
    $(non_target).addClass('hide').prop("disabled", true);
    $(cancel_target).removeClass('hide').prop("disabled", false);
    $(submit_target).removeClass('hide').prop("disabled", false).val(id);
    var values = $(self).data('values').split(',')
    $.each(values, function(index, value){
        var input = $('.input_' + value);
        var new_val = $(self).data(value);
        input.val(new_val);
        input.trigger('change');
    })
}

function cancel_edit(btn) {
    var target = $(this).data('target');
    var cancel_target = target + " .cancel-btn-edit";
    var submit_target = target + " .submit-btn-edit";
    var non_target = target + " .non-btn-edit";
    var form_target = $(this).data('form');
    $(non_target).removeClass('hide').prop("disabled", false);
    $(cancel_target).addClass('hide').prop("disabled", true);
    $(submit_target).addClass('hide').prop("disabled", true).val(null);
    $(':input', form_target)
     .not(':button, :submit, :reset, :hidden')
     .val('')
     .removeAttr('checked')
     .removeAttr('selected')
     .trigger('change');
}
