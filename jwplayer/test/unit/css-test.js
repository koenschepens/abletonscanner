define([
    'utils/css'
], function (css) {
    /* jshint qunit: true */

    module('css');

    test('css.css and css.clearCss', function(assert) {
        var count = document.getElementsByTagName('style').length;

        var testSelector = 'test-selector';
        var stylesBlue = {
            'background-color': 'blue'
        };

        var stylesRed = {
            'background-color': 'red'
        };

        css.css(testSelector, stylesBlue);

        // check that a new style sheet has been added since this is the first time calling css.css
        var newCount = document.getElementsByTagName('style').length;
        assert.equal(newCount, count+1, 'css adds a new style sheet');

        // check that style sheet is correctly included to the end of head
        var styleSheet = document.getElementsByTagName('head')[0].lastChild;
        assert.ok(styleSheet.innerHTML.indexOf('test-selector{background-color:blue}') >=0 , 'css correctly included');

        // check that css will be replaced
        css.css(testSelector, stylesRed);
        assert.ok(styleSheet.innerHTML.indexOf('test-selector{background-color:blue}') < 0, 'css correctly replaced');
        assert.ok(styleSheet.innerHTML.indexOf('test-selector{background-color:red}') >= 0, 'css correctly replaced');

        css.clearCss('test-selector');

        // check clearCss works correctly
        assert.ok(styleSheet.innerHTML.indexOf('test-selector{background-color:red}') < 0, 'css correctly removed');
    });

    test('css.style', function(assert) {
        var element = document.createElement('div');
        var element2 = document.createElement('div');

        var styles = {
            'background-color': 'white',
            'z-index': 10,
            'background-image': 'images/image.jpg',
            'color': '123456'
        };

        var styles2 = {
            'backgroundColor': 'white',
            'backgroundImage': 'images/image.jpg'
        };

        // this should not break
        css.style(null, styles);
        css.style(element, null);

        css.style(element, styles);
        assert.ok(element.getAttribute('style').indexOf('background-color: white') >= 0, 'css style background');
        assert.ok(element.getAttribute('style').indexOf('z-index: 10') >= 0, 'css style z index');
        assert.ok(element.getAttribute('style').indexOf('background-image: url(') >= 0, 'css style img');
        assert.ok(element.getAttribute('style').indexOf('color: rgb(18, 52, 86)') >= 0, 'css style color');

        // test camelCases
        css.style(element2, styles2);
        assert.ok(element2.getAttribute('style').indexOf('background-color: white') >= 0, 'camelCase style background');
        assert.ok(element2.getAttribute('style').indexOf('background-image: url(') >= 0, 'camelCase style img');
    });

    test('css.transform', function(assert) {
        var element = document.createElement('div');

        // this should not break
        css.transform(null, 'none');
        css.transform(element, null);

        css.transform(element, 'none');

        assert.equal(element.style.transform, 'none', 'css transform');
        assert.equal(element.style.MsTransform, 'none', 'css transform ms');
        assert.equal(element.style.MozTransform, 'none', 'css transform moz');
        assert.equal(element.style.OTransform, 'none', 'css transform o');

        css.transform(element, '');

        assert.equal(element.style.transform, '', 'css transform');
        assert.equal(element.style.MsTransform, '', 'css transform ms');
        assert.equal(element.style.MozTransform, '', 'css transform moz');
        assert.equal(element.style.OTransform, '', 'css transform o');
    });

    test('css.hexToRgba', function(assert) {
        // this should not break
        css.hexToRgba(null, null);

        var rgba = css.hexToRgba('123456', 0.5);
        assert.equal(rgba, 'rgba(18,52,86,0.005)', 'css hexToRgba test');

        rgba = css.hexToRgba('123', 0);
        assert.equal(rgba, 'rgba(17,34,51,0)', 'css hexToRgba test with length 3');

        rgba = css.hexToRgba('', 0);
        assert.equal(rgba, 'rgba(0,0,0,0)', 'css hexToRgba test with invalid value');
    });

});
