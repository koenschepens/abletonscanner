define([
    'utils/helpers'
], function (utils) {
    /* jshint qunit: true */

    module('helpers');

    test('helpers foreach test', function(assert) {
        var aData = {'hello': 'hi'};
        var tester = [];
        function fnEach(key, val) {
            tester.push(key);
            tester.push(val);
        }
        utils.foreach(aData, fnEach);

        assert.equal(tester[0], 'hello');
        assert.equal(tester[1], 'hi');
    });

    test('helpers log with fake console', function(assert) {
        var tmpConsole = window.console;
        var m = [];

        window.console = null;
        // this should not break
        utils.log('testing');

        //test window console called with utils.log
        window.console = {log: function(message) {
            m.push(message);
        }};
        utils.log('testing');
        assert.equal(m[0], 'testing');

        // restore actual window console
        window.console = tmpConsole;
    });
});