function _pad_digit(val) {
    while (String(val).length < 2) {
        val = "0" + val
    }
    return val
}

function chart_sequence(data) {
    if (data.length == 0) {
        console.log('empty data for chart')
        return
    }
    var chart = c3.generate({
        bindto:"#chart",
        data: {
            x: 'date',
            xFormat: null,
            columns: [
                ['date'].concat(_.map(data, function(pair) { return parseInt(pair[0]) * 1000 })),
                ['spend'].concat(_.map(data, function(pair) { return pair[1] }))
            ]
        },
        axis : {
            x : {
                type : 'timeseries',
                tick: {
                    format: function (x) {
                        return _pad_digit(x.getHours()) + ":" + _pad_digit(x.getMinutes())
                    }
                }
            }
        }
    });
}

function chart_by_hour(user_id, from, to) {
    return $.get('http://localhost:5000/hour',
        { from: from, to: to, user_id: user_id },
        function( data ) {
                chart_sequence(data)
            }
        )
}

function update_chart() {
    user_id = $('#user_id').val()
    from = $('#from').val()
    to = $('#to').val()
    chart_by_hour(user_id, from, to)
}

function _formatDate(date) {
    return date.getFullYear() + "-" + _pad_digit(date.getMonth() + 1) + "-" +
    _pad_digit(date.getDate()) + "T" + _pad_digit(date.getHours()) + ":" +
    _pad_digit(date.getMinutes()) + ":" + _pad_digit(date.getSeconds())
}

function init_angular() {
    var app = angular.module('demo', []).config(function($interpolateProvider){
        $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
    });

    app.controller('ListCtrl', function($scope) {
        $scope.update_dashboard = function() {
            update_chart()

            user_id = $('#user_id').val()
            from = $('#from').val()
            to = $('#to').val()

            $.get('http://localhost:5000/list',
                { from: from, to: to, user_id: user_id },
                function( data ) {
                        $scope.$apply(function() {
                            $scope.transactions = _.map(data, function(pair) {
                                t = new Date(parseInt(pair[0]) * 1000)
                                return { user_id: user_id, date: _formatDate(t), spend: pair[1]} })
                            console.log('updated the transactions table.')
                        })
                    }
                )

            $.get('http://localhost:5000/sum',
                { from: from, to: to, user_id: user_id },
                function( data ) {
                        $scope.$apply(function() {
                            $('#sum_result').text(
                                'The sum of spend for user ' + user_id +
                                ' from ' + _formatDate(new Date(parseInt(data[0]) * 1000)) +
                                ' to ' + _formatDate(new Date(parseInt(data[1]) * 1000)) +
                                ' is ' + data[2].toFixed(2))
                        })
                    }
                )
            };
    });
}


