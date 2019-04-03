define([
    'utils/dom'
], function (dom) {
    /* jshint qunit: true */

    module('dom');

    test('dom.addClass', function (assert) {
        var element = document.createElement('div');
        assert.strictEqual(element.className, '', 'Created an element with no classes');

        dom.addClass(element, 'class1');
        assert.equal(element.className, 'class1', 'Added first class to element');

        dom.addClass(element, 'class1');
        assert.equal(element.className, 'class1', 'Added same class to element');

        dom.addClass(element, 'class2');
        assert.equal(element.className, 'class1 class2', 'Added second class to element');

        dom.addClass(element, ['class3', 'class4']);
        assert.equal(element.className, 'class1 class2 class3 class4', 'Added array of classes to element');

        dom.addClass(element, 'class5 class6');
        assert.equal(element.className, 'class1 class2 class3 class4 class5 class6',
            'Added space delimited classes to element');
    });

    test('dom.removeClass', function (assert) {
        var element = document.createElement('div');
        element.className = 'class1 class2 class3';
        assert.equal(element.className, 'class1 class2 class3', 'Created an element with two classes');

        dom.removeClass(element, 'class3');
        assert.equal(element.className, 'class1 class2', 'Removed a class from element');

        dom.removeClass(element, ['class2']);
        assert.equal(element.className, 'class1', 'Removed array of classes from element');

        dom.removeClass(element, 'class1');
        assert.equal(element.className, '', 'Removed lass class from element');
    });

    test('dom.createElement', function(assert) {
        var element = dom.createElement('<div id=\'testid\'></div>');

        assert.equal(element.id, 'testid', 'element create test');
    });

    test('dom.styleDimension', function(assert) {
        var percentage = dom.styleDimension('50%');
        var px = dom.styleDimension('50');

        // check style dimensions with percentage and px
        assert.equal(percentage, '50%', 'percentage dimension test');
        assert.equal(px, '50px', 'px dimension test');
    });

    test('dom.classList', function(assert) {
        var elementA = document.createElement('div');
        elementA.className = 'class1 class2';

        var elementB = document.createElement('div');
        dom.addClass(elementB, 'a b');

        // get classList with both elements
        var classA = dom.classList(elementA);
        var classB = dom.classList(elementB);

        // check that the classList is what we expect
        assert.equal(classA[0], 'class1', 'first class add to class list');
        assert.equal(classA[1], 'class2', 'first class add to class list');
        assert.equal(classB[0], 'a', 'first class add to class name');
        assert.equal(classB[1], 'b', 'first class add to class name');

        // check that hasClass function works correctly
        assert.ok(dom.hasClass(elementA, 'class1'), 'has class test with existing class');
        assert.notOk(dom.hasClass(elementA, 'class3'), 'has class test with non existing class');
    });

    test('dom.toggleClass', function(assert) {
        var element = document.createElement('div');
        dom.addClass(element, 'a');

        // check toggleClass
        dom.toggleClass(element, 'a');
        dom.toggleClass(element, 'b');

        // check that b is added to element by toggle, and a is removed by toggle
        assert.ok(dom.hasClass(element, 'b'), 'has class test with toggle class');
        assert.notOk(dom.hasClass(element, 'a'), 'has class test with removed class');
    });

    test('dom.emptyElement', function(assert) {
        var element = document.createElement('div');
        var child = document.createElement('p');

        // confirm that child is added to the element
        element.appendChild(child);
        assert.equal(element.firstChild, child);

        // empty the element and test that firstChild is not child anymore
        dom.emptyElement(element);
        assert.notOk(element.firstChild, 'emptyElement should remove all children');

        // add child again to test empty
        element.appendChild(child);
        assert.equal(element.firstChild, child);

        // empty the children in element
        dom.empty(element);
        assert.notOk(element.firstChild, 'empty should remove all children');

        // check empty with null will not break
        dom.empty(null);
    });

    test('addStyleSheet test', function(assert) {
        var url = 'testUrl';
        dom.addStyleSheet(url);

        // check that stylesheet with testUrl href has been added to the head
        assert.ok(document.getElementsByTagName('head')[0].lastChild.href.indexOf('testUrl') >= 0);
    });

    test('bounds test', function(assert) {
        var element = document.createElement('div');
        var emptyBound = {left: 0, right: 0, width: 0, height: 0 , top: 0, bottom: 0};
        var bound = dom.bounds(element);

        assert.ok(_checkEqualBound(bound, emptyBound), 'bounds should be empty bounds');

        // check null bounds does not break
        dom.bounds(null);

        function _checkEqualBound(bound, checkBound) {
            return bound.left === checkBound.left &&
                    bound.right === checkBound.right &&
                    bound.width === checkBound.width &&
                    bound.height === checkBound.height &&
                    bound.top === checkBound.top &&
                    bound.bottom === checkBound.bottom;
        }
    });

});
