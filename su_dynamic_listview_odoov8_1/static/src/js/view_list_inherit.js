/* global openerp, _, $ */

openerp.su_dynamic_listview_odoov8_1 = function (instance) {
    'use strict';

    var _t = instance.web._t;

    instance.web.ListView.include({
        load_list: function (data) {
            var self = this;
            self._super(data);

            var $ul = self.$buttons.find('#ul_fields_show');

            if ($ul.data('state') === 'uninitialized' && self.$buttons.length) {
                $ul.data({state: 'loading'});

                var known_fields = $ul.children("li[tag='field']").map(function () {
                    return $(this).attr('name');
                }).get();

                new instance.web.Model(self.model).call('fields_get', [], {
                    context: self.dataset.context
                }).done(function fields_get(fields) {
                    var arr = [];

                    for (var key in fields) {
                        if (fields.hasOwnProperty(key) && known_fields.indexOf(key) === -1) {
                            arr.push([key, fields[key].string]);
                        }
                    }

                    arr.sort(function(a, b) {
                        return (a[1] || '').localeCompare(b[1] || '');
                    });

                    for (var i = 0; i < arr.length; i++) {
                        var field_name = arr[i][0];
                        var field = fields[field_name];
                        var label = field.string;
                        $('<li/>').attr({
                            name: field_name,
                            tag: 'field',
                            type: field.type,
                        }).append(
                            $('<span/>').html('&#xf00c;'),
                            $('<a/>').text(label).append(
                                $('<em/>').text(_.str.sprintf(' (%s)', field_name))),
                            $('<input/>').attr({type:' text', value: label})
                        ).appendTo($ul);
                    }

                    self.$buttons.off('click', '.su_fields_show li');
                    self.$buttons.on('click', '.su_fields_show li', self.proxy('onClickShowField'));
                    self.$buttons.off('click', '.update_fields_show');
                    self.$buttons.on('click', '.update_fields_show', self.proxy('updateShowField'));
                    self.$buttons.off('click', '.reset_fields_show');
                    self.$buttons.on('click', '.reset_fields_show', self.proxy('resetShowField'));
                    self.$buttons.off('keypress', '.su_dropdown li > input');
                    self.$buttons.on('keypress', '.su_dropdown li > input', self.proxy('onChangeStringField'));
                    self.$buttons.off('focusout', '.su_dropdown li > input');
                    self.$buttons.on('focusout', '.su_dropdown li > input', self.proxy('onFocusOutTextField'));
                    self.$buttons.off('click', '.su_fields_show li > span');
                    self.$buttons.on('click', '.su_fields_show li > span', self.proxy('onClickSpanCheck'));
                    self.$buttons.off('click', '#apply_for_all_user');
                    self.$buttons.on('click', '#apply_for_all_user', self.proxy('onClickApplyAll'));

                    self.$buttons.find('#ul_fields_show').sortable();
                    self.$buttons.find('#ul_fields_show').disableSelection();

                    $ul.data({state: 'loaded'});
                });
            } else if ($ul.data('state') === 'loaded') {
                $ul.children("li").sort(function (a, b) {
                    var $a = $(a), $b = $(b);
                    if ($a.hasClass('selected') === $b.hasClass('selected')) {
                        return $a.index() < $b.index() ? -1 : 1;
                    }
                    return $a.hasClass('selected') ? -1 : 1;
                }).appendTo($ul);
            }
        },
        onClickApplyAll: function (e) {
            e.stopPropagation();
        },
        onClickSpanCheck: function (e) {
            var $elem = $(e.currentTarget);
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
                    name: $result.attr("name"),
                    tag: $result.attr("tag"),
                    type: $result.attr("type"),
                    icon: $result.attr("icon"),
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
        resetShowField: function () {
            var self = this;
            if (confirm(_t('This action cannot be undone, continue?'))) {
                new instance.web.Model("show.field").call('reset_fields', [{
                    model: this.model,
                    view_id: this.fields_view.view_id,
                }]).done(function (result) {
                    return self.load_view(self.dataset.context).done(function () {
                        return self.reload_content();
                    });
                });
            }
        },
        onClickShowField: function (e) {
            e.stopPropagation();
            var $elem = $(e.currentTarget);
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
