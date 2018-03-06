/* global openerp, _, $ */

openerp.su_dynamic_listview_odoov8_1 = function (instance) {
    'use strict';

    instance.web.ListView.include({
        load_list: function (data) {
            this._super(data);

            if (this.$buttons.length) {
                this.$buttons.off('click', '.su_fields_show li');
                this.$buttons.on('click', '.su_fields_show li', this.proxy('onClickShowField'));
                this.$buttons.off('click', '.update_fields_show');
                this.$buttons.on('click', '.update_fields_show', this.proxy('updateShowField'));
                this.$buttons.off('keypress', '.su_dropdown li > input');
                this.$buttons.on('keypress', '.su_dropdown li > input', this.proxy('onChangeStringField'));
                this.$buttons.off('focusout', '.su_dropdown li > input');
                this.$buttons.on('focusout', '.su_dropdown li > input', this.proxy('onFocusOutTextField'));
                this.$buttons.off('click', '.su_fields_show li > span');
                this.$buttons.on('click', '.su_fields_show li > span', this.proxy('onClickSpanCheck'));
                this.$buttons.off('click', '#apply_for_all_user');
                this.$buttons.on('click', '#apply_for_all_user', this.proxy('onClickApplyAll'));

                this.$buttons.find('#ul_fields_show').sortable();
                this.$buttons.find('#ul_fields_show').disableSelection();
            }
        },
        onClickApplyAll: function (e) {
            e.stopPropagation();
        },
        onClickSpanCheck: function (e) {
            var $elem = $(e.currentTarget);
            // if (e.currentTarget.className.search('span_ticked') >= 0) {
            if ($elem.hasClass('span_ticked')) {
                $elem.parent().removeClass("selected");
                $elem.removeClass("span_ticked");
                $elem.parent().find('input').removeClass("display-block");
                $elem.parent().find('a').removeClass("display-none");
            }
            e.stopPropagation();
        },
        onFocusOutTextField: function (e) {
            var $elem = $(e.currentTarget);
            $elem.removeClass("display-block");
            $elem.parent().find('a').removeClass("display-none");
        },
        onChangeStringField: function (e) {
            var $elem = $(e.currentTarget);
            var text = $elem.val() + e.key;
            $elem.parent().find('a').text(text);
        },
        getFieldsShow: function () {
            var fields_show = [];
            var sequence = 1;
            this.$buttons.find(".su_fields_show li.selected").each(function () {
                var $result = $(this);
                fields_show.push({
                    string: $result.find('input').val().trim(),
                    sequence: sequence,
                    name: $result.attr("name")
                });
                sequence += 1;
            });
            return fields_show;
        },
        updateShowField: function () {
            var self = this;
            new instance.web.Model("show.field").call('change_fields', [{
                model: this.model,
                view_id: this.fields_view.view_id,
                fields_show: this.getFieldsShow(),
                for_all_user: !!this.$buttons.find("#apply_for_all_user:checked").length
            }]).done(function (result) {
                return self.load_view(self.dataset.context).done(function () {
                    return self.reload_content();
                });
            });
        },
        onClickShowField: function (e) {
            e.stopPropagation();
            var $elem = $(e.currentTarget);
            // if (e.currentTarget.className.search('selected') < 0) {
            if (!$elem.hasClass('selected')) {
                $elem.addClass("selected");
                $elem.find('span').addClass("span_ticked");
            } else {
                $elem.find('input').addClass("display-block");
                $elem.find('a').addClass("display-none");
            }
        }
    });
};
